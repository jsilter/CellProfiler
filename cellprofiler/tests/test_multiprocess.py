'''
Created on Jul 23, 2011

@author: jacob
'''
import unittest
import os
import time

from cellprofiler.pipeline import Pipeline
import cellprofiler.distributed as cpdistributed
import cellprofiler.multiprocess_server as multiprocess_server
import cellprofiler.measurements as measurements

from test_Measurements import compare_measurements


class TestMultiProcess(unittest.TestCase):

    def setUp(self):
        self.testdir = os.path.dirname(__file__)
        self.datadir = os.path.join(self.testdir,'data')
        self.port= 8139 #Good for this developers machine
        
    def takeDown(self):
        self.testdir = None
        self.datadir = None
        self.port = None

    def run_pipeline_multi(self,pipeline,output_file_path,status_callback):
        distributor = cpdistributed.Distributor(None)
        distributor.start_serving(pipeline,self.port,output_file_path, status_callback)
        print "serving at ", distributor.server_URL
        #Start workers
        donejobs = multiprocess_server.run_multiple_workers(distributor.server_URL)
        
        running_pipeline = distributor.run_with_yield()
        for ghost in running_pipeline:
            time.sleep(0.1)
            pass
            #tm = time.time()
            #print "%s \t %s" % (tm,ghost)
      
    def tst_pipeline_multi(self,pipeline_path,ref_data_path,output_file_path):
        pipeline= Pipeline()
        pipeline.load(pipeline_path)
        
        self.run_pipeline_multi(pipeline,output_file_path,None)
        
        ref_meas = measurements.load_measurements(ref_data_path)
        test_meas = measurements.load_measurements(output_file_path)

        compare_measurements(ref_meas, test_meas,check_feature)
        
    def test_wound_healing(self):
        pipeline_path = os.path.join(self.datadir,'ExampleWoundHealingImages/ExampleWoundHealing.cp')
        ref_data_path = os.path.join(self.datadir,'ExampleWoundHealingImages','ExampleWoundHealing_ref.h5')

        output_file_path = os.path.join(self.datadir,'output/test_wound_healing.h5')
        
        self.tst_pipeline_multi(pipeline_path,ref_data_path,output_file_path)

def check_feature(feat_name):
        fnl = feat_name.lower()
        ignore = ['executiontime','pathname','filename']
        for igflag in ignore:
            if igflag in fnl:
                return False
        return True  
              
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()