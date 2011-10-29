""" test_Measurements.py - tests for CellProfiler.Measurements

CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2011 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
"""
__version__ = "$Revision$"

import base64
import gc
import unittest
import numpy as np
import os
import tempfile
import zlib

import cellprofiler.measurements as cpmeas
from cStringIO import StringIO

OBJECT_NAME = "myobjects"

FLOAT_TYPES = [np.float, np.float32, np.float64]
datadir = os.path.join(os.path.dirname(__file__),'data')


class TestMeasurements(unittest.TestCase):
    def test_00_00_init(self):
        x = cpmeas.Measurements()

    def test_01_01_image_number_is_zero(self):
        x = cpmeas.Measurements()
        self.assertEqual(x.image_set_number, 1)

    def test_01_01_next_image(self):
        x = cpmeas.Measurements()
        x.next_image_set()
        self.assertEqual(x.image_set_number, 2)

    def test_02_01_add_image_measurement(self):
        x = cpmeas.Measurements()
        x.add_measurement("Image", "Feature", "Value")
        self.assertEqual(x.get_current_measurement("Image", "Feature"), "Value")
        self.assertTrue("Image" in x.get_object_names())
        self.assertTrue("Feature" in x.get_feature_names("Image"))

    def test_02_02_add_object_measurement(self):
        x = cpmeas.Measurements()
        np.random.seed(0)
        m = np.random.rand(10)
        x.add_measurement("Nuclei", "Feature", m)
        self.assertTrue((x.get_current_measurement("Nuclei", "Feature") == m).all)
        self.assertTrue("Nuclei" in x.get_object_names())
        self.assertTrue("Feature" in x.get_feature_names("Nuclei"))

    def test_02_03_add_two_measurements(self):
        x = cpmeas.Measurements()
        x.add_measurement("Image", "Feature", "Value")
        np.random.seed(0)
        m = np.random.rand(10)
        x.add_measurement("Nuclei", "Feature", m)
        self.assertEqual(x.get_current_measurement("Image", "Feature"), "Value")
        self.assertTrue((x.get_current_measurement("Nuclei", "Feature") == m).all())
        self.assertTrue("Image" in x.get_object_names())
        self.assertTrue("Nuclei" in x.get_object_names())
        self.assertTrue("Feature" in x.get_feature_names("Image"))

    def test_02_04_add_two_measurements_to_object(self):
        x = cpmeas.Measurements()
        x.add_measurement("Image", "Feature1", "Value1")
        x.add_measurement("Image", "Feature2", "Value2")
        self.assertEqual(x.get_current_measurement("Image", "Feature1"), "Value1")
        self.assertEqual(x.get_current_measurement("Image", "Feature2"), "Value2")
        self.assertTrue("Image" in x.get_object_names())
        self.assertTrue("Feature1" in x.get_feature_names("Image"))
        self.assertTrue("Feature2" in x.get_feature_names("Image"))

    def test_03_03_MultipleImageSets(self):
        np.random.seed(0)
        x = cpmeas.Measurements()
        x.add_measurement("Image", "Feature", "Value1")
        m1 = np.random.rand(10)
        x.add_measurement("Nuclei", "Feature", m1)
        x.next_image_set()
        x.add_measurement("Image", "Feature", "Value2")
        m2 = np.random.rand(10)
        x.add_measurement("Nuclei", "Feature", m2)
        self.assertEqual(x.get_current_measurement("Image", "Feature"), "Value2")
        self.assertTrue((x.get_current_measurement("Nuclei", "Feature") == m2).all())
        for a, b in zip(x.get_all_measurements("Image", "Feature"), ["Value1", "Value2"]):
            self.assertEqual(a, b)
        for a, b in zip(x.get_all_measurements("Nuclei", "Feature"), [m1, m2]):
            self.assertTrue((a == b).all())

    def test_04_01_get_all_image_measurements_float(self):
        r = np.random.RandomState()
        m = cpmeas.Measurements()
        r.seed(41)
        vals = r.uniform(size=100)
        bad_order = r.permutation(np.arange(1, 101))
        for image_number in bad_order:
            m.add_measurement(cpmeas.IMAGE, "Feature", vals[image_number - 1],
                              image_set_number=image_number)
        result = m.get_all_measurements(cpmeas.IMAGE, "Feature")
        np.testing.assert_equal(result, vals)

    def test_04_02_get_all_image_measurements_string(self):
        r = np.random.RandomState()
        m = cpmeas.Measurements()
        r.seed(42)
        vals = r.uniform(size=100)
        bad_order = r.permutation(np.arange(1, 101))
        for image_number in bad_order:
            m.add_measurement(cpmeas.IMAGE, "Feature",
                              unicode(vals[image_number - 1]),
                              image_set_number=image_number)
        result = m.get_all_measurements(cpmeas.IMAGE, "Feature")
        self.assertTrue(all([r == unicode(v) for r, v in zip(result, vals)]))

    def test_04_03_get_all_image_measurements_unicode(self):
        r = np.random.RandomState()
        m = cpmeas.Measurements()
        r.seed(42)
        vals = [u"\u2211" + str(r.uniform()) for _ in range(100)]
        bad_order = r.permutation(np.arange(1, 101))
        for image_number in bad_order:
            m.add_measurement(cpmeas.IMAGE, "Feature",
                              vals[image_number - 1],
                              image_set_number=image_number)
        result = m.get_all_measurements(cpmeas.IMAGE, "Feature")
        self.assertTrue(all([r == unicode(v) for r, v in zip(result, vals)]))

    def test_04_04_get_all_object_measurements(self):
        r = np.random.RandomState()
        m = cpmeas.Measurements()
        r.seed(42)
        vals = [r.uniform(size=r.randint(10, 100)) for _ in range(100)]
        bad_order = r.permutation(np.arange(1, 101))
        for image_number in bad_order:
            m.add_measurement(OBJECT_NAME, "Feature",
                              vals[image_number - 1],
                              image_set_number=image_number)
        result = m.get_all_measurements(OBJECT_NAME, "Feature")
        self.assertTrue(all([np.all(r == v) and len(r) == len(v)
                             for r, v in zip(result, vals)]))

    def test_05_01_test_has_current_measurements(self):
        x = cpmeas.Measurements()
        self.assertFalse(x.has_current_measurements('Image', 'Feature'))

    def test_05_02_test_has_current_measurements(self):
        x = cpmeas.Measurements()
        x.add_measurement("Image", "OtherFeature", "Value")
        self.assertFalse(x.has_current_measurements('Image', 'Feature'))

    def test_05_03_test_has_current_measurements(self):
        x = cpmeas.Measurements()
        x.add_measurement("Image", "Feature", "Value")
        self.assertTrue(x.has_current_measurements('Image', 'Feature'))

    def test_06_00_00_dont_apply_metadata(self):
        x = cpmeas.Measurements()
        value = "P12345"
        expected = "pre_post"
        x.add_measurement("Image", "Metadata_Plate", value)
        pattern = "pre_post"
        self.assertEqual(x.apply_metadata(pattern), expected)

    def test_06_00_01_dont_apply_metadata_with_slash(self):
        x = cpmeas.Measurements()
        value = "P12345"
        expected = "pre\\post"
        x.add_measurement("Image", "Metadata_Plate", value)
        pattern = "pre\\\\post"
        self.assertEqual(x.apply_metadata(pattern), expected)

    def test_06_01_apply_metadata(self):
        x = cpmeas.Measurements()
        value = "P12345"
        expected = "pre_" + value + "_post"
        x.add_measurement("Image", "Metadata_Plate", value)
        pattern = r"pre_\g<Plate>_post"
        self.assertEqual(x.apply_metadata(pattern), expected)

    def test_06_02_apply_metadata_with_slash(self):
        x = cpmeas.Measurements()
        value = "P12345"
        expected = "\\" + value + "_post"
        x.add_measurement("Image", "Metadata_Plate", value)
        pattern = r"\\\g<Plate>_post"
        self.assertEqual(x.apply_metadata(pattern), expected)

    def test_06_03_apply_metadata_with_two_slashes(self):
        '''Regression test of img-1144'''
        x = cpmeas.Measurements()
        plate = "P12345"
        well = "A01"
        expected = "\\" + plate + "\\" + well
        x.add_measurement("Image", "Metadata_Plate", plate)
        x.add_measurement("Image", "Metadata_Well", well)
        pattern = r"\\\g<Plate>\\\g<Well>"
        self.assertEqual(x.apply_metadata(pattern), expected)

    def test_06_04_apply_metadata_when_user_messes_with_your_head(self):
        x = cpmeas.Measurements()
        value = "P12345"
        expected = r"\g<Plate>"
        x.add_measurement("Image", "Metadata_Plate", value)
        pattern = r"\\g<Plate>"
        self.assertEqual(x.apply_metadata(pattern), expected)

    def test_06_05_apply_metadata_twice(self):
        '''Regression test of img-1144 (second part)'''
        x = cpmeas.Measurements()
        plate = "P12345"
        well = "A01"
        expected = plate + "_" + well
        x.add_measurement("Image", "Metadata_Plate", plate)
        x.add_measurement("Image", "Metadata_Well", well)
        pattern = r"\g<Plate>_\g<Well>"
        self.assertEqual(x.apply_metadata(pattern), expected)

    def test_07_01_copy(self):
        x = cpmeas.Measurements()
        r = np.random.RandomState()
        r.seed(71)
        areas = [ r.randint(100, 200, size=r.randint(100, 200))
                  for _ in range(12)]

        for i in range(12):
            x.add_measurement(cpmeas.IMAGE, "Metadata_Well", "A%02d" % (i + 1),
                              image_set_number=(i + 1))
            x.add_measurement(OBJECT_NAME, "AreaShape_Area", areas[i],
                              image_set_number=(i + 1))

        y = cpmeas.Measurements(copy=x)
        for i in range(12):
            self.assertEqual(
                y.get_measurement(cpmeas.IMAGE, "Metadata_Well", (i + 1)),
                "A%02d" % (i + 1))
            values = y.get_measurement(OBJECT_NAME, "AreaShape_Area", (i + 1))
            np.testing.assert_equal(values, areas[i])

    def test_08_01_load(self):
        data = ('eJzt3M1LFGEcwPFnZtZ2VcSXS29Gewm8BJu9KHgxUtvAl6UX8GDpmmMWauIL'
                'SPQH6M2jl6Bb0qGgCK92M+rWRZAg6BJB4LFL2D7zPM/uztS4smtYu9/P5fH5'
                'zTPP7M7+5pnxML/lZFdPXc2JGiHFYiIiGkS+XW31jb9vto/o1tLtkm7XbBO3'
                'vG3HdLxRzx8cd/N6d7ccvRtgjvO5SrUxgUqU7L6cku2g7pt82rT94/rc9NzC'
                'rDvlTs/Pyb7Jy84ijxuWv0lH9Sd0XhbK36/VqiV/K1Mwf80qu1TlH3dtKn3P'
                'Fbm8TZZ43Bv9A10yg03exZ0SJ6xQYetAKqr6M/r6LrQO7NSp1syDyhJcB1p0'
                'u1LtH+etA/0LU6PurNfvc+fTY+n59HBqMj3v5taHxD6PG1wHWqLFfoPKFrYO'
                'DNaq/qK+vgutA0l9A/A/baNShD3Prtb5x8lrXrb3p8fcRVH686xaB+zsOpCo'
                '3Xu8+Vyx20UesExZIqp+C/2DVGXOqPzTdlTEyVzZ8o+GzImOeCPiej91Ri1L'
                '7Wgex8z6UCvavf0s/X+N7c1ribmJhfHxSVfPJbyVXMbH3HHvhmDiscz8cn/H'
                'trd6dSwisptFk/7l5Zi+nub+4jPJL5hX7fV7jzfr3krjgRy+bFjiSJF5pZ4k'
                'LNufV8H8Mv1cnjhPm3QsooZ70/6eJzMH/E33R95HrT/dRws8+Gw1BwL6CnD8'
                'XQAAAJQJK6+181onrwUAAAAAAAAAAAAAAAAAAAAAAIcr7L3RUyHjY7cCgYiv'
                'AQAAZWjxzve3Vl3mOcCJv/zZsf3FedWWiXauRx/+ENHMxs11S8RjIvF+Y/dk'
                '/c6zjtNr71aXZCmXje3W10d3lp9/04X8hh68+CRr6ix+sB49dj4e4lcCAAAF'
                'hNV1TOi6d6lh1Raq67g1olrqOlamsLqOM8P+cQdd17FwPUJV7+24pXKzITvU'
                '1HkrrS6hyfd91CWceKJjkbzLJL/e3JBXb669yDOhBOsRbg7vOTz7QeKjJR22'
                '7BxCPcLEXR0Lq0c49B/WI5yYCgSoRwgAAFDWqEcIAAAAAAAAAAAAAAAAAAAA'
                'AMC/L+y90Y6Q8WdC6hFSVwAAgPJ19cpAr/fOoL7hm/cHo7pNnT3Xev7CRWH/'
                'FpfhS9n3CXNxGW7Lzr9W/5c+OAAAAAAA2LdfZABKkA==')
        data = zlib.decompress(base64.b64decode(data))
        fd, filename = tempfile.mkstemp('.h5')
        try:
            f = os.fdopen(fd, "wb")
            f.write(data)
            f.close()
            m = cpmeas.load_measurements(filename)
            for i in range(1, 4):
                self.assertEqual(m.get_measurement(
                    cpmeas.IMAGE, 'ImageNumber', i), i)
            for i, plate in enumerate(('P-12345', 'P-23456', 'P-34567')):
                self.assertEqual(m.get_measurement(
                    cpmeas.IMAGE, 'Metadata_Plate', i + 1), plate)
        finally:
            try:
                os.unlink(filename)
            except:
                print "Failed to remove file %s" % filename

    def test_09_01_group_by_metadata(self):
        m = cpmeas.Measurements()
        r = np.random.RandomState()
        r.seed(91)
        aa = [None] * 100
        bb = [None] * 100
        for image_number in r.permutation(np.arange(1, 101)):
            a = r.randint(1, 3)
            aa[image_number - 1] = a
            b = "A%02d" % r.randint(1, 12)
            bb[image_number - 1] = b
            m.add_measurement(cpmeas.IMAGE, "Metadata_A", a,
                              image_set_number=image_number)
            m.add_measurement(cpmeas.IMAGE, "Metadata_B", b,
                              image_set_number=image_number)
        result = m.group_by_metadata(["A", "B"])
        for d in result:
            for image_number in d.image_numbers:
                self.assertEqual(d["A"], aa[image_number - 1])
                self.assertEqual(d["B"], bb[image_number - 1])

    def test_09_02_get_groupings(self):
        m = cpmeas.Measurements()
        r = np.random.RandomState()
        r.seed(91)
        aa = [None] * 100
        bb = [None] * 100
        for image_number in r.permutation(np.arange(1, 101)):
            a = r.randint(1, 3)
            aa[image_number - 1] = a
            b = "A%02d" % r.randint(1, 12)
            bb[image_number - 1] = b
            m.add_measurement(cpmeas.IMAGE, "Metadata_A", a,
                              image_set_number=image_number)
            m.add_measurement(cpmeas.IMAGE, "Metadata_B", b,
                              image_set_number=image_number)
        result = m.get_groupings(["Metadata_A", "Metadata_B"])
        for d, image_numbers in result:
            for image_number in image_numbers:
                self.assertEqual(d["Metadata_A"], aa[image_number - 1])
                self.assertEqual(d["Metadata_B"], bb[image_number - 1])

    def test_10_01_remove_image_measurement(self):
        m = cpmeas.Measurements()
        m.add_measurement(cpmeas.IMAGE, "M", "Hello", image_set_number=1)
        m.add_measurement(cpmeas.IMAGE, "M", "World", image_set_number=2)
        m.remove_measurement(cpmeas.IMAGE, "M", 1)
        self.assertTrue(m.get_measurement(cpmeas.IMAGE, "M", 1) is None)
        self.assertEqual(m.get_measurement(cpmeas.IMAGE, "M", 2), "World")

    def test_10_02_remove_object_measurement(self):
        m = cpmeas.Measurements()
        m.add_measurement(OBJECT_NAME, "M", np.arange(5), image_set_number=1)
        m.add_measurement(OBJECT_NAME, "M", np.arange(7), image_set_number=2)
        m.remove_measurement(OBJECT_NAME, "M", 1)
        self.assertTrue(m.get_measurement(OBJECT_NAME, "M", 1) is None)
        np.testing.assert_equal(m.get_measurement(OBJECT_NAME, "M", 2),
                                np.arange(7))

    def test_10_03_remove_image_number(self):
        m = cpmeas.Measurements()
        m.add_measurement(cpmeas.IMAGE, "M", "Hello", image_set_number=1)
        m.add_measurement(cpmeas.IMAGE, "M", "World", image_set_number=2)
        np.testing.assert_equal(np.array(m.get_image_numbers()),
                                np.arange(1, 3))
        m.remove_measurement(cpmeas.IMAGE, cpmeas.IMAGE_NUMBER, 1)
        np.testing.assert_equal(np.array(m.get_image_numbers()), np.array([2]))

    def test_11_00_match_metadata_by_order_nil(self):
        m = cpmeas.Measurements()
        result = m.match_metadata(("Metadata_foo", "Metadata_bar"),
                                  (np.zeros(3), np.zeros(3)))
        self.assertEqual(len(result), 3)
        self.assertTrue(all([len(x) == 1 and x[0] == i + 1
                             for i, x in enumerate(result)]))

    def test_11_01_match_metadata_by_order(self):
        m = cpmeas.Measurements()
        m.add_measurement(cpmeas.IMAGE, "Metadata_foo", "Hello", image_set_number=1)
        m.add_measurement(cpmeas.IMAGE, "Metadata_foo", "Hello", image_set_number=2)
        result = m.match_metadata(("Metadata_bar",), (np.zeros(2),))
        self.assertEqual(len(result), 2)
        self.assertTrue(all([len(x) == 1 and x[0] == i + 1
                             for i, x in enumerate(result)]))

    def test_11_02_match_metadata_equal_length(self):
        m = cpmeas.Measurements()
        m.add_measurement(cpmeas.IMAGE, "Metadata_foo", "Hello", image_set_number=1)
        m.add_measurement(cpmeas.IMAGE, "Metadata_bar", "World", image_set_number=1)
        m.add_measurement(cpmeas.IMAGE, "Metadata_foo", "Goodbye", image_set_number=2)
        m.add_measurement(cpmeas.IMAGE, "Metadata_bar", "Phobos", image_set_number=2)
        result = m.match_metadata(("Metadata_foo", "Metadata_bar"),
                                  (("Goodbye", "Hello"), ("Phobos", "World")))
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 1)
        self.assertEqual(result[0][0], 2)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0], 1)

    def test_11_03_match_metadata_different_length(self):
        m = cpmeas.Measurements()
        m.add_measurement(cpmeas.IMAGE, "Metadata_foo", "Hello", image_set_number=1)
        m.add_measurement(cpmeas.IMAGE, "Metadata_bar", "World", image_set_number=1)
        m.add_measurement(cpmeas.IMAGE, "Metadata_foo", "Goodbye", image_set_number=2)
        m.add_measurement(cpmeas.IMAGE, "Metadata_bar", "Phobos", image_set_number=2)
        m.add_measurement(cpmeas.IMAGE, "Metadata_foo", "Hello", image_set_number=3)
        m.add_measurement(cpmeas.IMAGE, "Metadata_bar", "Phobos", image_set_number=3)
        result = m.match_metadata(("Metadata_foo",),
                                  (("Goodbye", "Hello"),))
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 1)
        self.assertEqual(result[0][0], 2)
        self.assertEqual(len(result[1]), 2)
        self.assertEqual(result[1][0], 1)
        self.assertEqual(result[1][1], 3)

    def test_12_00_load_version_0(self):
        data = ('eJzr9HBx4+WS4mIAAQ4OBhYGAQZk8B8KTiig8mHyCVCaEUp3QOkVTDBxRrCc'
                'BFRcEGo+urqQIFdXkOr/aABmzwNWCM3BMApGIvBwdQwA0RFQPiw9nWBCVeeb'
                'mlhcWpSam5pXUgziw9KlA5n24kq/HswQfgY0XRJKvy84IfRo+h2ZAD39wkrZ'
                'DlZUdZ65iempDIh060GhvcF+/i6gFAxLdwrMFBo4QgGuciCAHcIvgOZvQuXA'
                'B14IDTNnFIwsgF4OKEDpCZyo6sDlgF9pblJqEZiflp8PpmHlggWJ9qKXAxrs'
                'JBowCsAAVzkQwQ3hV0DzN6FywANqAGprexSMFICrPTuDF1VdSmJJIojOzEtJ'
                'rWCgvD0LKQeY4OWAATd+9TB3LZAi08JhChgZ2CBxAY0QVmCIgphMTExgEWZg'
                'zgYxBIABzQJWoQDVB8nxjIwwcyCAAxjSIDYzowe0SGBBsU8IGmMgNbzNhn6I'
                'HvTgAIwMCL+AaEsDVP4oGAWjYBSMglEwCoYfQG9XWvDjVw/r90yQpKWrhh4g'
                'v10JaakzwuddIAA23IdoX/pAg54HxV7k9qU8uH3ZQEVfkQ9w9bdPQPsjL2Qg'
                'NKH+doEchB7tb49MgKu/zSGLqo7a/W3a9RMjCPYTwwdhPxG9nkiQxascnl93'
                'yNPSVUMP0L6eiCFYT+QMonoCAIv/qlY=')
        data = zlib.decompress(base64.b64decode(data))
        fid, name = tempfile.mkstemp(".h5")
        m = None
        try:
            fd = os.fdopen(fid, "wb")
            fd.write(data)
            fd.close()
            m = cpmeas.load_measurements(name)
            self.assertEqual(tuple(m.get_image_numbers()), (1,))
            self.assertEqual(m.get_measurement(cpmeas.IMAGE, "foo",
                                               image_set_number=1), 12345)
        finally:
            if m is not None:
                del m
            os.unlink(name)

    def test_12_01_load_version_1(self):
        data = ('eJzt3E9sFFUcwPH3Zrft0lIpDUGCBWqiUg8124ZAQQslUqwxtkSQlAvplu7a'
                'Ymlr/yQ9mWKIKZgoRw5GS2JMI2rqQSFeEE94MZyM8WBKwMDBIkFDMGDrzr73'
                'dneGzi4sq7vd/X44/Hbe/HZmOrx582aT+R1v27W7snxtubAFAsIvqkSyBW3/'
                'UelYNuu7dJQ6Tuo4bZl2GVu3Rrev1Nt35+17rbXVzl5wMfsJ+lUMCBSjttad'
                'e+zYqZdrdbxoOfP2h4dH+gYHxKvh0MjYcPhIeGB0xG43/bPpIfcrRan6rt5A'
                'SbQH2h8ty4q1+KL92f5QFe2Y/qQjk7qfS2m2owSiV4L92Se7dFf2O/ZXrXu4'
                'nfPr8Yb2xJWSH/a2d+ySwoqPEuMlqfPN9Vrr+y+PaunxGhen9Pn8rkzFdOPi'
                'nWoVGReLk9e4OFvmzGsMNjTUB7fUNzbVNzTaHzY1xtozHxcX779demCYqDZ5'
                '0THi4NwFWSnEcmvq7vzpucsT9+zWK+U75oX/czH7ijjstbUvdbf+Uc1P0l4N'
                '+5er6JzDoFi4rwbTn26UO/N6QqMhO/YN9ITHReIqaMlwv1KULT5L8Ik0swR1'
                'hFJPE8xkxvTriuh1aa+ReoUV264UI71jkUh/OD53kLq9JxzpD40m2uOzDcvq'
                '/FC3+ZOmHMmzDd8Je7aR6RlwMrMEc1faXZE631yvH1VmZfcFw3P2mbZf1alo'
                'OfuVmYSZ/mWWE/3EV9ut2/wqPbbZ+/vJUJb/0gcTu5Msi36wpq4vXH/72C+l'
                '0c9NWzrmRUl01cUnpQgGxMxL32+v+G3yxEarf/j8+qF9V2uit6UzpU81yLDn'
                '0+gnann1ChXd40hQx80rnMfTHRqOxZePhN4It48d6Q6r5Y7uw+FDo4kGM77U'
                'pfn7vI5v+lO1/I3H8Zn8n1zHl+1xzj7JDStFbUC0bH3vqwMnjz3z1sZ37n3w'
                '8bWr1u5vXz+7Ifji7+v+ERPnm5uX+VXfSnfHFo+rwB27OHn15KlqZ17sCovG'
                '9rFD/eG+R+/J6g4l43eoJh6gMuI1YvWuUsuTq1VMNw4EntDxfzpu5Bev59jp'
                '1c68yOBgLLrvuJk+x7pnqi2rUueb+9SNxx5yRwXOaxwY0g0n16qYbhzoWqci'
                '84Hi5DUfmFnrzMv2zNb9u/a7aW5EZnXbmpRpRWcJ/BJy84Buy8UvIXtqUueb'
                '/je9Piu7Lxg5+CXk3Abdlo+/hNj3UbnYfTSY+ns3n3U16CvA51wEAABAgZBJ'
                '0UqKAAAAAAAAAAAAAAAAAAAAAAAgf3i9N/q0R/4P7joXfkcAAAAFKNM6E539'
                'rgbqTAAAABQ06kwAAAAAAAAAAAAAAAAAAAAAAJD/vN4brfHI7wm4GqgzAQBA'
                'wbPnC2KxOhPaxWkV3dMEFId0/aP2jIpVuTpA5NTe9o5dUvji//+zf6TOr9Vx'
                'qEmmSouPN++veISDW0KkKFPvbuvTUhI9A7F3t32qxT7D9oeqgHk2q9XfW6Oi'
                'VF80z23mOq0QTbHvSf0SuBXbrhQjvWORSH84ni91e0840h8aTbQHotu3v++z'
                'rJlrus2f9HhYrf+n7JwdJxrahWjJyvlQ/cqK94Oqz1Lnm/7X+3lWdl8wpCjN'
                'sF/VqWipL5oaAqaOlOlfZjnRT3zjX+g2v0qPbfb+fjKU5b/0wWRaV2vmrKuB'
                'uloAAAAFzUqKpqYWcz4AAAAAAAAAAAAAAAAAAAAAAPKL13uj9R75z7kLIlBX'
                'CwCAgidj/4SuziLESl2hJHBTLdfdUjFdfaWZP1WkvlJxamvduceOnXrZ9Ke2'
                'W868ntBoyI59Az3hcREv95JxNZ4lUI+oJaiPLRf1iKZupUyPX693/srK7gtG'
                'DuoRBW7rtkKqR9QSv8I16hEBAAAUNOoRAQAAAAAAAAAAAAAAAAAAAACQ/7ze'
                'G13nkV9zdPH3RXlnAACAwuVVj+hUk5oXnNumYrp6RC0vqDzqERUnr3pEP29z'
                'zi+LsB7RpfEc1iMKPi9T5pvrdbI5dV6xyUE9olPbE/2kYOoRXWqjHhEAAEAx'
                'oR4RAAAAAAAAAAAAAAAAAAAAAAD572HrEW2lHhEAAEVn/ODcBVkpxHJr6u78'
                '6bnLE/fs+cCV8h3zwp+07s2FS7fvTGzeGl03+7Uc/FuU3bdyU7NeeVuU/Qv/'
                'J+C3')
        data = zlib.decompress(base64.b64decode(data))
        fid, name = tempfile.mkstemp(".h5")
        m = None
        try:
            fd = os.fdopen(fid, "wb")
            fd.write(data)
            fd.close()
            m = cpmeas.load_measurements(name)
            self.assertEqual(tuple(m.get_image_numbers()), (1, 2))
            self.assertEqual(m.get_measurement(cpmeas.IMAGE, "foo",
                                               image_set_number=1), 12345)
            self.assertEqual(m.get_measurement(cpmeas.IMAGE, "foo",
                                               image_set_number=2), 23456)
            for image_number, expected in ((1, np.array([234567, 123456])),
                                           (2, np.array([123456, 234567]))):
                values = m.get_measurement("Nuclei", "bar",
                                           image_set_number=image_number)
                self.assertEqual(len(expected), len(values))
                self.assertTrue(np.all(expected == values))
        finally:
            if m is not None:
                del m
            os.unlink(name)
            
    def test_12_04_load_withrel(self):
        finame = 'test_rel_01.h5'
        path = os.path.join(datadir,finame)
        meas = cpmeas.load_measurements(path)
        self.assertIn(cpmeas.RELATIONSHIP, meas.hdf5_dict.top_group)
        groups = meas.get_relationship_groups()
        self.assertEquals(len(groups), 1)
        group = groups[0]
        expected_length = 114
        temp = meas.get_relationships(
                                group.module_number, group.relationship, group.object_name1,
                                group.object_name2, group.group_number)
        keys = ['group_index1','group_index2','object_number1','object_number2']
        for key in keys:
            data = temp[key]
            self.assertEquals(len(data), expected_length)

    def test_13_01_load_matlab(self):
        data = ('eJztHEtzHEd5pCghVkhi3gmVQ5NylS2XJe3KWlueCpFkSbYV9CpLsRMss+nd'
                '6d3teF7MQ7tLTBXHcM2JOweuUFw4pfIDuFHAkRTwA3wCDqSK7+vu2XnsrPYh'
                'aYuAxrX2dvf36u/VX/f0env1YGv1NinNFcj26sFsjZuM7Jk0qDmepRM7uEbW'
                'PEYDZhDH1slBIySrYZ0UFkmxoC8s6cUlslAoFrXRnonN7Vfw33c07QX450X4'
                'TKqh51V7IvH5Cnwa1DZM5sP4lPay6l+Ez1roecwOJPI2o37oMQs6fG3PYzUG'
                'Y1XA0vZZEHC77ndEQP73pgbjL/untO+o9hfw2QmtCvN2a5sWrTOgrijDt9sM'
                'GK3a1Gz/hBkKO4LedowQZ6GefXrEdsPADYN7TnO3FjBbdB9wi+0H1As6+BIa'
                'u4B2xDLZHbrr3GPVwPHaqnud1WhoBpJ8PKi6BY0EimgfOI7p3wFPsKklhex0'
                '32OmmzIh6m9Ji/X3Qh/9XVD96lk5DfxCAv+rA9hvUsk9LN6EwttL4E3l4H03'
                'gXdRtTFKZgtLs3Hk3Jy7daNUKBRiPY4qT1J/efK8qKXlwfaafhh4of1E+H8f'
                '/G9m8LFdBXxmuYcVahxyqz5bXFwqRPM4bXpugt5EDr2kXhB+pQ//lzL8sS08'
                'nATo+bn2yPpl9CT9MsLbe2O4fBLJ8z34bLRc5nHMXFIkCbUTVk3GE2wFH/Lq'
                'cHy+rtqXUEbuMpPbrBx9Ac48KEMSCUI/w+feK8Pp/7VXjtf/319O6x/ba8w0'
                '9zwH1x+PRDLppBEErj4/32w256oA4SqIOcerTz9gns9hVVqY3n+wc58dcdEq'
                'FhcLi9PTWw41hAJ9/ZElsm3ZDi29+NQ/sstHCvPwcrF4/Vbp8PLTI+pxWgEg'
                'T9FBaEjVQO6p33Ca5Sa3DaepH3ghe2o7AZA9bJVuw2f9aYUG1UbZB80xnXoe'
                'bV+Jhq4RI2i77Psht4OlmcfTBB7MqwR7wdlIhRETBGWGDuT5ETdCahIuxI6B'
                'fWZCegaZiMWChmPoB6wVzG60aDUgFvIWoHJpIU5N4RNuE0arDVL3nNBd1q8L'
                'qAPBuAEfoAFfaCBarFU1QxAjwm3AgoQEqo5lgZ7WHQJzJqHPBBG1qBFqmsQP'
                'KzXHNEChpMmDBuAgPSky0JNjy/qOY0vcTRuWIcmGiGLDdKoUJ6erFUlB3BGI'
                'h62bax3UtQarPlGoPqy0QNwjFvd9WAsJfDVC1+RATBL2l/X3lRbvogaiqVXa'
                'qEZq0ICiWAJgQ06fVJkXUJiCwlej+y6r8lqMBsPMNHy0n9AtkNQloJh1UiUA'
                'QqWyJITMMlUntAO9KA2StIPP8g1ArlSpz2Z9Zvs84EdsRvdhpeeGoLDnYCcA'
                'genBAL7SUMr8itlGK/CE13Rm4jkWaTagPEqY6D6rhyb1wClcj/kYDFLAGvio'
                'H+MqUwsjYqGg/+jK8t5bWDuyt+euzpSx9RBi9m2MhtXZPQwI/FqYvYVfP1r4'
                '6UzZR6B9DhiJkZm0p3pDidNRPnFp0NDnropYVM88kkeW60rI3MH7oY1jl5TT'
                'UdtmZspm0p+Qm+UccVCBh3VSx1/EMPqkCtdNO2CeycCiRiZSq5K4TyDnK0PJ'
                'MMXsJRhwEQzUj/wC3NypfAheBuw24zyxAwJI48t0IsH19Z3V/GFJQ5fLijK6'
                '8HwnDDDx+ihdCjaeniLGIljFa0tAC5l2FZGUAqN8qrj5VWri9ALp01G4Tm8a'
                'sPRBtO3BIki99q5knsrhC905/HrxuBx+65RTuIrz2D652mbElXOINKgSPpcz'
                '5JD0E/oHd4fcZRKDA3Yg3UPhXUPfdnkLlBjaHOhc2eb2tW3amtGLhWuLBYG/'
                'zkGjXsdaaBwfOAk5OjQ9atdZx5AHIBqIZDFPVj7EtzCjRxQwnRObUQ8yJsRf'
                'nXldrpBlGjhhtYGej1wrjmfIeQhFoYrilJxQYdCAsG5AzCZCZjfwQ3LXdCrU'
                'lKJGMBCHnqdWwxrFTYvyqC2nCcxgc0hCF6OpAvEK6UEkC4WrF+YK4rlWVF/k'
                'auZCVdEC+QIRydUol3KVq8HRIAoq7Xj2QEcy3RbSohIN7uOWLOR+g8BaYrlx'
                '4Ij4RydvZ3E82iRi1ceZy7CrsKDJmN2Hxj6H1RdE9C3HCYTCIQsHGF1ySvug'
                'A8yVYnE1oUjA6cmsST2Yk+n4oCJo2zIrWNzmVmjhgg5qNMRsKGyY9ZvRAshQ'
                'r6iEUKy2CObNAgvHDIW+uCqfRVZOsY1t3iNxRJGeTBpQ95gEbCbLmDhiYhtE'
                'RFfDwAHTYeyYbQJ/V0NcgYjfQ0X9MXspo2Ob/NltUxuLt5S3JV29wm3MBXLO'
                'ibW2K+2KaMmZsYq5XmKnQkmZCftEKMmwioXdwCWJbFHXpFVOhbvfpSEsrjQd'
                'LyUZfU1ntmpSXyw/OMxUMxm6yzqAEdEfaQQViWZAMZqM1xtYEYosjeoUtKD0'
                'tAPPcdvL+sMshJwuCFVX6c+PFnmLG0Zi9WgTJY4jKxIHSgYP4z/iUaHVJ7Jn'
                'Wb/TGe2rzsiHovRWU+Ty9Zb1L6Vj564a6aRhXWr1Hp5kidI15sBrWIpjlQPl'
                'n92pEzrD8dKx5sA3O2TK91rCZbsw9FKhkM23Vnw4JjUW+Qwm/Ngz4zwVKwUq'
                'LRfrTyKXUqEgWYaIr6nclIHF1BTtDxvacPvJkc43HMs1QduI/6/p4fbJl1X7'
                '00mkA3VfuXv/nXlEzVeWld0xYJ11rHwH0oEZN9MMttdL6xxqu6AMNUVvavdE'
                'xBwP05Ft0zZY6ziwWJgoEh+oQExJh1tSzOR92O5B9T0AWMx0P7R2axsiGUA1'
                'mFHIRotVxUKDR6LlQjHe3aeoPeRG0OirjwTTXY/Xexkhy3QhvzTV5Fnuhuc5'
                'Xm8gTXv3/lZ/yTRtH6INkkI/0BTTXurA56TxNtx57LNlxP9gSH6jnnuOY15/'
                '+vG/v3hV+7WY18+G5NfvnJho6byF7VK1xJboYmmpslC7sUhLxVKhyG5cv1Uq'
                'FW4slYzFceh3S+GdNZ9x2lFL4J/2efK0lrYjtuUBzZxr12M6rSH5nvY5+jj0'
                '/MmFvzyr/+H1z8Zm19//9aPSP341lrzz7hj1mMw7Y9Hje5+89ed//nYseozw'
                'Ph6Sz3va8fFwOQF/UbXxeFKfn59f0+cxLuYhLuajuJhPBOlY89Dnzso49fzZ'
                'xHD177dUe1mL3liXZR0TFbhb6sy+vMZwk1N+HzGzne91+J/1PMe5jvxwZueP'
                'P59aWxkXv998+2+//ME7q4Lfs+dGv6ewhxto3JtpqUe9dJHlZNftgEEvDUT7'
                '8DXHdLxtqm4IbNEKM9Nd+OwHHnc7bx3j7ifcFfVsuoZd5z5sttsgIHtAzTBC'
                'uAPb3+7ZRNAPxZYzReg06toV7fj8czGBf1F9ovfsh+rKx5fhfXuhD72pFL0p'
                're7R9iB4z6XwntM+ZMFA/LJ478M+ZxC8yRTepLbjnCy/DIs3rXX7XRZvsgsv'
                'TQ/xP780XNy/ptrP4PNAvRQRwZOIiKh/0645+KotGpJuuhNd/Ok8MvP7u7UI'
                'UQ33yCsd+tF7eYWv6Gd7O3zxtUyKzn7Dad7B92sZ+rfxjQ3eVsgMoL5+d7F3'
                'Xkb9vZnoHyR+vqal4wfbXe/rE/SG9Wfc64+aX7J3AQY5L3shQwfb0dnHIPJP'
                'pPAntOvaYOd0z2f4Ylu8wdJG32fFVxMG1/8geWGQvIdnpSfh1+984PXMfLGd'
                'd0viKQqiDT7/UfNpL7yVPnh5960Sb/gGlntUu2X9tXhCfqPki653j2r8JPfM'
                'hvVXfG95En4rffhdyMwb253acAi5e9nrtPiPkh/lVnE0vykWztZPs3g3B8Qb'
                'NZ/1ygONPng3M3rFdq9LQ49WZ/cePyrM3nqcuSgk+mYG8odXM/ywnXnbPNC5'
                'wqUMHWzPXX10eDj/OHmZqNMRXSDSBrTDqPl4VH85y3r6rNeNxGUqbVT9Qh48'
                'UZ0zalyNknei1zrjtE9Uj45q17OuP7vtWTqRflb64OX5YeKyg+gfpC74RoYO'
                'tnOuzQ1ML6/O6LpFocbPct3Nq8vjaxaD8z/tuvSs6qqsnko5eMPwG+1+g7z/'
                'cZbzzOq1VOjOm2dZr+bVI6dZr+b5bXybJV/u05xvrzrx48TvOiYyeHnnF+PU'
                'jzjsEFeVT85/lPwmLzbJe/fcNpiboHcadjrHO8c7xzvHO8f778VbSeANek4e'
                'r1ty2fgyzfccb7z+c9Z1z5fV7/9f67WVPvM+zzfneOd4/7t4FydivOx+PLuP'
                'R/gPEnzy8sVVLZ0vsJ363w3kj139OfwFrrxdMJe94o98Wn343M7wud2Lj/pd'
                'UVv9YFX9eGiu528ZcvR5IYd/Ui+T8OeNN0/nHtawfF+60C3vS33wpoa4p5q1'
                '/5Vj4KPnJPDDzn9iQuL9Ysh5HMcnK9fkCfH+A86LP/E=')
        data = zlib.decompress(base64.b64decode(data))
        fid, name = tempfile.mkstemp(".mat")
        m = None
        try:
            fd = os.fdopen(fid, "wb")
            fd.write(data)
            fd.close()
            m = cpmeas.load_measurements(name)
            self.assertEqual(tuple(m.get_image_numbers()), (1,))
            self.assertEqual(m.get_measurement(cpmeas.IMAGE, "Count_Nuclei",
                                               image_set_number=1), 1)
            values = m.get_measurement("Nuclei", "Location_Center_X", 1)
            self.assertEqual(len(values), 1)
            self.assertAlmostEqual(values[0], 34.580433355219959)
        finally:
            gc.collect()
            if m is not None:
                del m
            os.unlink(name)

    def tst_combine(self, img_nums_1, img_nums_2):
        """
        Test combining features of 2 different image sets,
        with sequential image numbers
        """
        obj_nums = xrange(0, 2)
        feat_nums = xrange(0, 3)
        all_img_nums = set(img_nums_1) | set(img_nums_2)

        mknums = lambda pre, post: ['%s_%s' % (pre, pst) for pst in post]
        obj_names = [cpmeas.EXPERIMENT, cpmeas.IMAGE, cpmeas.OBJECT]
        feat_names = mknums('Feat', feat_nums)

        modnum = 5
        groupnum = 1
        relname = 'relname'
        object_name1 = 'objectname1'
        object_name2 = 'objectname2'
        rel_names = ['%02d_%d_%s_%s_%s' % (modnum, groupnum, relname, object_name1, object_name2)]
        group_indices = np.ones(10)
        obj_numbers = np.arange(0, 10) % max(obj_nums)

        r = np.random.RandomState()
        r.seed(3)

        set1 = cpmeas.Measurements()
        set2 = cpmeas.Measurements()
        ideal_comb = cpmeas.Measurements()

        for obj_name in obj_names:
            for feat_name in feat_names:
                if(obj_name == cpmeas.EXPERIMENT):
                    img_nums = [0]
                else:
                    img_nums = all_img_nums
                for img_num in img_nums:
                    sz = img_num % 3 + 1
                    data = r.randint(0, 10, sz)
                    ideal_comb.add_measurement(obj_name, feat_name, data,
                                               can_overwrite=False,
                                               image_set_number=img_num)

                    ideal_comb.add_relate_measurement(modnum, relname, object_name1, object_name2,
                                                      group_indices, group_indices, obj_numbers,
                                                      obj_numbers, groupnum)
                    subsets = None
                    if img_num in img_nums_1:
                        subsets = [set1]
                    elif img_num in img_nums_2:
                        subsets = [set2]
                    else:
                        subsets = [set1, set2]
                    for subset in subsets:
                        subset.add_measurement(obj_name, feat_name, data,
                                               can_overwrite=False,
                                               image_set_number=img_num)

                        subset.add_relate_measurement(modnum, relname, object_name1, object_name2,
                                                      group_indices, group_indices, obj_numbers,
                                                      obj_numbers, groupnum)

        #Combine subsets and compare to overall measurements set
        set1.combine_measurements(set2)
        compare_measurements(ideal_comb, set1)

    def test_14_01_combine(self):
        """
        Test combining features of 2 different image sets,
        with sequential image numbers
        """
        img_nums_1 = xrange(1, 5)
        img_nums_2 = xrange(5, 8)
        self.tst_combine(img_nums_1, img_nums_2)

    def test_14_02_combine(self):
        """
        Combine measurements with non-sequential image numbers
        """
        img_nums_1 = [1, 4, 6, 9]
        img_nums_2 = [2, 3, 5, 7, 8]
        self.tst_combine(img_nums_1, img_nums_2)

    def test_14_03_combine(self):
        """
        Combine measurements image numbers
        that do not form a continuous integer sequence
        """
        img_nums_1 = [1, 4, 6, 9]
        img_nums_2 = [3, 7, 8]
        self.tst_combine(img_nums_1, img_nums_2)


def compare_measurements(ideal_meas_input, act_meas_input, check_feature=lambda s: True):
    """
    Compare 2 Measurement objects, assert all fields the same.

    Parameters
    -----------
    ideal_meas: Measurements, or string path to it
    act_meas: Measurements, or string path to it
    check_feature : callable, optional
    should take 1 argument, the feature name. Return true to check between
    objects, False to ignore. Default checks all.
    """

    ideal_meas = ideal_meas_input
    act_meas = act_meas_input
    if(isinstance(ideal_meas, str)):
        ideal_meas = cpmeas.load_measurements(ideal_meas)
    if(isinstance(act_meas, str)):
        act_meas = cpmeas.load_measurements(act_meas)
    excs = []

    obj_names = ideal_meas.get_object_names()
    image_numbers = ideal_meas.get_image_numbers()
    np.testing.assert_equal(sorted(image_numbers), sorted(act_meas.get_image_numbers()))
    for obj_name in obj_names:
        feature_names = ideal_meas.get_feature_names(obj_name)
        act_feat_names = act_meas.get_feature_names(obj_name)
        #np.testing.assert_equal(sorted(feature_names), sorted(act_feat_names),
                                #msg='Different number of feature names')

        for feat_name in feature_names:
            if(not check_feature(feat_name)):
                continue
            for img_num in image_numbers:
                ideal_dat = ideal_meas.get_measurement(obj_name, feat_name, img_num)
                pot_err_msg = 'Data at %s.%s num %d not equal' % \
                                        (obj_name, feat_name, img_num)
                act_dat = act_meas.get_measurement(obj_name, feat_name, img_num)
                try:
                    is_float = type(act_dat) in FLOAT_TYPES
                    if is_float:
                        np.testing.assert_(type(ideal_dat) == type(act_dat),'Actual data is type %s, expected float' % type(act_dat))
                        np.testing.assert_almost_equal(act_dat, ideal_dat,
                                    decimal=4, err_msg=pot_err_msg, verbose=True)
                        continue

                    np.testing.assert_equal(act_dat, ideal_dat,
                                        err_msg=pot_err_msg, verbose=True)
                except AssertionError, exc:
                    excs.append(exc)

    groups = ideal_meas.get_relationship_groups()
    keys = ['group_index1', 'group_index2', 'object_number1', 'object_number2']
    for group in groups:
        ideal_temp = act_meas.get_relationships(
                                group.module_number, group.relationship, group.object_name1,
                                group.object_name2, group.group_number)
        try:
            act_temp = act_meas.get_relationships(
                                group.module_number, group.relationship, group.object_name1,
                                group.object_name2, group.group_number)
            for key in keys:
                try:
                    act_data = act_temp[key]
                except ValueError:
                    raise AssertionError('%s not found in measurement under test' % key)
                np.testing.assert_equal(ideal_temp[key], act_data, 'group relationship %s not equal' % key)

        except AssertionError, exc:
            excs.append(exc)

    if(len(excs) > 0):
        print excs
        raise excs[-1]

if __name__ == "__main__":
    #sep_comb_suite = unittest.TestSuite()
    #sep_comb_suite.addTest(TestMeasurements('test_14_01_combine'))
    #unittest.TextTestRunner(verbosity=2).run(sep_comb_suite)
    unittest.main()
