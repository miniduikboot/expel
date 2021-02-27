# EXiled Plugin-development Environment Launcher

<p align="center">
<a href="https://github.com/miniduikboot/expel/blob/master/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/miniduikboot/expel"></a>
<a href="https://github.com/miniduikboot/expel/actions/"><img alt="Lint status" src="https://github.com/miniduikboot/expel/actions/workflows/black.yml/badge.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

EXPEL is a set of scripts that is designed to make developing plugins for EXILED easier. It creates an reproducable environment that is pre-setup to compile EXILED plugins.

## Features

- Compile EXILED from scratch
- Compile your plugins
- Start a server with your plugin

## System Requirements

Your system needs to have the following:

- Docker 19.03 or newer (for BuildKit support)
- Python 3.6 or newer (only if you're using system Python)
- Around 5GB of storage (I'm working on reducing this)

With respect to operating systems, we have a table that lists how you can best run the program:

| Operating System | Running using system Python | Running inside Docker<sup>1</sup> |
| ---------------- | --------------------------- | --------------------------------- |
| Linux            | ✓                           | ✓                                 |
| Windows          | ✓                           | ⚠<sup>2</sup>                     |

1: Running with system Python is usually 35% faster per operation compared to running inside Docker, but requires you to install Python on your system.

2: For this to work, you need to enable the option "Expose daemon on tcp://localhost:2375 without TLS" in the Docker Desktop configuration panel. Please note the security consequences this has: every process or container on your system can start additional containers. We're open to more secure solutions

## How to install

1. Clone this repository with Git Submodules enabled and enter it:
   `git clone --recursive https://github.com/miniduikboot/expel; `
2. Run the buildscript (on Linux this is `./build.sh`, on Windows this is `./build.cmd`) to build the container. This may take a few minutes as it needs to download quite a lot of stuff, including a copy of the game.
3. To update EXPEL, pull the repository using `git pull`, then run the buildscript again.

There are a few ways to run EXPEL:

- You can run EXPEL using your system python, for this add `expel.py` to your PATH, then run it from the folder containing your .csproj file.
- You can run EXPEL inside a container, for this `expel.sh` to your PATH, then run it from the folder containing your .csproj file.

## Usage

Currently EXPEL supports the following commands in the rough order you want to run them:

- `restore` installs NuGet dependencies
- `build` builds a release version of your plugin
- `install` copies your plugin to the local server
- `run` starts an EXILED server with your plugin

## FAQ

### Can I use existing plugin projects with EXPEL?

Yes, it should be possible to build an existing plugin with EXPEL without major conversions.

All EXILED-related references are supplied to the plugin by EXPEL: it is recommended to include EXILED and its dependencies (YamlDotNet, Harmony) as a Reference instead of a PackageReference. If you have dependencies next to them, feel free to declare them using PackageReference. Currently EXPEL only provides a single version of EXILED, so we strongly recommend against pinning your version of EXILED.

EXPEL assumes that the `bin` and `obj` (for final and intermediate dependencies respectively) are stored in the root of the plugin directory and not renamed.

### Where are my build results stored?

They are in `.expel/build-bin/Release`

### Where is my server configuration?

They are in `.expel/server-config`. Note that the EXILED dll's in there will be overwritten on each server run: if you want to change the version of EXILED, rebuild the container.

### Can I port EXPEL to a different mod framework/game?

Go right ahead: EXPEL is licensed under MIT, which allows you to modify and distribute this project. A note that your project was based on EXPEL would be much appreciated though.

As EXILED is licensed under CC-BY-SA 2.5, which is a copyleft license, the combined program is effectively licensed under CC-BY-SA 2.5, not MIT.
However, if you remove EXILED and include a different framework, it is possible to use the remaining code under MIT.

### I'm having issues with EXPEL that are not covered by this FAQ

Contact miniduikboot#2965 in the EXILED Discord. Please take some time to formulate your problem and include the following:

1. What are you trying to do?
2. What did you expect to happen and what is happening instead?
3. If you got an error message, attach it as well.
4. Attach the output of `expel doctor` to your request. If you aren't able to get EXPEL running, please add which OS you are using and your docker version.
