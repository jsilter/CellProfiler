'''test_smooth.py - test the smooth module

CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2011 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
'''
__version__="$Revision$"

import base64
import numpy as np
from scipy.ndimage import gaussian_filter
import StringIO
import unittest
import zlib

from cellprofiler.preferences import set_headless
set_headless()

import cellprofiler.workspace as cpw
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.objects as cpo
import cellprofiler.modules.smooth as S
import cellprofiler.pipeline as cpp
import cellprofiler.measurements as cpmeas
from cellprofiler.cpmath.smooth import fit_polynomial, smooth_with_function_and_mask
from cellprofiler.cpmath.filter import median_filter, bilateral_filter

INPUT_IMAGE_NAME = 'myimage'
OUTPUT_IMAGE_NAME = 'myfilteredimage'

class TestSmooth(unittest.TestCase):
    def make_workspace(self, image,mask):
        '''Make a workspace for testing FilterByObjectMeasurement'''
        module = S.Smooth()
        pipeline = cpp.Pipeline()
        object_set = cpo.ObjectSet()
        image_set_list = cpi.ImageSetList()
        image_set = image_set_list.get_image_set(0)
        workspace = cpw.Workspace(pipeline,
                                  module,
                                  image_set,
                                  object_set,
                                  cpmeas.Measurements(),
                                  image_set_list)
        image_set.add(INPUT_IMAGE_NAME, cpi.Image(image, mask))
        module.image_name.value = INPUT_IMAGE_NAME
        module.filtered_image_name.value = OUTPUT_IMAGE_NAME
        return workspace, module
    
    def test_01_01_load_matlab(self):
        data = base64.b64decode(
            'TUFUTEFCIDUuMCBNQVQtZmlsZSwgUGxhdGZvcm06IFBDV0lOLCBDcmVhdGVkIG9u'
            'OiBGcmkgTWF5IDA4IDE0OjU1OjE0IDIwMDkgICAgICAgICAgICAgICAgICAgICAg'
            'ICAgICAgICAgICAgICAgICAgICAgICAgICAgIAABSU0PAAAAAgIAAHic3VW7TsMw'
            'FL0NKRSEymNiYMjIQmmFhBh5i0rQVhQhIbGY1KSWErtKHNQiPoCRz2Hk07AhaRNT'
            'yIOoA46s6Dr3nHtzfOJUAeB1GWBe3CtiavA1ykFcikwZdzHnhFpeGXTYCNbfxbxB'
            'LkH3Nr5Bto89GI9wvUkf2PVoMH50yXq+jVvIiSaL0fKde+x67YcQGDzukCG2u+QJ'
            'Q3yEaVf4kXiE0QAf8Kur47qMK3WrYm4sTHQoKTpIXdYj6zL/ACb5+hTdViP5q8G8'
            'xkO+fTpEJjccxM2+5NlP4KkoPDJuu8Q6ElJLfD0Br8fwOpwcdpp56x4z1w3r/rXv'
            'JP2qCl7GZ4QbHWaPKHMIstPtw5LCI+MTZlDGDd8LDJWGZ1HhkfGhz5nYSGJCep6i'
            '+pk1T5LPtBiPBi022/qqzxt7tfos68/FeOagXmsU+v5p+yjF+Eqwq+CL7uc8gW9N'
            '4ZMxoT3ySHo+sg3iIGt8Gmd5z5/8llenWkadpp0HlotGnolsHOFJ24/qn1uhyiz1'
            'UOvTHRTD72u//x+jevzVb5+msFzmD7LzTfvvTvgMYT08KJJH7a/oPv8L/xv87B/V'
            'v3l9c8FQrxk5UNLwrCg8Mu46jPF+2z2lfURN/O37mU/oXxPXeiXfOdSA77g09crl'
            '7DhdXHebz5sS9wLZ9mfrl/xw5M3/AOjFxSA=')
        pipeline = cpp.Pipeline()
        pipeline.load(StringIO.StringIO(data))
        self.assertEqual(len(pipeline.modules()),2)
        smooth = pipeline.modules()[1]
        self.assertEqual(smooth.module_name, 'Smooth')
        self.assertEqual(smooth.image_name.value, 'OrigBlue')
        self.assertEqual(smooth.filtered_image_name.value, 'CorrBlue')
        self.assertEqual(smooth.smoothing_method.value, S.FIT_POLYNOMIAL)
        self.assertTrue(smooth.wants_automatic_object_size)
    
    def test_01_02_load_v01(self):
        data = base64.b64decode(
            'eJztWN1u0zAUdrqsbCDt5wourV0hxKJ0iGr0hnUrE5GWrqLVBHd4rdtZcuLKcaaWJ'
            '+CSR+JxuNwjEJekSUxo0mxMqlRXlnvs853P57MT17WbvYvmKXxrmNBu9g6HhGLYoU'
            'gMGXca0BWv4RnHSOABZG4DnnMCbTSF5jGs1RtmvVE7gkem+Q6UK5pl7wTNj30AqkG'
            '7FdRKOLQZ2lqiSruLhSDuyNsEOngR9v8M6hXiBF1TfIWoj72YIuq33CHrTcfzIZsN'
            'fIrbyEk6B6XtO9eYe5fDCBgOd8gE0y75hpUUIrdP+JZ4hLkhPoyv9s55mVB4pQ7mk'
            '1gHTdFB6rKb6Jf+H0Hsr2fotp/w3wtt4g7ILRn4iELioNF8FjLecU68LSWetC85GZ'
            '0Gkkv8SQ5+T8HL2sMTcfhhgvoCOkj0b8rO44xxHs3DzMFrKbwG3oT5581/R+GV9jk'
            'RsMPo1GUOQbRYnKdKHGm3GHSZgL6H4/XIy2MjFWcDfAlWswiuksJVQJsV49NTOB3U'
            '6oZZZB8+V/KVdgsPkU8FtOQmhC3CcV8wPi2Vt2nUCuHUdTcydK4quKhEuO2wfSidV'
            '5lP3Q+tZse6D9993z+rkueyfG3mPmp+q8b3q7rcuVmW5yQnr6z3+uyQHXHmj/8/f9'
            'b5GvPD4OjH44da1zVujVvj1s/xGvf4uLsETj3v1N+B0v8rWLzfXoH0fpN2H1M65kz'
            '+H8ANZ3Zp9QzK0ODPrdG4CL5aiQuk5Pmcw3Og8Bz8i8dzGBM3RnfWZOu1nRE/mXcl'
            '+OxWF+us6hvrfve+DF9F+5vvWQ5OD5WSuO9guXV9ucA/yq2s/29KodH7')
        data = zlib.decompress(data)
        pipeline = cpp.Pipeline()
        pipeline.load(StringIO.StringIO(data))
        self.assertEqual(len(pipeline.modules()),2)
        smooth = pipeline.modules()[1]
        self.assertEqual(smooth.module_name, 'Smooth')
        self.assertEqual(smooth.image_name.value, 'OrigBlue')
        self.assertEqual(smooth.filtered_image_name.value, 'CorrBlue')
        self.assertEqual(smooth.smoothing_method.value, S.FIT_POLYNOMIAL)
        self.assertTrue(smooth.wants_automatic_object_size)
    
    def test_02_01_fit_polynomial(self):
        '''Test the smooth module with polynomial fitting'''
        np.random.seed(0)
        image = np.random.uniform(size=(100,100)).astype(np.float32)
        mask = np.ones(image.shape,bool)
        mask[40:60,45:65] = False
        expected = fit_polynomial(image, mask)
        workspace, module = self.make_workspace(image, mask)
        module.smoothing_method.value = S.FIT_POLYNOMIAL
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assertFalse(result is None)
        np.testing.assert_almost_equal(result.pixel_data, expected)
    
    def test_03_01_gaussian_auto_small(self):
        '''Test the smooth module with Gaussian smoothing in automatic mode'''
        sigma = 100.0/ 40.0 / 2.35
        np.random.seed(0)
        image = np.random.uniform(size=(100,100)).astype(np.float32)
        mask = np.ones(image.shape,bool)
        mask[40:60,45:65] = False
        fn = lambda x: gaussian_filter(x, sigma, mode='constant', cval = 0.0)
        expected = smooth_with_function_and_mask(image, fn, mask)
        workspace, module = self.make_workspace(image, mask)
        module.smoothing_method.value = S.GAUSSIAN_FILTER
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assertFalse(result is None)
        np.testing.assert_almost_equal(result.pixel_data, expected)
    
    def test_03_02_gaussian_auto_large(self):
        '''Test the smooth module with Gaussian smoothing in large automatic mode'''
        sigma = 30.0 / 2.35
        image = np.random.uniform(size=(3200,100)).astype(np.float32)
        mask = np.ones(image.shape,bool)
        mask[40:60,45:65] = False
        fn = lambda x: gaussian_filter(x, sigma, mode='constant', cval = 0.0)
        expected = smooth_with_function_and_mask(image, fn, mask)
        workspace, module = self.make_workspace(image, mask)
        module.smoothing_method.value = S.GAUSSIAN_FILTER
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assertFalse(result is None)
        np.testing.assert_almost_equal(result.pixel_data, expected)

    def test_03_03_gaussian_manual(self):
        '''Test the smooth module with Gaussian smoothing, manual sigma'''
        sigma = 15.0 / 2.35
        np.random.seed(0)
        image = np.random.uniform(size=(100,100)).astype(np.float32)
        mask = np.ones(image.shape,bool)
        mask[40:60,45:65] = False
        fn = lambda x: gaussian_filter(x, sigma, mode='constant', cval = 0.0)
        expected = smooth_with_function_and_mask(image, fn, mask)
        workspace, module = self.make_workspace(image, mask)
        module.smoothing_method.value = S.GAUSSIAN_FILTER
        module.wants_automatic_object_size.value = False
        module.object_size.value = 15.0
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assertFalse(result is None)
        np.testing.assert_almost_equal(result.pixel_data, expected)
        
    def test_04_01_median(self):
        '''test the smooth module with median filtering'''
        object_size = 100.0/ 40.0
        np.random.seed(0)
        image = np.random.uniform(size=(100,100)).astype(np.float32)
        mask = np.ones(image.shape,bool)
        mask[40:60,45:65] = False
        expected = median_filter(image, mask, object_size / 2 + 1)
        workspace, module = self.make_workspace(image, mask)
        module.smoothing_method.value = S.MEDIAN_FILTER
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assertFalse(result is None)
        np.testing.assert_almost_equal(result.pixel_data, expected)
        
    def test_05_01_bilateral(self):
        '''test the smooth module with bilateral filtering'''
        sigma = 16.0
        sigma_range = .2
        np.random.seed(0)
        image = np.random.uniform(size=(100,100)).astype(np.float32)
        mask = np.ones(image.shape,bool)
        mask[40:60,45:65] = False
        expected = bilateral_filter(image, mask, sigma, sigma_range)
        workspace, module = self.make_workspace(image, mask)
        module.smoothing_method.value = S.SMOOTH_KEEPING_EDGES
        module.sigma_range.value = sigma_range
        module.wants_automatic_object_size.value = False
        module.object_size.value = 16.0 * 2.35
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assertFalse(result is None)
        np.testing.assert_almost_equal(result.pixel_data, expected)        
