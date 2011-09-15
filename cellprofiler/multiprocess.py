"""
Designed to act as a server for utilizing multiple cores
on a machine and processing in parallel
"""

import multiprocessing
import StringIO
import time
import logging

import zmq

from distributed import JobTransit, Manager
from cellprofiler.pipeline import Pipeline
import cellprofiler.preferences as cpprefs

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

def start_serving_headless(pipeline, output_file_path, address, port=None):
    manager = Manager(pipeline, output_file_path, address, port)
    manager.start()
    manager.initialized.wait()
    #url = manager.url
    return manager

def run_pipeline_headless(pipeline, output_file_path,
                            address, port=None):
    manager = start_serving_headless(pipeline, output_file_path,
                                          address, port)
    num_jobs = manager.total_jobs
    results = run_multiple_workers(manager.url, num_workers=num_jobs)
    return results

if __name__ == '__main__':
    pass
