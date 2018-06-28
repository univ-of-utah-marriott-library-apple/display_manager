Display Manager
===============

A command-line utility which can modify your Mac's display settings.

## Contents

* [Contact](#contact) - how to reach us
* [System Requirements](#system-requirements) - what you need
* [Install](#install) - instructions for installing Display Manager
* [Uninstall](#uninstall) - removal of Display Manager
* [Purpose](#purpose) - why does this script exist?
* [Usage](#help)
   * [Set](#set) - set the configuration
   * [Show](#show) - look at available configurations
   * [Mirroring](#mirroring) - configure mirroring
   * [Brightness](#brightness) - change brightness
   * [Rotate](#rotate) - change display orientation

## Contact

If you have any comments, questions, or other input, either [file an issue](../../issues) or [send us an email](mailto:mlib-its-mac-github@lists.utah.edu). Thanks!

## System Requirements

Display Manager is for Mac computers.

Display Manager depends uses the Apple-supplied Python 2.7 binary, which lives at `/usr/bin/python` and comes pre-configured with the PyObjC bindings. These bindings allow Python to access the Objective-C methods that do the actual manipulation of the display settings.

If you have replaced the setDefault `/usr/bin/python` binary (which you should never do, by the way), you should ensure that it has the PyObjC bindings set up correctly.

## Install

First, check that you meet all the requirements and have the prerequisites outlined in the [System Requirements](#system-requirements) section.

[Then download the latest installer for Display Manager here!](../../releases/)

Once the download has completed, double-click the `.dmg` file. This will open a window in Finder where you should see two packages (files ending in `.pkg`). Double click the one named "Display Manager [x.x.x].pkg" (where *x.x.x* represents the current version number). This will launch the installer, which will guide you through the installation process. (Follow the on-screen instructions to complete the installation.)

## Uninstall

To remove Display Manager from your system, download the .dmg and run the "Uninstall Display Manager [x.x.x]" package to uninstall it, where *x.x.x* represents the version number. The version is not relevant, as all of the Display Manager uninstallers will work on any version of Display Manager.

At the end it will say "Installation Successful" but don't believe it - this will only remove files.

## Purpose

Display Manager was designed as a replacement to the old SetDisplay.c program that administrators have been using for years. While SetDisplay still works and can do many things, we decided to port the project to Python for a few reasons:

* Greater compatibility
   * Python is not a compiled language, so any potential architecture changes in the future won't affect it
* Better readability
   * For those not well-versed in C-style languages, Python can be easier to read through (and modify, if necessary)
* More features
   * We support all the features of SetDisplay
   * Plans for additional features (AirPlay configuration, HDMI underscan settings, etc.)

## Usage

The Display Manager executable supports the following commands:

```
$ display_manager.py { help | set | show | mirroring | brightness | rotate }
```

The `help` option just prints out relevant information, and is interchangeable with `--help`. You can give any commands as an argument to `help` (e.g. `display_manager.py help mirroring`), and you can give `help` as an argument to any commands.

The other commands each have their own help instructions, which are detailed below.

### Set

The `set` command is used to change the current configuration on a display or across all displays. It does not ask for confirmation; be careful about what you put in here. Running desired settings through `show` beforehand is recommended.

| Subcommand | Purpose                                                                                      |
|------------|----------------------------------------------------------------------------------------------|
| `help`     | Prints the help instructions.                                                               |
| `closest`  | Set the display to the supported configuration that is closest to the user-supplied values.  |
| `highest`  | Set the display to the highest supported configuration settings.                             |
| `exact`    | Set the display to the specified values **if** they form a supported configuration.          |

| Option                            | Purpose                                                               |
|-----------------------------------|-----------------------------------------------------------------------|
| `-w width`, `--width width`       | Resolution width.                                                     |
| `-h height`, `--height height`    | Resolution height.                                                    |
| `-d depth`, `--depth depth`       | Color depth.                                                          |
| `-r refresh`, `--refresh refresh` | Refresh rate (in Hz).                                                 |
| `--display display`               | Only change settings for the display with identifier `display`.       |
| `--no-hidpi`                      | Don't use any HiDPI configuration settings.                           |
| `--only-hidpi`                    | Only use HiDPI-scaled configuration settings.                         |

#### Examples

* Set the main display to its highest supported configuration:
```
$ display_manager.py set highest
```

* Set the main display to an exact specification:

```
$ display_manager.py set exact -w 1024 -h 768 -d 32 -r 70
```

* Set the main display to the closest value to what you want:
```
$ display_manager.py set -w 1024 -h 768 -d 32 -r 70
```
or
```
$ display_manager.py set closest -w 1024 -h 768 -d 32 -r 70
```

* Set display `478176570` to use the highest HiDPI-scaled configuration:
```
$ display_manager.py set highest --display 478176570 --only-hidpi
```

### Show

Use the `show` command to learn more about the supported display configurations for your hardware.

| Subcommand    | Purpose                                                                                   |
|---------------|-------------------------------------------------------------------------------------------|
| `help`        | Prints the help instructions.                                                            |
| `all`         | Shows all available supported display configuration.                                      |
| `closest`     | Shows the closest supported configuration to the given values.                            |
| `highest`     | Shows the highest available supported display configuration.                              |
| `current`     | Shows the current display configuration.                                                  |
| `displays`    | Shows a list of all attached, configurable displays.                                      |

| Option                            | Purpose                                                               |
|-----------------------------------|-----------------------------------------------------------------------|
| `-w width`, `--width width`       | Resolution width.                                                     |
| `-h height`, `--height height`    | Resolution height.                                                    |
| `-d depth`, `--depth depth`       | Color depth.                                                          |
| `-r refresh`, `--refresh refresh` | Refresh rate (in Hz).                                                 |
| `--display display`               | Only show display modes for the display with identifier `display`.    |
| `--no-hidpi`                      | Don't use any HiDPI configuration settings.                           |
| `--only-hidpi`                    | Only use HiDPI-scaled configuration settings.                         |

#### Examples

* Show the main display's highest supported configuration:
```
$ display_manager.py show highest
resolution: 1600x1200; pixel depth: 32; refresh rate: 60.0; ratio: 1.33:1
```

* Show all connected displays and their identifiers:
```
$ display_manager.py show displays
Display: 478176570 (Main Display)
Display: 478176723
Display: 478173192
Display: 478160349
```

### Mirroring

The `mirroring` command is used to configure display mirroring.

| Subcommand | Purpose                                                                  |
|------------|--------------------------------------------------------------------------|
| `help`     | Prints the help instructions.                                           |
| `enable`   | Activate mirroring.                                                      |
| `disable`  | Deactivate mirroring.                                                    |

| Option                        | Purpose                                               |
|-------------------------------|-------------------------------------------------------|
| `--display display`           | Change mirroring settings *for* display `display`.    |
| `--mirror display`            | Set the display to become a mirror of `display`.      |

#### Examples

* Set display `478176723` to become a mirror of `478176570`:
```
$ display_manager.py mirroring enable --display 478176723 --mirror 478176570
```

* Stop mirroring:
```
$ display_manager.py mirroring disable
```

### Brightness

You can set the brightness on your display with the `brightness` command (assuming your display supports it).

| Subcommand    | Purpose                                               |
|---------------|-------------------------------------------------------|
| `help`        | Prints the help instructions.                        |
| `show`        | Show the current brightness setting(s).               |

| Option                | Purpose                                       |
|-----------------------|-----------------------------------------------|
| `--display display`   | Change the brightness on display `display`.   |

#### Examples

* Show the current brightness settings of all displays:
```
$ display_manager.py brightness show
```

* Set the brightness of the main display to its maximum brightness:
```
$ display_manager.py brightness set .4
```

* Set the brightness of display `478176723` to 40% of maximum brightness:
```
$ display_manager.py brightness set .4 --display 478176723
```

### Rotate

You can view and change your display's orientation with the `rotate` command.

| Subcommand    | Purpose                                               |
|---------------|-------------------------------------------------------|
| `help`        | Prints the help instructions.                        |
| `show`        | Show the current rotation setting(s).                 |
| `set [value]` | Set display orientation to [value] \(in degrees\).    |

| Option                | Purpose                                       |
|-----------------------|-----------------------------------------------|
| `--display display`   | Change the orientation of display `display`.  |

#### Examples

* Show the current orientation of all displays (in degrees):
```
$ display_manager.py rotate show
```

* Rotate the main display by 90 degrees (counter-clockwise):
```
$ display_manager.py rotate set 90
```

* Flip display `478176723` upside-down:
```
$ display_manager.py rotate set 180 --display 478176723
```

* Restore display `478176723` to default orientation:
```
$ display_manager.py rotate set 0 --display 478176723
```
