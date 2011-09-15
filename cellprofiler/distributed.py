import time
import os.path
import StringIO
import zlib
import hashlib
import tempfile
import json
import urllib2
import base64
from multiprocessing import Manager, Process, Lock

import threading

import logging
from collections import deque
logger = logging.getLogger(__name__)

import zmq
from zmq import NotDone
from zmq.eventloop import ioloop

import cellprofiler.preferences as cpprefs
import cellprofiler.cpimage as cpi
import cellprofiler.workspace as cpw
import cellprofiler.measurements as cpmeas

#Whether CP should run distributed (changed by preferences or command line)
force_run_distributed = False
def run_distributed():
    return (force_run_distributed or cpprefs.get_run_distributed())

class Manager(threading.Thread):

    #Member variables accessible to anybody who makes
    #a get request
    expose = ['num_remaining', 'pipeline_path', 'pipeline_hash']
    def __init__(self, pipeline, output_file, address="tcp://127.0.0.1", port=None):
        super(Manager, self).__init__()
        self.init = {}
        self.pipeline = pipeline
        self.pipeline_path = None
        self.output_file = output_file
        self.address = address
        self.port = port
        self._work_queue = QueueDict()
        self._loop = ioloop.IOLoop()
        self.initialized = threading.Event()
        self.info = {}
        self._jobs_finished = 0

    def prepare_queue(self):
        if(self.pipeline_path is not None):
            #Assume we have already prepared queue
            return

        # duplicate pipeline
        pipeline = self.pipeline.copy()

        # make sure createbatchfiles is not in the pipeline
        exclude_mods = ['createbatchfiles', 'exporttospreadsheet']
        for ind, mod in enumerate(pipeline.modules()):
            if(mod.module_name.lower() in exclude_mods):
                print '%s cannot be used in distributed mode, removing' \
                    % (mod.module_name)
                pipeline.remove_module(ind + 1)

        # create the image list
        image_set_list = cpi.ImageSetList()
        image_set_list.combine_path_and_file = True
        self.measurements = cpmeas.Measurements(filename=self.output_file)
        workspace = cpw.Workspace(pipeline, None, None, None,
                                  self.measurements, image_set_list)

        if not pipeline.prepare_run(workspace):
            raise RuntimeError('Could not create image set list.')

        # call prepare_to_create_batch, for whatever preparation is necessary
        # hopefully none
        #pipeline.prepare_to_create_batch(workspace, lambda s: s)

        # add a CreateBatchFiles module at the end of the pipeline,
        # and set it up for saving the pipeline state
        module = pipeline.instantiate_module('CreateBatchFiles')
        module.module_num = len(pipeline.modules()) + 1
        pipeline.add_module(module)
        module.wants_default_output_directory.set_value(True)
        module.remote_host_is_windows.set_value(False)
        module.batch_mode.set_value(False)
        module.distributed_mode.set_value(True)

        #TODO This is really not ideal
        #save and compress the pipeline
        #This saves the data directly on disk, uncompressed
        raw_pipeline_path = module.save_pipeline(workspace)
        #Read it back into memory
        raw_pipeline_file = open(raw_pipeline_path, 'r')
        pipeline_txt = raw_pipeline_file.read()

        pipeline_fd, pipeline_path = tempfile.mkstemp()
        pipeline_file = open(pipeline_path, 'w')

        pipeline_blob = zlib.compress(pipeline_txt)
        pipeline_file.write(pipeline_blob)
        pipeline_file.close()
        self.pipeline_path = 'file://%s' % (pipeline_path)

        # we use the hash to make sure old results don't pollute new
        # ones, and that workers are fetching what they expect.
        self.pipeline_hash = hashlib.sha1(pipeline_blob).hexdigest()

        # add jobs for each image set
        #XXX Maybe use guid instead of img_set_index?
        for img_set_index in range(image_set_list.count()):
            job = {'id':img_set_index + 1,
                   'pipeline_path':self.pipeline_path,
                   'pipeline_hash':self.pipeline_hash}
            self._work_queue.append(job)

        self.total_jobs = image_set_list.count()
        return self._work_queue

    def _prepare_socket(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.setsockopt(zmq.LINGER, 100)
        if(self.port is not None):
            self.url = "%s:%s" % (self.address, int(self.port))
            socket.bind(self.url)
        else:
            self.port = socket.bind_to_random_port(self.address)
            self.url = "%s:%s" % (self.address, self.port)

        self._context = context
        self._socket = socket

        return self.url

    def _prepare_loop(self):
        self._loop.add_handler(self._socket, self.gen_msg_handler, zmq.POLLIN)

    def gen_msg_handler(self, socket, event):
        raw_msg = socket.recv()
        msg = parse_json(raw_msg)

        response = {'status': 'bad request'}
        if((msg is None) or ('type' not in msg)):
            #TODO Log something
            pass
        elif(msg['type'] == 'next'):
            response = self.get_next()
        elif((msg['type'] == 'result') and ('result' in msg)):
            response = self.report_result(msg)
        elif((msg['type']) == 'command'):
            response = self.receive_command(msg)
        elif((msg['type']) == 'get'):
            #General purpose way of querying simple information
            keys = msg['keys']
            for key in keys:
                if(key in self.info):
                    response[key] = self.info[key]
                elif(key in self.expose):
                    response[key] = getattr(self, key, 'notfound')
                else:
                    response[key] = 'notfound'
                response['status'] = 'success'

        self._socket.send(json.dumps(response))
        if(self.num_remaining == 0):
            self._loop.stop()

    def run(self):
        self.prepare_queue()
        self._prepare_socket()
        self.initialized.set()

        self._prepare_loop()

        #Blocking. Starts IO loop
        self._loop.start()

        self.post_run()

    def running(self):
        return self._loop.running()

    @property
    def num_remaining(self):
        return len(self._work_queue)

    def get_next(self):
        try:
            job = self._work_queue.get_next()
        except IndexError:
            job = None

        if(job is None):
            response = {'status': 'nowork'}
        else:
            response = job
        response['num_remaining'] = self.num_remaining
        return response

    def report_result(self, msg):
        id = msg['id']
        pipeline_hash = msg['pipeline_hash']
        try:
            work_item_index = self._work_queue.lookup(id)
            work_item = self._work_queue[work_item_index]
        except ValueError:
            work_item = None
        #print work_item
        response = {'status': 'failure'}
        if(work_item is None):
            resp = 'work item %s not found' % (id)
            response['code'] = resp
        elif(pipeline_hash != work_item['pipeline_hash']):
            resp = "mismatched pipeline hash"
            response['code'] = resp
        else:
            #Read data, write to temp file, load into HDF5_dict instance
            raw_dat = msg['result']
            meas_str = base64.b64decode(raw_dat)
            temp_dir = os.path.dirname(self.output_file)
            temp_hdf5 = tempfile.NamedTemporaryFile(dir=temp_dir)
            temp_hdf5.write(meas_str)
            temp_hdf5.flush()
            curr_meas = cpmeas.load_measurements(filename=temp_hdf5.name)

            self.measurements.combine_measurements(curr_meas,
                                                   can_overwrite=True)

            del self._work_queue[work_item_index]
            self._jobs_finished += 1
            response = {'status': 'success',
                        'num_remaining': self.num_remaining}
        return response

    def receive_command(self, msg):
        """
        Control commands from client to server.

        For now we use these for testing, should implement
        some type of security before release. Easiest
        would be to use process.authkey
        """
        command = msg['command'].lower()
        if(command == 'stop'):
            self._loop.stop()
            response = {'status': 'stopping'}
        elif(command == 'remove'):
            jobid = '?'
            try:
                jobid = msg['id']
                response = {'id': jobid}
                self._work_queue.remove_bylookup(jobid)
                response['status'] = 'success'
            except KeyError, exc:
                logger.error('could not delete jobid %s: %s' % (jobid, exc))
                response['status'] = 'notfound'
        return response

    def post_run(self):
        self._socket.close()
        self._context.term()

class QueueDict(deque):
    """
    Queue which provides for some dictionary-like access
    """

    def lookup(self, value, key='id'):
        """
        Search the list and return the index for which self[index][`key`] = value
        
        Note that `key` is not required to exist in any (or all) elements, but
        performance will be worse if it does not.
        """
        for index, el in enumerate(self):
            try:
                val = el[key]
                if(val == value):
                    return index
            except KeyError:
                pass
        raise ValueError('%s not found for key %s' % (value, key))

    def remove_bylookup(self, value, key='id'):
        index = self.lookup(value, key)
        self.remove(self[index])

    def get_next(self):
        value = self[0]
        self.rotate(1)
        return value

class JobTransit(object):
    def __init__(self, url, context):
        self.url = url
        self.context = context

    def _get_pipeline_blob(self):
        msg = json.dumps({'type': 'get', 'keys':['pipeline_path']})
        sent, raw_msg = send_recv(self.context, self.url, msg)

        if(not raw_msg):
            return None

        msg = parse_json(raw_msg)
        try:
            pipeline_path = msg['pipeline_path']
        except KeyError:
            logger.error('path not found in response')
            return None

        return urllib2.urlopen(pipeline_path).read()

    def fetch_job(self):

        raw_msg = json.dumps({'type': 'next'})
        sent, resp = send_recv(self.context, self.url, raw_msg)
        if(not sent):
            return None
        msg = parse_json(resp)

        if(not msg):
            return None

        if msg.get('status', '').lower() == 'nowork':
            print "No work to be had."
            return JobInfo(-1, -1, 'no_work', '', -1, False)

        # fetch the pipeline
        pipeline_blob = self._get_pipeline_blob()
        pipeline_hash_local = hashlib.sha1(pipeline_blob).hexdigest()

        try:
            job_num = msg['id']
            pipeline_hash_rem = msg['pipeline_hash']
            image_num = int(job_num)
            jobinfo = JobInfo(image_num, image_num,
                              pipeline_blob, pipeline_hash_local, job_num)
            jobinfo.num_remaining = msg['num_remaining']

            jobinfo.is_valid = pipeline_hash_local == pipeline_hash_rem
            if(not jobinfo.is_valid):
                logger.info("Mismatched pipeline hash")
            return jobinfo
        except KeyError, exc:
            logger.debug('KeyError: %s' % exc)
            return None

    def report_measurements(self, jobinfo, measurements):
        meas_file = open(measurements.hdf5_dict.filename, 'r+b')
        meas_str = meas_file.read()
        send_str = base64.b64encode(meas_str)

        msg = {'type': 'result', 'result': send_str}
        msg.update(jobinfo.get_dict())
        raw_msg = json.dumps(msg)

        sent, resp = send_recv(self.context, self.url, raw_msg)
        return parse_json(resp)

class JobInfo(object):
    def __init__(self, image_set_start, image_set_end,
                 pipeline_blob, pipeline_hash, job_num, is_valid=True,
                 num_remaining=None):
        self.image_set_start = image_set_start
        self.image_set_end = image_set_end
        self.pipeline_blob = pipeline_blob
        self.pipeline_hash = pipeline_hash
        self.job_num = job_num
        self.is_valid = is_valid
        self.num_remaining = num_remaining

    def get_dict(self):
        return {'id': self.job_num,
                'pipeline_hash': self.pipeline_hash}

    def pipeline_stringio(self):
        return StringIO.StringIO(zlib.decompress(self.pipeline_blob))

def start_serving(manager, item1, item2):
    manager.start()
    return manager

def send_recv(context, url, msg, timeout=5, protocol=zmq.REQ):
    """
    Send and recv a message.
    
    Parameters
    ---------
    context: zmq.context
    url: string
        url to connect to
    msg: buffer
        Message which will be sent with zmq.send
    timeout: int,opt
        Amount of time to wait for message to be sent (seconds).
        Default is 5.
    protocol: int,opt
        zmq protocol. Default is zmq.REQ.
    
    Returns
    ---------
    sent : bool
        True if message was successfully sent
    response : response received, or None
        response will be None if not sent
    """
    socket = context.socket(protocol)
    socket.connect(url)
    socket.setsockopt(zmq.LINGER, 0)
    sent = send_with_timeout(socket, msg, timeout)
    if(sent):
        response = socket.recv()
    else:
        response = None
    socket.close()
    return sent, response

def recv_with_timeout(socket, msg, timeout=5):
    """
    zmq treats recv differently. Not sure if we can do this,
    or if it's necessary.
    """
    pass

def send_with_timeout(socket, msg, timeout=5):
    tracker = socket.send(msg, copy=False, track=True)
    try:
        tracker.wait(timeout)
    except NotDone:
        return False
    return True

def parse_json(raw_msg):
    try:
        msg = json.loads(raw_msg)
    except ValueError:
        logger.error('could not parse json: %s' % raw_msg)
        return None
    return msg
