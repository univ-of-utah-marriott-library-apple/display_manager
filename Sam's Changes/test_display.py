#!/usr/bin/python


import unittest
import display

# should get a list of all possible resolutions

class TestDisplayModeInitializationFailure(unittest.TestCase):
    '''Tests for DisplayMode initialization failures
    '''
    
    def test_init_fails_without_args(self):
        '''test initialization fails without arguments
        '''
        with self.assertRaises(TypeError):
            display.DisplayMode()

    def test_init_fails_with_invalid_mode(self):
        '''test initialization fails without mode object
        '''
        with self.assertRaises(display.DisplayError):
            display.DisplayMode(5)


class TestMainDisplayID(unittest.TestCase):
    '''Tests for getting mainDisplayID() need to run before other tests
    '''

    def test_main_display_id(self):
        '''test that mainDisplayID() doesn't fail
        '''
        id = display.mainDisplayID()

    def test_main_display_id_type(self):
        '''test that mainDisplayID() returns integer
        '''
        id = display.mainDisplayID()
        self.assertIsInstance(id, int)
    
    @unittest.skip("need to create scenario without main display")
    def test_main_display_id_failure(self):
        '''test that mainDisplayID() doesn't fail
        '''
        # need to figure out a way to test without displays
        with self.assertRaises(DisplayError):
            id = display.mainDisplayID()


# class TestDisplayModeString(unittest.TestCase):
#     
#     def test_

class TestDisplayInitializationFailure(unittest.TestCase):

    def test_invalid_init_string(self):
        '''Test that ValueError is raised with string parameter
        '''
        with self.assertRaises(ValueError):
            display.Display('string')

    def test_invalid_init_bad_id(self):
        '''Test that ValueError is raised with bad parameter
        '''
        raise TypeError()
        
    def test_invalid_init_empty(self):
        '''Test that TypeError is raised without parameters
        '''
        with self.assertRaises(TypeError):
            display.Display()


class TestDisplayInitialization(unittest.TestCase):
    
    def setUp(self):
        self.disp = display.Display.mainDisplay()
        self.assertIsInstance(self.disp, display.Display)

    def test_display_has_id(self):
        '''Test main display has id property
        '''
        self.assertIsNotNone(self.disp.id)

    def test_display_has_ratio(self):
        '''Test main display has ratio property
        '''
        self.assertIsNotNone(self.disp.ratio)

    def test_display_has_width(self):
        '''Test main display has width property
        '''
        self.assertIsNotNone(self.disp.width)

    def test_display_has_height(self):
        '''Test main display has height property
        '''
        self.assertIsNotNone(self.disp.height)

    
class TestDisplayMode(unittest.TestCase):
    '''various displayMode tests
    '''    

    def setUp(self):
        id = display.mainDisplayID()
        self.modes = display.allDisplayModes(id)
    
#     def test_display_mode_works_with_mode(self):
#         '''test that display modes works with modes from Quartz.CopyAllDisplayModes() 
#         '''
#         m = self.modes[0] # get first mode
#         display.DisplayMode(m)
            


if __name__ == '__main__':
    # TO-DO: loading tests in certain orders
    unittest.main(verbosity=1)

