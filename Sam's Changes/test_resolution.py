
import unittest
import resolution

# should get a list of all possible resolutions

TEMPLATES = {
    'MacBookPro11,1': [
        '640x480', '720x450', '825x525', '840x524', '800x600',
        '1024x640', '1024x768', '1152x720', '1280x800', '1440x900',
        '1650x1050', '1680x1050', '2048x1280', '2560x1600'
    ],
}

class TestString(unittest.TestCase):
    '''test for making sure resolution strings appear correctly 
    '''    

    def test_string_format(self):
        '''Test resolution formats correctly
        '''
        r = resolution.Resolution(1440, 900)
        self.assertEqual('1440x900', str(r))

    def test_string_format2(self):
        '''Test resolution formats correctly
        '''
        r = resolution.Resolution(1680, 1050)
        self.assertEqual('1680x1050', str(r))


class TestFloat(unittest.TestCase):
    '''Tests for making sure aspect ratios work as expected
    '''

    def test_1440x900(self):
        '''Test that 1440x900 <==> 1.6
        '''
        r = resolution.Resolution(1440, 900)
        self.assertEqual(float(r), 1.6)

    def test_1680x1050(self):
        '''Test that 1680x1050 <==> 1.6
        '''
        r = resolution.Resolution(1680, 1050)
        self.assertEqual(float(r), 1.6)

    def test_1650x1050(self):
        '''Test that 1650x1050 <==> 1.57 (rounded to 2 decimal places)
        '''
        r = resolution.Resolution(1650, 1050)
        self.assertEqual(float(r), 1.57)


class TestRatio(unittest.TestCase):
    '''Tests that reduce resolutions into ratios
    '''
    def test_1440x900(self):
        '''Test that 1440x900 <==> 8:5
        '''
        r = resolution.Resolution(1440, 900)
        self.assertEqual(r.ratio, '8:5')

    def test_1680x1050(self):
        '''Test that 1680x1050 <==> 8:5
        '''
        r = resolution.Resolution(1680, 1050)
        self.assertEqual(r.ratio, '8:5')

    def test_1650x1050(self):
        '''1650:1050 <==> 11:7
        '''
        r = resolution.Resolution(1650, 1050)
        self.assertEqual(r.ratio, '11:7')

    def test_2560x1440(self):
        '''1650:1050 <==> 16:9
        '''
        r = resolution.Resolution(2560, 1440)
        self.assertEqual(r.ratio, '16:9')


class TestCompareRatio(unittest.TestCase):
    '''Tests that compare various resolution ratios
    '''
    def test_1440x900_vs_1680x1050(self):
        '''1440:900 == 1680:1050 <==> True
        '''
        r1 = resolution.Resolution(1440, 900)
        r2 = resolution.Resolution(1680, 1050)
        self.assertEqual(r1.ratio, r2.ratio)


class TestCompareSameHeight(unittest.TestCase):
    '''Test similar resolutions with same height
    '''
    
    def setUp(self):
        self.rS = resolution.Resolution(1650, 1050)
        self.rG = resolution.Resolution(1680, 1050)

    def test_is_equal_fails(self):
        '''1680x1050 == 1650x1050 <==> False
        '''
        self.assertFalse(self.rG == self.rS)

    def test_is_not_equal_succeeds(self):
        '''1680x1050 != 1650x1050 <==> True
        '''
        self.assertTrue(self.rG != self.rS)

    def test_is_greater_than_succeeds(self):
        '''1680x1050 > 1650x1050 <==> True
        '''
        self.assertTrue(self.rG > self.rS)

    def test_is_greater_than_fails(self):
        '''1650x1050 > 1680x1050 <==> False
        '''
        self.assertFalse(self.rS > self.rG)

    def test_is_less_than_succeeds(self):
        '''1650x1050 < 1680x1050 <==> True
        '''
        self.assertTrue(self.rS < self.rG)

    def test_is_less_than_fails(self):
        '''1680x1050 < 1650x1050 <==> False
        '''
        self.assertFalse(self.rG < self.rS)

    def test_is_greater_than_or_equal_succeeds(self):
        '''1680x1050 >= 1650x1050 <==> True
        '''
        self.assertTrue(self.rG >= self.rS)

    def test_is_greater_than_or_equal_fails(self):
        '''1650x1050 >= 1680x1050 <==> False
        '''
        self.assertFalse(self.rS >= self.rG)

    def test_is_less_than_or_equal_succeeds(self):
        '''1650x1050 <= 1680x1050 <==> True
        '''
        self.assertTrue(self.rS <= self.rG)

    def test_is_less_than_or_equal_fails(self):
        '''1680x1050 <= 1650x1050 <==> False
        '''
        self.assertFalse(self.rG <= self.rS)


class TestCompareSameWidth(unittest.TestCase):
    '''Test resolutions with same width
    '''
    
    def setUp(self):
        self.rS = resolution.Resolution(2560, 1440)
        self.rG = resolution.Resolution(2560, 1600)

    def test_is_not_equal_succeeds(self):
        '''2560x1600 != 2560x1440 <==> True
        '''
        self.assertTrue(self.rG != self.rS)

    def test_is_equal_fails(self):
        '''2560x1600 == 2560x1440 <==> False
        '''
        self.assertFalse(self.rG == self.rS)

    def test_is_greater_than_succeeds(self):
        '''2560x1600 > 2560x1440 <==> True
        '''
        self.assertTrue(self.rG > self.rS)

    def test_is_greater_than_fails(self):
        '''2560x1440 > 2560x1600 <==> False
        '''
        self.assertFalse(self.rS > self.rG)

    def test_is_less_than_succeeds(self):
        '''2560x1440 < 2560x1600 <==> True
        '''
        self.assertTrue(self.rS < self.rG)

    def test_is_less_than_fails(self):
        '''2560x1600 < 2560x1440 <==> False
        '''
        self.assertFalse(self.rG < self.rS)

    def test_is_greater_than_or_equal_succeeds(self):
        '''2560x1600 >= 2560x1440 <==> True
        '''
        self.assertTrue(self.rG >= self.rS)

    def test_is_greater_than_or_equal_fails(self):
        '''2560x1440 >= 2560x1600 <==> False
        '''
        self.assertFalse(self.rS >= self.rG)

    def test_is_less_than_or_equal_succeeds(self):
        '''2560x1440 <= 2560x1600 <==> True
        '''
        self.assertTrue(self.rS <= self.rG)

    def test_is_less_than_or_equal_fails(self):
        '''2560x1600 <= 2560x1440 <==> False
        '''
        self.assertFalse(self.rG <= self.rS)


class TestCompareSame(unittest.TestCase):
    '''Test resolutions with identical values
    '''    

    def setUp(self):
        '''Setup two seperate resolution objects with identical values
        '''
        self.r1 = resolution.Resolution(1440, 900)
        self.r2 = resolution.Resolution(1440, 900)
        # make sure instances are separate from each other
        self.assertIsNot(self.r1, self.r2)
        
    def test_is_equal_succeeds(self):
        '''1440x900 == 1440x900 <==> True
        '''
        self.assertEqual(self.r1, self.r2)

    def test_is_not_equal_fails(self):
        '''1440x900 != 1440x900 <==> False
        '''
        self.assertFalse(self.r1 != self.r2)

    def test_is_greater_than_fails(self):
        '''1440x900 > 1440x900 <==> False
        '''
        self.assertFalse(self.r1 > self.r2)

    def test_is_less_than_fails(self):
        '''1440x900 < 1440x900 <==> False
        '''
        self.assertFalse(self.r1 < self.r2)

    def test_is_greater_than_or_equal_fails(self):
        '''1440x900 >= 1440x900 <==> True
        '''
        self.assertTrue(self.r1 >= self.r2)

    def test_is_less_than_or_equal_succeeds(self):
        '''1440x900 <= 1440x900 <==> True
        '''
        self.assertTrue(self.r1 <= self.r2)

#     @unittest.skip("not implemented")
#     def test_compare_same_resolution_hidpi(self):
#         '''Test hidpi and non-hidpi resolutions compare equally
#         '''
#         self.assertEqual(self.r1, self.r2)


class TestCompareDifferent(unittest.TestCase):
    '''Test resolutions with different values
    '''    

    def setUp(self):
        '''Compare 5120x2880 to 1920x1080
        '''
        self.rS = resolution.Resolution(1920, 1080)
        self.rG = resolution.Resolution(5120, 2880)
        
    def test_is_equal_fails(self):
        '''5120x2880 == 1920x1080 <==> False
        '''
        self.assertFalse(self.rG == self.rS)

    def test_is_not_equal_succeeds(self):
        '''5120x2880 != 1920x1080 <==> True
        '''
        self.assertTrue(self.rS != self.rG)

    def test_is_greater_than_succeeds(self):
        '''5120x2880 > 1920x1080 <==> True
        '''
        self.assertTrue(self.rG > self.rS)

    def test_is_greater_than_fails(self):
        '''1920x1080 > 5120x2880 <==> False
        '''
        self.assertFalse(self.rS > self.rG)

    def test_is_less_than_succeeds(self):
        '''1920x1080 < 5120x2880 <==> True
        '''
        self.assertTrue(self.rS < self.rG)

    def test_is_less_than_fails(self):
        '''5120x2880 < 1920x1080 <==> False
        '''
        self.assertFalse(self.rG < self.rS)

    def test_is_greater_than_or_equal_succeeds(self):
        '''5120x2880 >= 1920x1080 <==> True
        '''
        self.assertTrue(self.rG >= self.rS)

    def test_is_greater_than_or_equal_fails(self):
        '''1920x1080 >= 5120x2880 <==> False
        '''
        self.assertFalse(self.rS >= self.rG)

    def test_is_less_than_or_equal_succeeds(self):
        '''1920x1080 <= 5120x2880 <==> True
        '''
        self.assertTrue(self.rS <= self.rG)

    def test_is_less_than_or_equal_fails(self):
        '''5120x2880 <= 1920x1080 <==> False
        '''
        self.assertFalse(self.rG <= self.rS)


class TestFromString(unittest.TestCase):
    '''Test that fromString('1440x900') == Resolution(1440, 900)
    '''

    def setUp(self):
        self.r1 = resolution.fromString('1440x900')
        self.r2 = resolution.Resolution(1440, 900)
        
    def test_is_equal(self):
        '''Test resolutions are equal
        '''
        self.assertTrue(self.r1 == self.r2)

    def test_ratio(self):
        '''Test resolutions ratios are equal
        '''
        self.assertTrue(self.r1.ratio == self.r2.ratio)

    def test_circular_conversion(self):
        '''test resolution to string to resolution works
        '''
        s = str(self.r1)
        r = resolution.fromString(s)
        self.assertIsNot(self.r1, r)
        self.assertEqual(self.r1, r)
        
        
if __name__ == '__main__':
    unittest.main(verbosity=1)

