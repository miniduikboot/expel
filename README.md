# EXiled Plugin-development Environment Launcher

EXPEL is a set of scripts that is designed to make developing plugins for EXILED easier. It creates an reproducable environment that is pre-setup to compile EXILED plugins.

## Features

- Compile EXILED from scratch
- Compile your plugins
- Start a server with your plugin

## System Requirements

Your system needs to have the following:

- Bash (for the run script)
- Docker 19.03 or newer (for BuildKit support)
- Around 5GB of storage (I'm working on reducing this)

With respect to operating systems:

- Linux is supported
- macOS may work, but haven't tried
- Windows probably doesn't work

## How to install

1. Clone this repository with Git Submodules enabled and enter it:
   `git clone --recursive https://github.com/miniduikboot/expel; `
2. Run `./build.sh` to build the container. This may take a while, depending on your internet speed as it needs to download quite a lot of stuff.
3. Run `expel.sh` in your plugin source code directory

Currently `expel.sh` supports the following commands:

- `restore` installs NuGet dependencies
- `build` builds a release version of your plugin
- `run` starts an EXILED server

## FAQ

### Can I use existing plugin projects with EXPEL?

Yes, it should be possible to build an existing plugin with EXPEL. It works best

All EXILED-related references are supplied to the plugin by EXPEL: it is recommended to include EXILED and its dependencies (YamlDotNet, Harmony) as a Reference instead of a PackageReference. If you have dependencies next to them, feel free to declare them using PackageReference.

EXPEL assumes that the `bin` and `obj` (for final and intermediate dependencies respectively) are stored in the root of the plugin directory and not renamed.

### Where are my build results stored?

They are in .expel/build-bin/Release
