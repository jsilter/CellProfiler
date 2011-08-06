"""
Profiler some pipelines, in order to optimize
"""

__version__="$Revision$"

import os
import cProfile
import pstats

from cellprofiler.pipeline import Pipeline

basedir = os.path.dirname(os.path.abspath(__file__))

def run_pipeline(pipeline_filename,image_set_start=None,image_set_end=None,groups=None,measurements_filename= None):
    pipeline = Pipeline()
    measurements = None
    pipeline.load(pipeline_filename)
    measurements = pipeline.run(
                image_set_start=image_set_start, 
                image_set_end=image_set_end,
                grouping=groups,
                measurements_filename = measurements_filename,
                initial_measurements = measurements)
    
    
def run_example_fly():
    pipeline_filename = os.path.join(basedir,'data','ExampleFlyImages','ExampleFly_fp.cp')
    run_pipeline(pipeline_filename)
    
if __name__ == '__main__':
    rerun = False
    outfilename = os.path.join(basedir,'profile_ExampleFly')
    
    if(not os.path.exists(outfilename) or rerun):
        cProfile.run('run_example_fly()',outfilename)
    
    p = pstats.Stats(outfilename)
    #Strip directory names,sort by cumulative time spent
    to_print = p.sort_stats('cumulative')#.strip_dirs().
    #Only print top 20
    to_print.print_stats(20)
    