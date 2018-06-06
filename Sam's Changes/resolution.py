#!/usr/bin/python

from __future__ import print_function
 
import fractions


class Resolution(object):
    '''Simple class to represent a resolution
    '''

    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        self._ratio = None
    
    def __eq__(self, x):
        '''x.__eq__(y) <==> (x.width, x.height) == (y.width, y.height)
        '''
        return (self.width, self.height) == (x.width, x.height)

    def __ne__(self, x):
        '''x.__ne__(y) <==> (x.width, x.height) != (y.width, y.height)
        '''
        return (self.width, self.height) != (x.width, x.height)

    def __gt__(self, x):
        '''x.__gt__(y) <==> (x.width, x.height) > (y.width, y.height)
        '''
        return (self.width, self.height) > (x.width, x.height)

    def __lt__(self, x):
        '''x.__lt__(y) <==> (x.width, x.height) < (y.width, y.height)
        '''
        return (self.width, self.height) < (x.width, x.height)

    def __ge__(self, x):
        '''x.__ge__(y) <==> (x.width, x.height) >= (y.width, y.height)
        '''
        return (self.width, self.height) >= (x.width, x.height)

    def __le__(self, x):
        '''x.__le__(y) <==> (x.width, x.height) <= (y.width, y.height)
        '''
        return (self.width, self.height) <= (x.width, x.height)

    # Not sure which set of comparisons is more efficient, but they
    # both work the same
#     def __eq__(self, x):
#         '''x.__eq__(y) <==> (x.width * x.height) == (y.width * y.height)
#         '''
#         return (self.width * self.height) == (x.width * x.height)
# 
#     def __ne__(self, x):
#         '''x.__ne__(y) <==> (x.width * x.height) != (y.width * y.height)
#         '''
#         return (self.width * self.height) != (x.width * x.height)
# 
#     def __gt__(self, x):
#         '''x.__gt__(y) <==> (x.width * x.height) > (y.width * y.height)
#         '''
#         return (self.width * self.height) > (x.width * x.height)
# 
#     def __lt__(self, x):
#         '''x.__lt__(y) <==> (x.width * x.height) < (y.width * y.height)
#         '''
#         return (self.width * self.height) < (x.width * x.height)
# 
#     def __ge__(self, x):
#         '''x.__ge__(y) <==> (x.width * x.height) >= (y.width * y.height)
#         '''
#         return (self.width * self.height) >= (x.width * x.height)
# 
#     def __le__(self, x):
#         '''x.__le__(y) <==> (x.width, x.height) <= (y.width, y.height)
#         '''
#         return (self.width * self.height) <= (x.width * x.height)


    def __float__(self):
        '''x.__float__() <==> round(float(x.width)/x.height, 2)
        '''
        f = float(self.width)/self.height
        # Anything more than 2 decimal places seems like overkill
        return round(f, 2)

    def __str__(self):
        '''x.__str__() <==> "{0}x{1}".format(x.width, x.height)
        '''
        return "{0}x{1}".format(self.width, self.height)

    # Not sure if this is necesary
#     def __repr__(self):
#         '''x.__repr__() <==> Resolution(x.width, x.height)
#         '''
#         return 'Resolution({0}, {1})'.format(self.width, self.height)

    @property
    def ratio(self):
        '''Reduced form of resolution in ratio notation
        Resolution(5120, 2880).ratio <==> '16:9'
        '''
        if not self._ratio:
            f = fractions.Fraction(self.width, self.height)
            self._ratio = "{0}:{1}".format(f.numerator, f.denominator)
        return self._ratio

def fromString(r):
    '''Returns a resolution object from string (e.g. '1440x900')
    '''
    w, h = r.split('x')
    return Resolution(w, h)

       
if __name__ == '__main__':
    pass
