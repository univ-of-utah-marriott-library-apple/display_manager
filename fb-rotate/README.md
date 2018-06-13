
Display Rotation for the Mac: fb-rotate
=======================================

A Unix utility able to rotate the display on any Mac, including the internal display on Apple notebooks, and able to switch the primary display, the one with the menu bar, back and forth between displays.

WARNING!
========

On Recent Macbooks running Sierra and El Capitan:

After a 90 or 270 degree rotation, the dislay fails, the computer and applications are still running, keyboard works, but the display is black. After a reset and restart, the screen is turned and fb-rotate continues to work for everything (including the -i and -l options in my tests), but the 90 and 270 rotations again cause the display to fail.

The 180 degree rotation works fine.

This utility depends on a private Apple API. We have had a ten year run. It was bound to stop working eventually. I will keep playing, but I'm not hopeful.

WARNING!
========

Compiling fb-rotate
-------------------

Assuming you have Xcode installed, you can compile the C-code yourself on any Mac OS from 10.3 to 10.11. 

In the Terminal app, after you've changed the current directory to the one `fb-rotate.c` is stored, using

     cd <path to the directory>

then,

     gcc -w -o fb-rotate fb-rotate.c -framework IOKit -framework ApplicationServices

will compile the utility.


Use of fb-rotate
----------------

The l-option (list):

     fb-rotate -l

will list the display id's, e.g. in Terminal,
 
     $ ./fb-rotate -l
     Display ID       Resolution
     0x19156030       1280x800                  [main display]
     0x76405c2d       1344x1008 

The i-option (info):

     fb-rotate -i

will list the display id's with other information, e.g.

     $ ./fb-rotate -i
     #  Display_ID  Resolution  ____Display_Bounds____  Rotation    
     0  0x19156030  1280x800       0     0  1280   800      0    [main][internal]
     1  0x76405c2d  1344x1008   1280     0  2624  1008      0    
     Mouse Cursor Position:  (   528 ,   409 )

(Unlike the file: `com.apple.windowserver.plist`, fb-rotate's information is always accurate and current.)

The d (display) and r (rotate) options :

     fb-rotate -d 0 -r 180

will rotate the main display 180 degrees, e.g.

     $ ./fb-rotate -d 0 -r 180
     $ ./fb-rotate -i
     #  Display_ID  Resolution  ____Display_Bounds____  Rotation
     0  0x19156030  1280x800       0     0  1280   800    180    [main][internal]
     1  0x76405c2d  1344x1008   1280     0  2624  1008      0    
     Mouse Cursor Position:  (  1047 ,   359 )

(You can rotate to the 0, 90 and 270 degree orientations as well.)

Also,

     fb-rotate -d <display ID> -r 0

will rotate the display with the indicated ID back to the standard orientation, e.g.

     $ ./fb-rotate -d 0x19156030 -r 0
     $ ./fb-rotate -i
     #  Display_ID  Resolution  ____Display_Bounds____  Rotation
     0  0x19156030  1280x800       0     0  1280   800      0    [main][internal]
     1  0x76405c2d  1344x1008   1280     0  2624  1008      0    
     Mouse Cursor Position:  (   226 ,   103 )

(Again, you can also rotate to the 90, 180 and 270 degree orientations.)

Further, there are shortcuts: 

When using the `-d` option,

- `-1` is a short cut for the `<display ID>` of the internal monitor,
- `0`  is a short cut for the `<display ID>` of the main monitor,
- `1`  is a short cut for the `<display ID>` of the first non-internal monitor.

When using the `-r` option,

- `-r 1` toggles between the 0 and 90 degree orientations.


Finally, the m-option (main):

     fb-rotate -d <display ID> -m

will set the display with the indicated ID to be the primary (main) display that has the menu bar, e.g.

     $ ./fb-rotate -d 0x76405c2d -m
     $ ./fb-rotate -i
     #  Display_ID  Resolution  ____Display_Bounds____  Rotation
     1  0x76405c2d  1344x1008      0     0  1344  1008      0    [main]
     0  0x19156030  1280x800   -1280     0     0   800      0    [internal]
     Mouse Cursor Position:  (  1122 ,   438 )



Downloads
---------

[A binary version of fb-rotate][fb-rotate] is available at Modbookish, a forum focused on the [Axiotron Modbook][Modbook].


Caveats
-------

Warning: Some white MacBooks (2006-2008), namely those using Intel's integrated graphics, have difficulty rotating to the 90º or 270º orientations and the resulting display may be difficult to use. 


Credits and License 
-------------------

The original code for fb-rotate comes from a programming example in
the book **Mac OS X Internals: A Systems Approach** by Amit Singh (© 2006). The source is made available under the GNU General Public License (GPL). For more information, see the book's associated web site: [http://osxbook.com][osxbook]

Changes were made by [Eric Nitardy][ericn] (© 2010) which have to be made available under the same license.

[osxbook]: http://osxbook.com
[ericn]: http://cdlbb.github.com
[fb-rotate]: http://modbookish.lefora.com/topic/3513246/A-Unix-Utility-to-Change-the-Primary-Display-on-OSX/
[Modbook]: http://www.modbook.com


