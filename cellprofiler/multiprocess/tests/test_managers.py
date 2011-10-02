import unittest
import os
import json
import time

import zmq
import numpy as np

from cellprofiler.modules.tests import example_images_directory
from cellprofiler.pipeline import Pipeline
import cellprofiler.preferences as cpprefs
import cellprofiler.measurements as cpmeas
from cellprofiler.tests.test_Measurements import compare_measurements

from cellprofiler.multiprocess.managers import PipelineManager, parse_json
from cellprofiler.multiprocess.workers import  JobTransit, JobInfo, send_recv
from cellprofiler.multiprocess.workers import single_job, worker_looper, run_pipeline_headless


test_dir = os.path.dirname(os.path.abspath(__file__))
test_data_dir = os.path.join(test_dir, 'data')

class TestManager(unittest.TestCase):
    def setUp(self):
        #print 'starting test %s' % self.id()
        self.address = "tcp://127.0.0.1"
        #self.ports = {'jobs': None}
        self.port = None

        info = self.id().split('.')[-1]
        output_finame = info + '.h5'

        ex_dir = example_images_directory()
        self.img_dir = os.path.join(ex_dir, "ExampleWoundHealingImages")
        img_dir = self.img_dir
        pipeline_path = os.path.join(img_dir, 'ExampleWoundHealing.cp')
        self.output_file = os.path.join(img_dir, output_finame)

        self.pipeline = Pipeline()
        self.pipeline.load(pipeline_path)

        #self.distributor = Distributor(self.pipeline, self.output_file,
                                       #self.port, self.address )

        self.manager = PipelineManager(self.pipeline, self.output_file,
                                       self.port, self.address)

        #Might be better to write these paths into the pipeline
        self.old_image_dir = cpprefs.get_default_image_directory()
        cpprefs.set_default_image_directory(img_dir)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        #Amount of time (in msec) to allow a socket to stay open
        #for messages to be sent. We shouldn't need this > 0, default
        #is infinite (-1).
        self.socket.setsockopt(zmq.LINGER, 100)
        self.procs = []

    def tearDown(self):
        self.address = None
        self.port = None
        self.output_file = None

        self.pipeline = None
        self.manager = None
        #context.term hangs if we haven't closed all the sockets
        self.socket.close()
        self.context.term()
        for proc in self.procs:
            if(proc.is_alive()):
                print 'terminating ' + proc.name()
                proc.terminate()

        cpprefs.set_default_image_directory(self.old_image_dir)
        #print 'finished test %s' % self.id()

    def _start_serving(self, port=None):
        self.manager.start()
        self.manager.initialized.wait()
        port = self.manager.ports['jobs']
        url = '%s:%s' % (self.address, port)
        return url

    def _stop_serving_clean(self, url=None):
        stop_message = {'type': 'command',
                        'command': 'stop'}
        if(url is None):
            url = '%s:%s' % (self.address, self.port)
        msg = json.dumps(stop_message)
        send_recv(self.context, url, msg)

    def test_manager_start(self):
        url = self._start_serving()
        print 'back to main thread'
        time.sleep(1.0)
        self.assertTrue(self.manager.running())
        self._stop_serving_clean(url)
        self.assertFalse(self.manager.running())


    def test_start_serving(self):
        """
        Very basic test. Start server,
        make sure nothing goes wrong.
        """

        time_delay = 0.1
        url = self._start_serving()
        self.manager.join(time_delay)
        #Server will loop forever unless it hits an error
        self.assertTrue(self.manager.running())
        self._stop_serving_clean(url)
        #self.manager.stop_serving(force=True)

    def test_stop_serving(self):
        stop_message = {'type': 'command',
                        'command': 'stop'}

        url = self._start_serving()
        self.assertTrue(self.manager.running())

        time_limit = 1
        sent, resp = send_recv(self.context, url, json.dumps(stop_message),
                                 timeout=time_limit)
        self.assertTrue(sent)

        resp = parse_json(resp)
        self.assertTrue('status' in resp)
        self.assertTrue(resp['status'] == 'stopping')

        #Race condition here. We resolve by waiting awhile,
        #give the server some time to stop
        time.sleep(1)
        self.assertFalse(self.manager.running())

    def test_get_work_01(self):
        """
        Prepare a queue of work.
        Keep getting work but don't report results,
        make sure jobs are served over and over
        """

        url = self._start_serving()
        self.assertTrue(self.manager.running())

        num_jobs = self.manager.total_jobs
        num_trials = 100
        fetcher = JobTransit(url, self.context)

        for tri in xrange(num_trials):
            job = fetcher.fetch_job()
            self.assertIsNotNone(job)
            self.assertTrue(job.is_valid)
            exp_tri = (tri % num_jobs) + 1
            act_tri = job.job_num
            self.assertEqual(exp_tri, act_tri, 'Job Numbers do not match.' +
                             'Expected %d, found %d' % (exp_tri, act_tri))

        self._stop_serving_clean(url)

    def test_remove_work(self):
        """
        Get jobs and delete them from server (do not report results)
        """

        url = self._start_serving()
        self.assertTrue(self.manager.running())
        fetcher = JobTransit(url, self.context)

        num_jobs = self.manager.total_jobs
        self.socket.connect(url)

        received = set()
        while True:
            job = fetcher.fetch_job()
            if(job and job.is_valid):
                break
            msg = {'type': 'command',
                   'command': 'remove',
                   'id': job.job_num}
            self.socket.send(json.dumps(msg))
            rec = parse_json(self.socket.recv())
            self.assertTrue(rec['status'] == 'success')
            received.add(job.job_num)
            if(job.num_remaining == 0):
                break

        act_num_jobs = len(received)
        self.assertTrue(num_jobs, act_num_jobs)
        expected = set(xrange(1, num_jobs + 1))
        self.assertTrue(expected, received)

        self._stop_serving_clean(url)

    @np.testing.decorators.slow
    @unittest.skip('slow')
    def test_single_job(self):
        url = self._start_serving()
        transit = JobTransit(url, self.context)
        jobinfo = transit.fetch_job()
        measurement = single_job(jobinfo)
        #print measurement
        self._stop_serving_clean(url)

    @np.testing.decorators.slow
    @unittest.skip('lengthy test')
    def test_worker_looper(self):
        url = self._start_serving()
        responses = worker_looper(url, self.context)
        #print responses
        self._stop_serving_clean(url)
        for response in responses:
            self.assertEqual(response['status'], 'success')
        self.assertFalse(self.manager.running())
        
        ref_data_path = os.path.join(test_data_dir, 'ExampleWoundHealing_ref.h5')
        output_file_path = os.path.join(test_data_dir, 'output', 'test_wound_healing.h5')

        ref_meas = cpmeas.load_measurements(ref_data_path)
        test_meas = cpmeas.load_measurements(output_file_path)

        compare_measurements(ref_meas, test_meas, check_feature)
        

    @np.testing.decorators.slow
    def test_report_measurements(self):
        url = self._start_serving()

        meas_file = os.path.join(test_data_dir, 'CpmeasurementsGhqeaL.hdf5')
        curr_meas = cpmeas.load_measurements(filename=meas_file)
        transit = JobTransit(url, context=self.context)
        jobinfo = JobInfo(0, 0, None, None, 1)

        response = transit.report_measurements(jobinfo, curr_meas)
        self.assertTrue('code' in response)
        self.assertTrue('mismatched pipeline hash' in response['code'])
        self._stop_serving_clean(url)

    #@unittest.expectedFailure
    @np.testing.decorators.slow
    @unittest.skip('lengthy test')
    def test_wound_healing(self):
        ex_dir = example_images_directory()
        pipeline_path = os.path.join(ex_dir, 'ExampleWoundHealingImages', 'ExampleWoundHealing.cp')
        ref_data_path = os.path.join(test_data_dir, 'ExampleWoundHealing_ref.h5')
        output_file_path = os.path.join(test_data_dir, 'output', 'test_wound_healing.h5')

        self.tst_pipeline_multi(pipeline_path, ref_data_path, output_file_path)
        
    @unittest.expectedFailure
    @np.testing.decorators.slow
    @unittest.skip('lengthy test')
    def test_fly(self):
        ex_dir = example_images_directory()
        pipeline_path = os.path.join(ex_dir, 'ExampleFlyImages', 'ExampleFly.cp')
        ref_data_path = os.path.join(test_data_dir, 'ExampleFly_ref.h5')
        output_file_path = os.path.join(test_data_dir, 'output', 'test_fly.h5')
        
        self.tst_pipeline_multi(pipeline_path, ref_data_path, output_file_path)


    def tst_pipeline_multi(self, pipeline_path, ref_data_path, output_file_path):
        pipeline = Pipeline()
        pipeline.load(pipeline_path)
        
        img_dir = os.path.dirname(pipeline_path)
        cpprefs.set_default_image_directory(img_dir)

        results = run_pipeline_headless(pipeline, output_file_path, self.port, self.address)
        notdone = True
        while notdone:
            notdone = True
            for res in results:
                notdone &= not res.ready()
        ref_meas = cpmeas.load_measurements(ref_data_path)
        test_meas = cpmeas.load_measurements(output_file_path)

        compare_measurements(ref_meas, test_meas, check_feature)

def check_feature(feat_name):
        fnl = feat_name.lower()
        ignore = ['executiontime', 'pathname', 'filename', 'pipeline_pipeline',
                  'group_index']
        for igflag in ignore:
            if igflag in fnl:
                return False
        return True

def MockManager(BaseManager):
    def __init__(self, numjobs):
        self.numjobs = numjobs
        super(MockManager, self).__init__()

    def prepare_queue(self):
        for jobnum in range(0, self.numjobs):
            curj = {'id':jobnum, 'value':-jobnum ** 2}
            self._work_queue.add(curj)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestManager('test_fly'))
    return suite

if __name__ == "__main__":
    unittest.main()
    #unittest.TextTestRunner(verbosity=2).run(suite())
