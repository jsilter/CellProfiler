"""
Designed to act as a server for utilizing multiple cores on a machine and 
processing in parallel
"""

import multiprocessing
import StringIO
import time
import logging

from cellprofiler.distributed import fetch_work,Distributor
from cellprofiler.pipeline import Pipeline
import cellprofiler.preferences as cpprefs

# whether CP should run multiprocessing (changed by preferences, or by command line)
force_run_multiprocess = False
def run_multiprocess():
    return (force_run_multiprocess or cpprefs.get_run_multiprocess())

def worker_looper(url,job_nums,lock):
    has_work = True
    job_nums = []
    while has_work:
        jobinfo = fetch_work(url)
        if(jobinfo):
            num = single_job(jobinfo)
            job_nums.append(num)
        else: 
            has_work = False
    return job_nums
 
def single_job(jobinfo):

        pipeline = Pipeline()
        try:
            pipeline.load(jobinfo.pipeline_stringio())
            image_set_start = jobinfo.image_set_start
            image_set_end = jobinfo.image_set_end
        except:
            logging.root.error("Can't parse pipeline for distributed work.", exc_info=True)
            return [jobinfo.job_num,'FAILURE']

        measurements = pipeline.run(image_set_start=image_set_start, 
                                    image_set_end=image_set_end,
                                    grouping= jobinfo.grouping)
        
        #out_measurements = StringIO.StringIO()
        #pipeline.save_measurements(out_measurements, measurements)
        
        jobinfo.report_measurements(pipeline, measurements)
        return [jobinfo.job_num,'SUCCESS']
   
def single_job_local(jobinfo):

        pipeline = Pipeline()
        try:
            pipeline.load(jobinfo.pipeline_stringio())
            image_set_start = jobinfo.image_set_start
            image_set_end = jobinfo.image_set_end
        except:
            logging.root.error("Can't parse pipeline for distributed work.", exc_info=True)
            return [jobinfo.job_num,'FAILURE']

        measurements = pipeline.run(image_set_start=image_set_start, 
                                    image_set_end=image_set_end,
                                    grouping= None)
        
        out_measurements = StringIO.StringIO()
        pipeline.save_measurements(out_measurements, measurements)   
        #jobinfo.report_measurements(pipeline, measurements)
        return out_measurements

def run_multiple_workers(url,num_workers = None):
    """
    Run multiple local workers which will attempt to
    retrieve work from the provided URL.
    
    Does not block, starts up a pool of workers.
    
    Returns
    -----------
    pool - multiprocessing.Pool
        The pool doing work
    """
    if(not num_workers):
        num_workers = multiprocessing.cpu_count()

    pool = multiprocessing.Pool(num_workers)
    
    urls = [url]*num_workers
    
    manager = multiprocessing.Manager()
    jobs = manager.list()
    lock = manager.Lock()

    for url in urls:
        pool.apply_async(worker_looper,args=(url,jobs,lock))  
    #Note: The results will not be available immediately
    #becaus we haven't joined the pool  
    return pool

def run_pipeline_headless(self,pipeline,port,output_file_path,status_callback):
    distributor = Distributor(None)
    distributor.start_serving(pipeline,port,output_file_path, status_callback)
    print "serving at ", distributor.server_URL
    #Start workers
    pool = run_multiple_workers(distributor.server_URL)
    
    running_pipeline = distributor.run_with_yield()
    for ghost in running_pipeline:
        time.sleep(0.1)
        pass

if __name__ == '__main__':
    pass
