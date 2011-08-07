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
    
    
def profile_example_fly(output_filename = None,always_run = False):
    pipeline_filename = os.path.join(basedir,'data','ExampleFlyImages','ExampleFly_fp.cp')
    profile_pipeline(pipeline_filename,output_filename = output_filename,always_run = always_run)
    
def profile_pipeline(pipeline_filename,output_filename = None,always_run= False):
    """
    Run the provided pipeline, output the profiled results to a file.
    Pipeline is run each time by default, if canskip_rerun = True
    the pipeline is only run if the profile results filename does not exist
    
    Parameters
    --------------
    pipeline_filename: str
        Absolute path to pipeline
    output_filename: str, optional
        Output file for profiled results. Default is
        the same location&filename as pipeline_filename, with _profile
        appended
    always_run: Bool, optional
        By default, only runs if output_filename does not exist
        If always_run = True, then always runs
    """
    if(not output_filename):
        pipeline_name = os.path.basename(pipeline_filename).split('.')[0]
        pipeline_dir = os.path.dirname(pipeline_filename)
        output_filename = os.path.join(pipeline_dir,pipeline_name + '_profile')
        
    if(not os.path.exists(output_filename) or always_run):
        print 'Running %s' % (pipeline_filename)
        cProfile.runctx('run_pipeline(pipeline_filename)',globals(),locals(),output_filename)
    
    p = pstats.Stats(output_filename)
    #sort by cumulative time spent,optionally sptrip directory names
    to_print = p.sort_stats('time')#.strip_dirs().
    to_print.print_stats(20)
    
def profile_cooccurrence():
    import numpy
    from cellprofiler.cpmath.haralick import cooccurrence
    outfilename = os.path.join(basedir,'profile_cooc')
    data = numpy.load('testdata.npz')
    quantized = data['quantized']
    labels = data['labels']
    scale = data['scale']
    cProfile.runctx('cooccurrence(quantized,labels,scale)',globals(),locals(),outfilename)
    
    p = pstats.Stats(outfilename)
    to_print = p.sort_stats('time')#.strip_dirs().
    to_print.print_stats(20)    
    
if __name__ == '__main__':
    profile_example_fly(always_run = False)
    