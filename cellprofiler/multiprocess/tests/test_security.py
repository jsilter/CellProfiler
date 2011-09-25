'''
Created on Sep 25, 2011

@author: jacob
'''
import unittest
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
test_data_dir = os.path.join(test_dir, 'data')

from cellprofiler.multiprocess.security import verify_message, create_signature

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testName(self):
        pass

    def test_simple_sign(self):
        private_key_path = os.path.join(test_data_dir, 'test_rsa')
        data = 'Hello. Please execute this code for me.'
        signature, pub_key = create_signature(private_key_path, data)

        message_dict = {'signature': signature,
                        'public_key': pub_key,
                        'data': data}
        assert verify_message(message_dict)
        message_dict['data'] = data[0:-1]
        assert not verify_message(message_dict)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
