# Architecture of EXPEL

EXPEL consists of three main parts:

- The containers that run the actual processes
- The launcher script that ties everything together
- The shellscripts that build and run the previous two parts

## The containers

- The `Dockerfile` is responsible for building the core containers, which download the game, build EXILED and then assemble a container for compiling plugins and another for running the server
- The scripts folder contains small bash scripts used while building the container. They are only ran inside the containers
- There is an optional mode to run expel inside a docker container. Building this is done using `Dockerfile.launcher`

There are buildscripts, `build.sh` and `build.cmd`, that builds the containers and tag them in the local repository.

## The launcher script

`expel.py` is the launcher script that can start the containers correctly. This is a python script because it became too complex for a bash script.
Python was picked because it is a scripting language (so end users can easily edit it if needed), has quite a big install base (most Linux distro's ship Python in the base install) and contains many useful modules in the standard library.

It is possible to run EXPEL inside a container using the shellscripts `expel.sh` and `expel.cmd`.

While installing third party dependencies is technically possible, this dramatically increases setup complexity. For this reason expel.py only depends on the standard library of Python.
