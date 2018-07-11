Display Manager
===============

An open-source Python library which can modify your Mac's display settings.
Includes a command-line utility and a few example apps.

## Contents

* [Contact](#contact) - how to reach us
* [System Requirements](#system-requirements) - what you need
* [Purpose](#purpose) - why does this library exist?
* [Get Started](#get-started) - how to get started with Display Manager
* [Overview](#overview) - what is included in this library?
 * [Library](#library)
 * [Command-Line API](#command-line-api)
 * [GUI](#gui)
* [Command-Line Usage](#command-line-usage) - how to use the command-line API
 * [Set](#set)
 * [Show](#show)
 * [Brightness](#brightness)
 * [Rotate](#rotate)
 * [Mirror](#mirror)
 * [Underscan](#underscan)
* [Usage Examples](#usage-examples) - potential use cases for Display Manager
 * [Library Examples](#library-examples)
 * [Command-Line Examples](#command-line-examples)
 * [System Administration Examples](#system-administration-examples)
* [Update History](#update-history)

## Contact

If you have any comments, questions, or concerns, feel free to [send us an email](mailto:mlib-its-mac-github@lists.utah.edu).

## System Requirements

Display Manager only runs on Mac computers. It depends on the Apple-supplied Python 2.7 binary, which lives at `/usr/bin/python` and comes pre-configured with the PyObjC bindings. These bindings allow Python to access the Objective-C methods that perform display manipulations.

If you have replaced the setDefault `/usr/bin/python` binary (which is not generally advised), you should ensure that it has the PyObjC bindings set up correctly.

## Purpose

Display Manager was designed as a replacement to the old SetDisplay.c program that administrators have been using for years. While SetDisplay still works and can do many things, we decided to port the project to Python for a few reasons:

* Greater compatibility
   * Python is not a compiled language, so any potential architecture changes in the future won't affect it
   
* Better readability
   * For those not well-versed in C-style languages, Python can be easier to read through (and modify, if necessary)

* More features
   * We support all the features of SetDisplay, as well as a few new features, including HDMI underscan settings, display rotation, etc.
   
## Get Started

First, check that you meet all the requirements and have the prerequisites outlined in the [System Requirements](#system-requirements) section.

*TODO: UPDATE WHEN INSTALLER, PACKAGE, ETC. ARE COMPLETE!!!*

Next, see [Overview](#overview) for an idea of what you can do with Display Manager.

## Overview

The Display Manager suite comes in 3 parts: the Display Manager library (DisplayManager.py), the command-line API (displayManager.py), and the GUI (gui.py).

### Library

The Display Manager library is based off the contents of DisplayManager.py, which contains the following:

The `Display` class is a virtual representation of a connected physical display. It allows one to check the status of various display parameters (e.g. brightness, resolution, rotation, etc.) and to configure such parameters.
The `DisplayMode` class is a simple representation of Quartz's Display Modes. DisplayModes can be sorted, converted to strings, and passed as parameters to various methods which configure the display.
The `Command` class is called whenever a request is is made of the DisplayManager library. It contains many parameters for display manipulation, and can be manually run as one sees fit.
The `CommandList` class is simply a container (for `command`s) that allows one to execute several commands at once.

`getMainDisplay` returns the primary `Display`; `getAllDisplays` returns a `Display` for each connected display; `getIOKit` allows one to manually access the IOKit functions and constants used in Display Manager (usage not recommended -- it's much simpler to go through `Command`s and `Display`s instead, if possible)

### Command-Line API

The command-line API, accessed via displayManager.py, allows you to manually set [display resolution, pixel depth, refresh rate](#set), [brightness](#brightness), [rotation](#rotate), [screen mirroring](#mirror), and [underscan](#underscan). See [command-line usage](#command-line-usage) below for more information.

### GUI

*TODO: ADD THIS SOON!*

## Command-Line Usage

The Display Manager command-line API supports the following commands:

```
$ displayManager.py { help | set | show | brightness | rotate | mirror | underscan }
```

The `help` option prints out relevant usage information (similar to this document). You can give any commands as an argument to `help` (e.g. `displayManager.py help mirror`), and you can give `help` as an argument to any commands. Each command has its own help information, which is detailed below:

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
$ displayManager.py set highest
```

* Set the main display to the closest value to what you want:
```
$ displayManager.py set -w 1024 -h 768 -d 32 -r 70
```
or
```
$ displayManager.py set closest -w 1024 -h 768 -d 32 -r 70
```

* Set the main display to an exact specification:
```
$ displayManager.py set exact -w 1024 -h 768 -p 32 -r 70
```

* Set display `478176570` to use the highest HiDPI-scaled configuration:
```
$ displayManager.py set highest -d 478176570 --only-hidpi
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
$ displayManager.py show highest
resolution: 1600x1200; pixel depth: 32; refresh rate: 60.0; ratio: 1.33:1
```

* Show all connected displays and their identifiers:
```
$ displayManager.py show displays
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
$ displayManager.py brightness show
```

* Set the brightness of the main display to its maximum brightness:
```
$ displayManager.py brightness set .4
```

* Set the brightness of display `478176723` to 40% of maximum brightness:
```
$ displayManager.py brightness set .4 -d 478176723
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
$ displayManager.py rotate show
```

* Rotate the main display by 90 degrees (counter-clockwise):
```
$ displayManager.py rotate set 90
```

* Flip display `478176723` upside-down:
```
$ displayManager.py rotate set 180 -d 478176723
```

* Restore display `478176723` to default orientation:
```
$ displayManager.py rotate set 0 -d 478176723
```

### Mirror

The `mirror` command is used to configure display mirroring.

| Subcommand | Purpose                                                                  |
|------------|--------------------------------------------------------------------------|
| `help`     | Prints the help instructions.                                            |
| `set`      | Activate mirroring.                                                    |
| `disable`  | Deactivate mirroring.                                                    |

| Option                        | Purpose                                               |
|-------------------------------|-------------------------------------------------------|
| `-d display`, `--display display`  | Change mirroring settings *for* display `display`.        |
| `-m display`, `--mirror display`   | Set the above display to become a mirror *of* `display`.  |

#### Examples

* Set display `478176723` to become a mirror of `478176570`:
```
$ displayManager.py mirror set -d 478176723 -m 478176570
```

* Stop mirroring:
```
$ displayManager.py mirror disable
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
$ displayManager.py underscan set 0
```

* Set display `478176723` to 42% underscan
```
$ displayManager.py underscan set .42 -d 478176723
```

## Usage Examples

Display Manager allows you to manipulate displays in a variety of ways. You can write your own scripts with the [Display Manager library](#library), manually configure displays through the [command-line API](#command-line-api), or access the functionality of the command-line API through the [GUI](#gui). A few potential use cases are outlined below:

### Library Examples

First, import the Display Manager library, like so:

```
from DisplayManager import *
```

Next, say you'd like to automatically set all the displays connected to your computer to their highest resolution. A simple script might look like this:

```
for display in getAllDisplays():
    display.setMode(display.highestMode())
```

Perhaps you'd like your main display to rotate to 90 degrees. The following would work:

```
display = getMainDisplay()
display.setRotate(90)
```

You can use any of the properties and methods of `Display` objects to configure their settings, which is exactly how the [command-line API](#command-line-api) works. You can also configure displays through `Command`s, like this:

```
command = Command("brightness", "set", brightness=.4)
command.run()
```

This would perform the same `Command` as entering the following into the command line:

```
$ displayManager.py brightness set .4
```

For more complex usage, initialize a `CommandList`, which runs several commands simultaneously in a non-interfering pattern. To do so, pass it `Commands` through the `.addCommand(command)` method. An example:

```
commandA = Command("underscan", "set", underscan=.4)
commandB = Command("rotate", "set", angle=180)
commandC = Command("brightness", "set", brightness=1)

commands = CommandList()
commands.append(commandA)
commands.append(commandB)
commands.append(commandC)
commands.run()
```

### Command-Line Examples

In some cases, it may be desirable to configure displays from the command line, whether manually or via a script. Say you'd like a script to automatically set a display to its highest available resolution. The following would do just that:

```
$ displayManager.py set highest
```

But, in many cases, you might want to call several such commands at the same time. Of course, you may write them out line-by-line, but this takes a little longer, and more importantly, running several commands in this way may lead to undesired interference between commands. As such, it is recommended that multiple commands be run like so:

```
$ displayManager.py "set -w 1920 -h 1080" "rotate set 90" "brightness set .5" ...
```

In this way, you may pass in as many commands as you like, and Display Manager will find a way to run them simultaneously without encountering configuration errors.

### System Administration Examples

#### Jamf

Suppose you'd like all computers in a particular [Jamf Pro](https://www.jamf.com/products/jamf-pro/) scope to default to their highest retina-friendly resolution at maximum brightness at login. You could create such a policy, and add a script containing the following to it:

```
displayManager.py "set highest --only-hidpi" "brightness set 1"
```

For more details about command-line usage, see [here](#command-line-usage); for examples, see [command-line examples](#command-line-examples).

#### Outset

Perhaps you're managing several wall-mounted monitors that are flipped upside-down, and you'd like them to automatically display right-side-up. You could save the following script to `/usr/local/outset/boot-every/flip.sh`:

```
displayManager.py rotate set 180
```

For more details about command-line usage, see [here](#command-line-usage); for examples, see [command-line examples](#command-line-examples).

## Update History

| Date | Version | Update |
|------------|-------|----------------------------------------------------------------|
| 2018-07-13 | 1.0.0 | First edition of full Display Manager. Created the DisplayManager library and the new command-line API, added the ability to run multiple commands at once, added a GUI, and added rotation and underscan features. |
| 2015-10-28 | 0.1.0 | Legacy iteration of Display Manager. Created command-line API. |
