Display Manager
===============

An open-source Python library which can modify your Mac's display settings.
Includes a command-line utility and a few example apps.

## Contents

* [Contact](#contact) - how to reach us
* [System Requirements](#system-requirements) - what you need
* [Install](#install) - instructions for installing Display Manager
* [Uninstall](#uninstall) - removal of Display Manager
* [Purpose](#purpose) - why does this library exist?
* [Library](#library) - what can you do with this library?
   * [Examples](#examples) - potential use cases for this library
* [Command-Line Usage](#help) - how to use the command line interface
   * [Set](#set) - set the configuration
   * [Show](#show) - look at available configurations
   * [Mirror](#mirror) - configure mirroring
   * [Brightness](#brightness) - change brightness
   * [Rotate](#rotate) - change display orientation

## Contact

If you have any comments, questions, or other input, either [file an issue](../../issues) or [send us an email](mailto:mlib-its-mac-github@lists.utah.edu). Thanks!

## System Requirements

Display Manager is for Mac computers.

Display Manager depends uses the Apple-supplied Python 2.7 binary, which lives at `/usr/bin/python` and comes pre-configured with the PyObjC bindings. These bindings allow Python to access the Objective-C methods that do the actual manipulation of the display settings.

If you have replaced the setDefault `/usr/bin/python` binary (which is not generally advised), you should ensure that it has the PyObjC bindings set up correctly.

## Install

First, check that you meet all the requirements and have the prerequisites outlined in the [System Requirements](#system-requirements) section.

[Then download the latest installer for Display Manager here!](../../releases/)

Once the download has completed, double-click the `.dmg` file. This will open a window in Finder where you should see two packages (files ending in `.pkg`). Double click the one named "Display Manager [x.x.x].pkg" (where *x.x.x* represents the current version number). This will launch the installer, which will guide you through the installation process. (Follow the on-screen instructions to complete the installation.)

## Uninstall

To remove Display Manager from your system, download the .dmg and run the "Uninstall Display Manager [x.x.x]" package to uninstall it.

## Purpose

Display Manager was designed as a replacement to the old SetDisplay.c program that administrators have been using for years. While SetDisplay still works and can do many things, we decided to port the project to Python for a few reasons:

* Greater compatibility
   * Python is not a compiled language, so any potential architecture changes in the future won't affect it
* Better readability
   * For those not well-versed in C-style languages, Python can be easier to read through (and modify, if necessary)
* More features
   * We support all the features of SetDisplay, as well as a few new features, including HDMI underscan settings, display rotation, etc.

## Library

The Display Manager library is based off the contents of DisplayManager.py, which contains the following:

The `Display` class is a virtual representation of a connected physical display. It allows one to check the status of various display parameters (e.g. brightness, resolution, rotation, etc.) and to configure such parameters.
The `DisplayMode` class is a simple representation of Quartz's Display Modes. DisplayModes can be sorted, converted to strings, and passed as parameters to various methods which configure the display.
The `Command` class is called whenever a request is is made of the DisplayManager library. It contains many parameters for display manipulation, and can be manually run as one sees fit.
The `CommandList` class is simply a container (for `command`s) that allows one to execute several commands at once.

`getMainDisplay` returns the primary `Display`; `getAllDisplays` returns a `Display` for each connected display; `getIOKit` allows one to manually access the IOKit functions and constants used in Display Manager (usage not recommended -- it's much simpler to go through `Command`s and `Display`s instead, if possible)

### Examples

Say you'd like to automatically set all the displays connected to your computer to their highest resolution. A simple script might look like this:

```
for display in getAllDisplays():
    display.setMode(display.highestMode())
```

Perhaps you'd like all the displays of the computers you manage to rotate to 90 degrees. The following would work:

```
display = Display(getMainDisplayID())
display.setRotate(90)
```

For System Admins using software like [Jamf](https://www.jamf.com/products/jamf-pro/) or [Outset](https://github.com/chilcote/outset), the ability to configure a startup script that automatically configures any number of Macs to certain display settings at boot or login may be quite useful.

## Usage

The Display Manager command-line interface supports the following commands:

```
$ commandLine.py { help | set | show | brightness | rotate | mirror | underscan }
```

The `help` option just prints out relevant information, and is interchangeable with `--help`. You can give any commands as an argument to `help` (e.g. `commandLine.py help mirror`), and you can give `help` as an argument to any commands.

The other commands each have their own help instructions, which are detailed below.

### Set

The `set` command is used to change the current configuration on a display or across all displays. It does not ask for confirmation; be careful about what you put in here. Running desired settings through `show` beforehand is recommended.

| Subcommand | Purpose                                                                                      |
|------------|----------------------------------------------------------------------------------------------|
| `help`     | Prints the help instructions.                                                                |
| `closest`  | Set the display to the supported configuration that is closest to the user-supplied values.  |
| `highest`  | Set the display to the highest supported configuration settings.                             |
| `exact`    | Set the display to the specified values **if** they form a supported configuration.          |

| Option                            | Purpose                                                               |
|-----------------------------------|-----------------------------------------------------------------------|
| `-w width`, `--width width`       | Resolution width.                                                     |
| `-h height`, `--height height`    | Resolution height.                                                    |
| `-p depth`, `--pixel-depth depth` | Pixel color depth (default: 32).                                      |
| `-r refresh`, `--refresh refresh` | Refresh rate (in Hz) (default: 0).                                    |
| `'d display', '--display display` | Only change settings for the display with identifier `display`.       |
| `--no-hidpi`                      | Don't use any HiDPI configuration settings.                           |
| `--only-hidpi`                    | Only use HiDPI-scaled configuration settings.                         |

#### Examples

* Set the main display to its highest supported configuration:
```
$ commandLine.py set highest
```

* Set the main display to the closest value to what you want:
```
$ commandLine.py set -w 1024 -h 768 -d 32 -r 70
```
or
```
$ commandLine.py set closest -w 1024 -h 768 -d 32 -r 70
```

* Set the main display to an exact specification:
```
$ commandLine.py set exact -w 1024 -h 768 -p 32 -r 70
```

* Set display `478176570` to use the highest HiDPI-scaled configuration:
```
$ commandLine.py set highest -d 478176570 --only-hidpi
```

### Show

Use the `show` command to learn more about the supported display configurations for your hardware.

| Subcommand    | Purpose                                                                                   |
|---------------|-------------------------------------------------------------------------------------------|
| `help`        | Prints the help instructions.                                                             |
| `all`         | Shows all available supported display configuration.                                      |
| `closest`     | Shows the closest supported configuration to the given values.                            |
| `highest`     | Shows the highest available supported display configuration.                              |
| `current`     | Shows the current display configuration.                                                  |
| `displays`    | Shows a list of all attached, configurable displays.                                      |

| Option                            | Purpose                                                               |
|-----------------------------------|-----------------------------------------------------------------------|
| `-w width`, `--width width`       | Resolution width.                                                     |
| `-h height`, `--height height`    | Resolution height.                                                    |
| `-p depth`, `--pixel-depth depth` | Pixel color depth (default: 32).                                      |
| `-r refresh`, `--refresh refresh` | Refresh rate (in Hz) (default: 0).                                    |
| `'d display', '--display display` | Only change settings for the display with identifier `display`.       |
| `--no-hidpi`                      | Don't use any HiDPI configuration settings.                           |
| `--only-hidpi`                    | Only use HiDPI-scaled configuration settings.                         |

#### Examples

* Show the current display's highest supported configuration:
```
$ commandLine.py show highest
resolution: 1600x1200; pixel depth: 32; refresh rate: 60.0; ratio: 1.33:1
```

* Show all connected displays and their identifiers:
```
$ commandLine.py show displays
Display: 478176570 (Main Display)
Display: 478176723
Display: 478173192
Display: 478160349
```

### Brightness

You can set the brightness on your display with the `brightness` command (assuming your display supports it).

| Subcommand    | Purpose                                               |
|---------------|-------------------------------------------------------|
| `help`        | Prints the help instructions.                         |
| `show`        | Show the current brightness setting(s).               |

| Option                | Purpose                                       |
|-----------------------|-----------------------------------------------|
| `-d [display]`, `--display [display]`  | Change the brightness on display `display`.   |

#### Examples

* Show the brightness settings of all displays:
```
$ commandLine.py brightness show
```

* Set the brightness of the main display to its maximum brightness:
```
$ commandLine.py brightness set .4
```

* Set the brightness of display `478176723` to 40% of maximum brightness:
```
$ commandLine.py brightness set .4 -d 478176723
```

### Rotate

You can view and change your display's orientation with the `rotate` command.

| Subcommand    | Purpose                                               |
|---------------|-------------------------------------------------------|
| `help`        | Prints the help instructions.                         |
| `show`        | Show the current rotation setting(s).                 |
| `set [value]` | Set display orientation to [value] \(in degrees\).    |

| Option                | Purpose                                       |
|-----------------------|-----------------------------------------------|
| `--display [display]`   | Change the orientation of `display`.        |

#### Examples

* Show the current orientation of all displays (in degrees):
```
$ commandLine.py rotate show
```

* Rotate the main display by 90 degrees (counter-clockwise):
```
$ commandLine.py rotate set 90
```

* Flip display `478176723` upside-down:
```
$ commandLine.py rotate set 180 -d 478176723
```

* Restore display `478176723` to default orientation:
```
$ commandLine.py rotate set 0 -d 478176723
```

### Mirror

The `mirror` command is used to configure display mirroring.

| Subcommand | Purpose                                                                  |
|------------|--------------------------------------------------------------------------|
| `help`     | Prints the help instructions.                                            |
| `enable`   | Activate mirroring.                                                      |
| `disable`  | Deactivate mirroring.                                                    |

| Option                        | Purpose                                               |
|-------------------------------|-------------------------------------------------------|
| `-d display`, `--display display`  | Change mirroring settings *for* display `display`.        |
| `-m display`, `--mirror display`   | Set the above display to become a mirror *of* `display`.  |

#### Examples

* Set display `478176723` to become a mirror of `478176570`:
```
$ commandLine.py mirror enable -d 478176723 -m 478176570
```

* Stop mirroring:
```
$ commandLine.py mirror disable
```

### Underscan

The `underscan` command can configure display underscan settings.

| Subcommand    | Purpose                                               |
|---------------|-------------------------------------------------------|
| `help`        | Prints the help instructions.                         |
| `show`        | Show the current underscan setting(s).                |
| `set [value]` | Set display underscan to [value] between 0 and 1.     |

| Option                | Purpose                                       |
|-----------------------|-----------------------------------------------|
| `--display [display]`   | Change the orientation of `display`.        |

#### Examples

* Set main display to 0% underscan
```
$ commandLine.py underscan set 0
```

* Set display `478176723` to 42% underscan
```
$ commandLine.py underscan set .42 -d 478176723
```
