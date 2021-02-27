#!/usr/bin/env python3
"""
EXILED Plugin-development Environment Launcher

This script launches containers for EXPEL to help the user build containers.
"""

# NOTE: All these elements import something from Python's standard library
# Please contact the project maintainers BEFORE importing a third-party library
import argparse
import os
import shutil
import subprocess
import sys

from typing import List
from pathlib import Path

required_python = [3, 6]

# DOCKER WRAPPER

# When working with Docker sibling containers, the mount path is on the host
# filesystem. However when we create the directory we need a path inside the
# container.

# During container build we set an environment flag to see if we run inside a
# docker container, check it here
inside_container = os.environ.get('EXPEL_INSIDE_CONTAINER') == '1'


class DockerBindMount:
    """
    Create a Bind Mount in the docker container.

    Bind mounts are folders from the host that are replicated inside the
    container. Changes will be written back immediately on the host.
    """

    def __init__(self, host_dir: Path, src: Path, dst: str, readonly: bool = False):
        """
        Create a bind mount

        Arguments:
        - host_dir: working directory on host
        - src: path relative to host prefix
        - dst: path in container
        - readonly: whether the directory should be mounted readonly
        """
        self.host_dir = host_dir
        self.src = src
        self.dst = dst
        self.readonly = readonly

    def create_source_dir(self):
        """
        Create the source directory. This needs to be created before starting
        the container, otherwise Docker will error out
        """
        if inside_container:
            src = "/work" / self.src
        else:
            src = self.host_dir / self.src

        if not src.resolve().is_dir():
            self.src.mkdir(parents=True)

    def mount_arg(self) -> str:
        """
        Get the mount argument to put after a --mount flag
        """
        src = (self.host_dir / self.src).resolve()
        result = f"type=bind,src={src},dst={self.dst}"
        if self.readonly:
            result += ",readonly"
        return result


def run_container(name: str, mounts: List[DockerBindMount], docker_args: List[str], args: List[str]):
    """
    Run a docker container

    Arguments:
    - name: name of the docker container
    - mounts: list of bindmounts for the container
    - docker_args: arguments for the docker container
    - args: arguments to the command in the Docker container.
    """
    cmd: List[str] = ["docker", "run", "-it", "--rm"]
    for mount in mounts:
        mount.create_source_dir()
        cmd.append("--mount")
        cmd.append(mount.mount_arg())
    cmd += docker_args
    cmd.append(name)
    cmd += args
    subprocess.run(cmd, check=True)


# MOUNT DEFINITIONS
# These paths will be mounted by Docker when calling the various operations


expel_cache = Path(".expel")


def restore_mounts(workdir: Path):
    """
    Mounts for restoring. This needs the obj folder of the project
    and the nuget cache dirs.
    """
    return [
        DockerBindMount(workdir, Path("."), "/home/build/plugin", True),
        DockerBindMount(workdir, expel_cache / "build-obj",
                        "/home/build/plugin/obj"),
        DockerBindMount(workdir, expel_cache /
                        "build-nuget", "/home/build/.nuget"),
        DockerBindMount(workdir, expel_cache / "build-nuget-cache",
                        "/home/build/.local/share/NuGet/"),
    ]


def build_mounts(workdir: Path):
    """
    Mounts for building. This needs the bin and object dirs, as well as the
    nuget cache dirs
    """
    return restore_mounts(workdir) + [
        DockerBindMount(workdir, expel_cache / "build-bin",
                        "/home/build/plugin/bin")
    ]


def run_mounts(workdir: Path):
    """
    Mounts for running the server. This just needs a special dir to store the
    server config in
    """
    return [
        DockerBindMount(workdir, expel_cache /
                        "server-config", "/home/run/.config")
    ]


# TASK DEFINITION


def build(args):
    """
    Build the plugin
    """
    run_container(
        "expel-plugin-build",
        build_mounts(),
        [],
        [
            # Append the directy with EXILED's references to the back of the
            # default value of AssemblySearchPaths.
            #
            # If it'd be prepended instead MSBuild would copy over System.*.dll
            # files to the publish dir, which is not needed.
            '-p:AssemblySearchPaths="{CandidateAssemblyFiles};'
            '{HintPathFromItem};{TargetFrameworkDirectory};{RawFileName};'
            '/home/build/Managed"',

            # Build the plugin in release mode by default
            "-p:Configuration=Release"
        ],
    )


def install(args):
    """
    Install the plugin to the local server
    """
    # We're making a bunch of assumptions to make this process simpler:
    # 1. Your .csproj file has the same name as your plugin
    # 2. The other .dll's are dependencies of your plugin
    # 3. There are no other .dll's in the bin folder

    work_dir = args.working_directory
    if inside_container:
        work_dir = '/work'
    plugins = {csproj.stem for csproj in Path(work_dir).glob('**/*.csproj')}

    build_dir = work_dir / expel_cache / 'build-bin' / 'Release'
    plug_dir = work_dir / expel_cache / 'server-config' / 'EXILED' / 'Plugins'
    deps_dir = plug_dir / 'dependencies'
    for dll in build_dir.glob('*.dll'):
        if dll.stem in plugins:
            print(f"{dll} is a plugin")
            shutil.copy(dll, plug_dir)
        else:
            print(f"{dll} is a dependency")
            shutil.copy(dll, deps_dir)


def restore(args):
    """
    Install NuGet dependencies for the plugin
    """
    run_container(
        "expel-plugin-build",
        restore_mounts(args.working_directory),
        [],
        ["-t:restore"],
    )


def run(args):
    """
    Run an EXILED server to test your plugin
    """
    run_container("expel-server-run", run_mounts(args.working_directory),
                  ['--publish', '7777:7777/udp'], [])


def doctor(args):
    """
    Print system information. Use this when creating a bug report
    """
    print(f"Running in container: {inside_container}")
    print(f"Python version: {sys.version}")
    if (sys.version_info.major != required_python[0] or
            sys.version_info.minor < required_python[1]):
        print(
            "WARNING: expel requires Python "
            f"{required_python[0]}.{required_python[1]}. "
            "Please update your python installation.")
    print("Docker system info:")
    subprocess.run(["docker", "system", "info"])
    print("Docker images:")
    subprocess.run(["docker", "images", "expel-*"])
    print("Build env EXILED version:")
    subprocess.run(["docker", "run", "--entrypoint", "ikdasm", "expel-plugin-build",
                    "-assembly", "/home/build/Managed/Exiled.API.dll"])


def list_tasks(print_header=True):
    """
    List all commands and a short descriptions of them
    """
    if print_header:
        print("EXPEL Tasks:")
    print()
    for task in tasks:
        print(f"{task.__name__}: {task.__doc__}")


tasks = [build, doctor, install, list_tasks, restore, run]


def main():
    """
    Main method of this script
    """
    parser = argparse.ArgumentParser(
        description="EXILED Plugin-development Environment Launcher"
    )
    parser.add_argument("task", type=str, help="Run a specific task")

    parser.add_argument(
        "--working-directory",
        type=Path,
        default=Path.cwd(),
        help="Use a different directory than the current directory",
    )
    args = parser.parse_args()
    type(args)
    for task in tasks:
        if args.task == task.__name__:
            task(args)
            sys.exit(0)
    print("Could not find a task with that name. Try one of the following:")
    list_tasks(False)


if __name__ == "__main__":
    main()
