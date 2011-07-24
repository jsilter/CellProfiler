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


class TestMultiProcess(unittest.TestCase):

    def setUp(self):
        self.testdir = os.path.dirname(__file__)
        self.datadir = os.path.join(self.testdir,'data')
        self.port= 8139 #Good for this developers machine
        
    def takeDown(self):
        self.testdir = None
        self.datadir = None
        self.port = None

    def run_multi_tst(self,pipeline,port,output_file_path,status_callback):
        distributor = cpdistributed.Distributor(None)
        distributor.start_serving(pipeline, port,output_file_path, status_callback)
        print "serving at ", distributor.server_URL
        #Start workers
        donejobs = multiprocess_server.run_multiple_workers(distributor.server_URL)
        
        running_pipeline = distributor.run_with_yield()
        for ghost in running_pipeline:
            time.sleep(0.1)
            pass
            #tm = time.time()
            #print "%s \t %s" % (tm,ghost)
                     
    def test_wound_healing(self):
        pipeline_path = os.path.join(self.datadir,'ExampleWoundHealingImages/ExampleWoundHealing.cp')
        pipeline= Pipeline()
        pipeline.load(pipeline_path)
        output_file_path = os.path.join(self.datadir,'output/test_wound_healing.hdf5')
        self.run_multi_tst(pipeline,self.port,output_file_path,None)
        
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()