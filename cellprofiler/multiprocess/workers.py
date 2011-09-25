"""
Designed to act as a server for utilizing multiple cores
on a machine and processing in parallel
"""

import multiprocessing
import time
import StringIO
import zlib
import hashlib
import json
import urllib2
import base64

import logging

import zmq
from zmq import NotDone

from cellprofiler.pipeline import Pipeline
import cellprofiler.preferences as cpprefs
from managers import PipelineManager, parse_json


logger = logging.getLogger(__name__)

# whether CP should run multiprocessing
# changed by preferences, or by command line
force_run_multiprocess = False


def run_multiprocess():
    return (force_run_multiprocess or cpprefs.get_run_multiprocess())


def worker_looper(url, context=None):
    """
    TODO: WRITE DOCSTRING
    NOTE: DO NOT PASS zmq.CONTEXT ACROSS PROCESSES.
    When calling the looper from a parent process,
    create the context there (should only 1 one per process)
    """
    has_work = True
    responses = []
    context_supplied = context is not None
    if(not context_supplied):
        context = zmq.Context()
    transit = JobTransit(url, context)
    while has_work:
        jobinfo = transit.fetch_job()
        if(jobinfo and jobinfo.is_valid):
            measurements = single_job(jobinfo)
            response = transit.report_measurements(jobinfo, measurements)
            responses.append(response)
            num_remaining = response['num_remaining']
            has_work = num_remaining > 0
        else:
            has_work = False
    if(not context_supplied):
        termcode = context.term()
    return responses


def single_job(jobinfo):
        pipeline = Pipeline()
        try:
            pipeline.load(jobinfo.pipeline_stringio())
            image_set_start = jobinfo.image_set_start
            image_set_end = jobinfo.image_set_end
        except:
            logging.root.error("Can't parse pipeline for distributed work.",
                               exc_info=True)
            return [jobinfo.job_num, 'FAILURE']

        measurements = pipeline.run(image_set_start=image_set_start,
                                    image_set_end=image_set_end)
        return measurements


def run_multiple_workers(url, num_workers=None):
    """
    Run multiple local workers which will attempt to
    retrieve work from the provided URL.

    Does not block, starts up a pool of workers.

    Returns
    -----------
    pool - multiprocessing.Pool doing work
    """
    if(not num_workers):
        num_workers = multiprocessing.cpu_count()
    else:
        num_workers = min(multiprocessing.cpu_count(), num_workers)

    pool = multiprocessing.Pool(num_workers)

    urls = [url] * num_workers
    results = []
    for url in urls:
        result = pool.apply_async(worker_looper, args=(url,))
        results.append(result)
    #Note: The results will not be available immediately
    #because we haven't joined the pool
    return results


def start_serving_headless(pipeline, output_file_path, port, address):
    manager = PipelineManager(pipeline, output_file_path, port, address)
    manager.start()
    manager.initialized.wait()
    #url = manager.url
    return manager


def run_pipeline_headless(pipeline, output_file_path,
                            port, address):
    manager = start_serving_headless(pipeline, output_file_path,
                                          port, address)
    num_jobs = manager.total_jobs
    url = '%s:%s' % (address, manager.ports['jobs'])
    results = run_multiple_workers(url, num_workers=num_jobs)
    return results


class JobTransit(object):
    def __init__(self, url, context=None):
        self.url = url
        self.context = context or zmq.Context.instance()

    def _get_pipeline_blob(self):
        msg = json.dumps({'type': 'get', 'keys': ['pipeline_path']})
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


def send_with_timeout(socket, msg, timeout=5):
    tracker = socket.send(msg, copy=False, track=True)
    try:
        tracker.wait(timeout)
    except NotDone:
        return False
    return True


if __name__ == '__main__':
    pass
