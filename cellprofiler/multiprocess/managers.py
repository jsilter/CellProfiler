import os.path
import zlib
import hashlib
import tempfile
import json
import base64
import uuid

import threading

import logging
from collections import deque
logger = logging.getLogger(__name__)

import zmq
from zmq.eventloop import ioloop

import cellprofiler.preferences as cpprefs
import cellprofiler.cpimage as cpi
import cellprofiler.workspace as cpw
import cellprofiler.measurements as cpmeas

#Whether CP should run distributed (changed by preferences or command line)
force_run_distributed = False


def run_distributed():
    return (force_run_distributed or cpprefs.get_run_distributed())


class BaseManager(threading.Thread):

    #Member variables accessible to anybody who makes
    #a get request
    expose = ['num_remaining']

    def __init__(self, ports, address="tcp://127.0.0.1", **kwargs):
        super(BaseManager, self).__init__(**kwargs)
        self.address = address
        self.ports = ports
        self._work_queue = QueueDict()
        self._loop = ioloop.IOLoop()
        self.initialized = threading.Event()
        self.info = {}
        self.jobs_finished = 0
        self.total_jobs = 0

    def prepare_queue(self):
        raise NotImplementedError("Must implement prepare_queue")
    
    def get_socket(self, socket_type, port=None):
        s = self._context.socket(socket_type)
        if port is None:
            p = s.bind_to_random_port(self.address)
        else:
            url = "%s:%s" % (self.address, int(port)) 
            p = s.bind(url)
        return s, p
    
    def prepare_sockets(self, context=None):
        """
        In progress, don't use yet
        """
        self._context = context or zmq.Context.instance()
        self.gui_commands = self.get_socket(zmq.PULL, self.ports['gui_commands'])
        self.gui_feedback = self.get_socket(zmq.PUSH, self.ports['gui_feedback'])
        
        self.jobs, jobs_port = self.get_socket(zmq.ROUTER)
        self.results, results_port = self.get_socket(zmq.PULL)
        self.control, control_port = self.get_socket(zmq.PUB)
        self.exceptions, exceptions_port = self.get_socket(zmq.ROUTER)

    def prepare_loop(self, context=None):
        self._context = context or zmq.Context.instance()
        
        port = self.ports['jobs']
        socket, port = self.get_socket(zmq.REP, port) 
        
        self.ports['jobs'] = port
        self._socket = socket
        self._loop.add_handler(self._socket, self.gen_msg_handler, zmq.POLLIN)

        return self.ports

    def add_job(self, job, id=None):
        """
        Add a job to the work queue. If no id is provided,
        a uuid will be generated
        """
        to_add = job
        if(id is None):
            id = uuid.uuid4()
        if('id' not in to_add):
            to_add['id'] = id
        self._work_queue.append(to_add)

    def job_finished(self, index=None, id=None):
        """
        Remove a job from the work queue
        At least 1 of id or index must be provided
        Parameters:
        id: optional
            id of the index
        Returns
        -----------
        success: boolean
            True if removed, False if not
        """
        if index is None:
            assert id is not None, "id cannot be none if index is None"
            try:
                index = self._work_queue.lookup(id)
            except KeyError:
                return False

        del self._work_queue[index]
        self.jobs_finished += 1
        return True

    def gen_msg_handler(self, socket, event):
        raw_msg = socket.recv()
        msg = parse_json(raw_msg)

        response = {'status': 'bad request'}
        if((msg is None) or ('type' not in msg)):
            #TODO Log something
            pass
        elif msg['type'] == 'next':
            response = self.get_next()
        elif((msg['type'] == 'result') and ('result' in msg)):
            response = self.report_result(msg)
        elif msg['type'] == 'command':
            response = self.receive_command(msg)
        elif msg['type'] == 'get':
            #General purpose way of querying simple information
            keys = msg['keys']
            for key in keys:
                if key in self.info:
                    response[key] = self.info[key]
                elif key in self.expose:
                    response[key] = getattr(self, key, 'notfound')
                else:
                    response[key] = 'notfound'
                response['status'] = 'success'

        self._socket.send(json.dumps(response))
        if self.num_remaining == 0:
            self._loop.stop()

    def run(self):
        self.prepare_queue()
        self.prepare_loop()
        self.initialized.set()

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
        raise NotImplementedError("Must implement report_result(self,msg)")

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


class PipelineManager(BaseManager):

    def __init__(self, pipeline, output_file, port=None, address="tcp://127.0.0.1",):
        self.expose.extend(['pipeline_path', 'pipeline_hash'])
        self.pipeline = pipeline
        self.pipeline_path = None
        self.output_file = output_file
        super(PipelineManager, self).__init__({'jobs':port}, address)

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
            job = {'id': img_set_index + 1,
                   'pipeline_path': self.pipeline_path,
                   'pipeline_hash': self.pipeline_hash}
            self._work_queue.append(job)

        self.total_jobs = image_set_list.count()
        return self._work_queue

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
        if work_item is None:
            resp = 'work item %s not found' % (id)
            response['code'] = resp
        elif pipeline_hash != work_item['pipeline_hash']:
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

            self.job_finished(index=work_item_index)
            response = {'status': 'success',
                        'num_remaining': self.num_remaining}
        return response


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
        raise KeyError('%s not found for key %s' % (value, key))

    def remove_bylookup(self, value, key='id'):
        index = self.lookup(value, key)
        self.remove(self[index])

    def get_next(self):
        value = self[0]
        self.rotate(1)
        return value


def start_serving(manager, item1, item2):
    manager.start()
    return manager


def recv_with_timeout(socket, msg, timeout=5):
    """
    zmq treats recv differently. Not sure if we can do this,
    or if it's necessary.
    """
    pass


def parse_json(raw_msg):
    try:
        msg = json.loads(raw_msg)
    except ValueError:
        logger.error('could not parse json: %s' % raw_msg)
        return None
    return msg
