#!/usr/bin/env python3
"""
EXILED Plugin-development Environment Launcher

This script launches containers for EXPEL to help the user build containers.
"""

# NOTE: All these elements import something from Python's standard library
# Please contact the project maintainers BEFORE importing a third-party library
import argparse
import subprocess
import sys

from typing import List
from pathlib import Path


# DOCKER WRAPPER


class DockerBindMount:
    """
    Create a Bind Mount in the docker container.

    Bind mounts are folders from the host that are replicated inside the
    container. Changes will be written back immediately on the host.
    """

    def __init__(self, src: Path, dst: str, readonly: bool = False):
        """
        Create a bind mount

        Arguments:
        - src: host path
        - dst: path in container
        """
        self.src = src.resolve()
        self.dst = dst
        self.readonly = readonly

    def create_source_dir(self):
        """
        Create the source directory. This needs to be created in advance, otherwise Docker will error out
        """
        if not self.src.is_dir():
            self.src.mkdir(parents=True)

    def mount_arg(self) -> str:
        """
        Get the mount argument to put after a --mount flag
        """
        result = f"type=bind,src={self.src},dst={self.dst}"
        if self.readonly:
            result += ",readonly"
        return result


def run_container(name: str, mounts: List[DockerBindMount], args: List[str]):
    """
    Run a docker container

    Arguments:
    - name: name of the docker container
    - mounts: list of bindmounts for the container
    - args: arguments to the command in the Docker container.
    """
    cmd: List[str] = ["docker", "run", "-it"]
    for mount in mounts:
        mount.create_source_dir()
        cmd.append("--mount")
        cmd.append(mount.mount_arg())
    cmd.append(name)
    cmd += args
    subprocess.run(cmd, check=True)


# TASK DEFINITION

expel_cache = Path.cwd() / ".expel"


restore_mounts = [
    DockerBindMount(Path.cwd(), "/home/build/plugin", True),
    DockerBindMount(expel_cache / "build-obj", "/home/build/plugin/obj"),
    DockerBindMount(expel_cache / "build-nuget", "/home/build/.nuget"),
    DockerBindMount(
        expel_cache / "build-nuget-cache", "/home/build/.local/share/NuGet/"
    ),
]

build_mounts = restore_mounts + [
    DockerBindMount(expel_cache / "build-bin", "/home/build/plugin/bin")
]

run_mounts = [DockerBindMount(expel_cache / "server-config", "/home/run/.config")]


def build():
    """
    Build the plugin
    """
    run_container(
        "expel-plugin-build",
        build_mounts,
        [
            # TODO minimalize this list. The first item are the SL reference,
            # one of the others is needed for NuGet
            '-p:AssemblySearchPaths="/home/build/Managed;{CandidateAssemblyFiles};{HintPathFromItem};{TargetFrameworkDirectory};{RawFileName}"'
            "-p:Configuration=Release"
        ],
    )


def install():
    """
    Install the plugin to the local server
    """
    raise NotImplementedError("sorry")


def restore():
    """
    Install NuGet dependencies for the plugin
    """
    run_container(
        "expel-plugin-build",
        restore_mounts,
        ["-t:restore"],
    )


def run():
    """
    Run an EXILED server to test your plugin
    """
    run_container("expel-server-run", run_mounts, [])


def list_tasks(print_header=True):
    """
    List all commands and a short descriptions of them
    """
    if print_header:
        print("EXPEL Tasks:")
    print()
    for task in tasks:
        print(f"{task.__name__}: {task.__doc__}")


tasks = [build, install, list_tasks, restore, run]


def main():
    """
    Main method of this script
    """
    parser = argparse.ArgumentParser(
        description="EXILED Plugin-development Environment Launcher"
    )
    parser.add_argument("task", type=str, help="Run a specific task")
    args = parser.parse_args()
    for task in tasks:
        if args.task == task.__name__:
            task()
            sys.exit(0)
    print("Could not find a task with that name. Try one of the following:")
    list_tasks(False)


if __name__ == "__main__":
    main()
