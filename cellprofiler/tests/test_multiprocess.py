'''
Created on Jul 23, 2011

@author: jacob
'''
import unittest
import os

from cellprofiler.pipeline import Pipeline
import cellprofiler.multiprocess_server as multiprocess_server
import cellprofiler.measurements as measurements

from test_Measurements import compare_measurements

RUN_EXTENDED = False


class TestMultiProcess(unittest.TestCase):

    def setUp(self):
        self.testdir = os.path.dirname(__file__)
        self.datadir = os.path.join(self.testdir,'data')
        self.port= 8139 #Good for this developers machine
        
    def takeDown(self):
        self.testdir = None
        self.datadir = None
        self.port = None

    def tst_pipeline_multi(self,pipeline_path,ref_data_path,output_file_path):
        pipeline= Pipeline()
        pipeline.load(pipeline_path)
        
        multiprocess_server.run_pipeline_multi(pipeline,self.port,output_file_path,None)
        
        ref_meas = measurements.load_measurements(ref_data_path)
        test_meas = measurements.load_measurements(output_file_path)

        compare_measurements(ref_meas, test_meas,check_feature)
        
    @unittest.skipIf(not RUN_EXTENDED,
                     "Lengthy test, skipping to save time")
    def test_wound_healing(self):
        pipeline_path = os.path.join(self.datadir,'ExampleWoundHealingImages','ExampleWoundHealing.cp')
        ref_data_path = os.path.join(self.datadir,'ExampleWoundHealingImages','ExampleWoundHealing_ref.h5')
        output_file_path = os.path.join(self.datadir,'output/test_wound_healing.h5')
        
        self.tst_pipeline_multi(pipeline_path,ref_data_path,output_file_path)
        
    def tst_manual(self):
        ex_path = os.path.join(self.datadir,'ExampleTrackObjects')
        ref_data_path = os.path.join(ex_path,'ExampleTrackObjects_norm_single.h5')
        
        norm_multi_path = os.path.join(ex_path,'ExampleTrackObjects_norm_multi.h5')
        dist_single_path = os.path.join(ex_path,'ExampleTrackObjects_dist_single.h5')

        to_check = [norm_multi_path]#,dist_single_path]
        for path in to_check:
            compare_measurements(ref_data_path,path,check_feature)
        
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