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
from pathlib import Path, PureWindowsPath

required_python = [3, 6]

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
        - src: path relative to host prefix
        - dst: path in container
        - readonly: whether the directory should be mounted readonly
        """
        self.src = src
        self.dst = dst
        self.readonly = readonly

    def create_source_dir(self):
        """
        Create the source directory. This needs to be created before starting
        the container, otherwise Docker will error out
        """
        src = options["build_path"] / self.src

        if not src.resolve().is_dir():
            src.mkdir(parents=True)
            # HACK: the expel containers use a different user id which is
            # likely different that the local user id. We set the permissions
            # to 777 to make sure that the container can write to these dirs.
            src.chmod(0o777)

    def mount_arg(self) -> str:
        """
        Get the mount argument to put after a --mount flag
        """
        src = options["host_path"] / self.src
        result = f"type=bind,src={src},dst={self.dst}"
        if self.readonly:
            result += ",readonly"
        return result


def run_container(
    name: str, mounts: List[DockerBindMount], docker_args: List[str], args: List[str]
):
    """
    Run a docker container

    Arguments:
    - name: name of the docker container
    - mounts: list of bindmounts for the container
    - docker_args: arguments for the docker container
    - args: arguments to the command in the Docker container.
    """
    cmd: List[str] = ["docker"]
    if options["docker_host"] is not None:
        cmd += ["-H", options["docker_host"]]
    cmd += ["run", "-it", "--rm"]
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


def restore_mounts():
    """
    Mounts for restoring. This needs the obj folder of the project
    and the nuget cache dirs.
    """
    return [
        DockerBindMount(Path("."), "/home/build/plugin", True),
        DockerBindMount(expel_cache / "build-obj", "/home/build/obj"),
        DockerBindMount(expel_cache / "build-nuget", "/home/build/.nuget"),
        DockerBindMount(
            expel_cache / "build-nuget-cache", "/home/build/.local/share/NuGet/"
        ),
    ]


def build_mounts():
    """
    Mounts for building. This needs the bin and object dirs, as well as the
    nuget cache dirs
    """
    return restore_mounts() + [
        DockerBindMount(expel_cache / "build-bin", "/home/build/bin")
    ]


def run_mounts():
    """
    Mounts for running the server. This just needs a special dir to store the
    server config in
    """
    return [DockerBindMount(expel_cache / "server-config", "/home/run/.config")]


# TASK DEFINITION


def build():
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
            "{HintPathFromItem};{TargetFrameworkDirectory};{RawFileName};"
            '/home/build/Managed"',
            # Build the plugin in release mode by default
            "-p:Configuration=Release",
            # Move the obj and bin folders to outside of the main build
            "-p:BaseIntermediateOutputPath=/home/build/obj/",
            "-p:OutputPath=/home/build/bin/",
        ],
    )


def install():
    """
    Install the plugin to the local server
    """
    # We're making a bunch of assumptions to make this process simpler:
    # 1. Your .csproj file has the same name as your plugin
    # 2. The other .dll's are dependencies of your plugin
    # 3. There are no other .dll's in the bin folder

    work_dir = options["build_path"]
    plugins = {csproj.stem for csproj in Path(work_dir).glob("**/*.csproj")}

    build_dir = work_dir / expel_cache / "build-bin"
    plug_dir = work_dir / expel_cache / "server-config" / "EXILED" / "Plugins"
    deps_dir = plug_dir / "dependencies"

    if not build_dir.exists():
        print("ERROR: Build directory not found, please build your plugin first")
        exit(1)

    if not deps_dir.exists():
        print("Creating Plugins folder")
        deps_dir.mkdir(parents=True)

    for dll in build_dir.glob("*.dll"):
        if dll.stem in plugins:
            print(f"{dll} is a plugin")
            shutil.copy(dll, plug_dir)
        else:
            print(f"{dll} is a dependency")
            shutil.copy(dll, deps_dir)


def restore():
    """
    Install NuGet dependencies for the plugin
    """
    run_container(
        "expel-plugin-build",
        restore_mounts(),
        [],
        [
            "-t:restore",
            "-p:BaseIntermediateOutputPath=/home/build/obj/",
        ],
    )


def run():
    """
    Run an EXILED server to test your plugin
    """
    run_container("expel-server-run", run_mounts(), ["--publish", "7777:7777/udp"], [])


def doctor():
    """
    Print system information. Use this when creating a bug report
    """
    print(f"Running in container: {os.environ.get('EXPEL_INSIDE_CONTAINER')}")
    print(f"Python version: {sys.version}")
    if (
        sys.version_info.major != required_python[0]
        or sys.version_info.minor < required_python[1]
    ):
        print(
            "WARNING: expel requires Python "
            f"{required_python[0]}.{required_python[1]}. "
            "Please update your python installation."
        )
    print("Docker system info:")
    subprocess.run(["docker", "system", "info"])
    print("Docker images:")
    subprocess.run(["docker", "images", "expel-*"])
    print("Build env EXILED version:")
    subprocess.run(
        [
            "docker",
            "run",
            "--entrypoint",
            "ikdasm",
            "expel-plugin-build",
            "-assembly",
            "/home/build/Managed/Exiled.API.dll",
        ]
    )


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

# Global options of the program
# They are set in the main method, then read from elsewhere
# - `docker_host` is a string that is set if Docker uses a nondefault socket
# - `host_path` is the working directory on the host. This may be a pure path.
# - `build_path` is the working directory inside the current environment.
# When working with Docker sibling containers, the mount path is on the host
# filesystem. However when we create the directory we need a path inside the
# container, hence the need for host_path and build_path.
options = {}


def main():
    """
    Main method of this script
    """
    parser = argparse.ArgumentParser(
        description="EXILED Plugin-development Environment Launcher"
    )
    parser.add_argument("task", type=str, help="Run a specific task")

    parser.add_argument(
        "--docker-host",
        type=str,
        help="Let Docker use a different socket to connect to the daemon",
    )
    parser.add_argument(
        "--working-directory",
        type=str,
        default=".",
        help="Use a different directory than the current directory",
    )
    parser.add_argument(
        "--windows",
        action="store_true",
        help="Interpret host paths as Windows paths",
    )
    args = parser.parse_args()

    # When running inside a docker container on Windows we need to manipulate
    # the host path as a Windows path, otherwise we can use system native paths
    if args.windows:
        options["host_path"] = PureWindowsPath(args.working_directory)
    else:
        options["host_path"] = Path(args.working_directory).resolve()

    # If we're running inside a container, we need to create directories in a
    # different location
    # During container build we set an environment variable to see if we run
    # inside the docker container, check it here.
    if os.environ.get("EXPEL_INSIDE_CONTAINER") == "1":
        # Path is hardcoded in Dockerfile
        options["build_path"] = Path("/work/")
    else:
        options["build_path"] = options["host_path"]

    options["docker_host"] = args.docker_host

    for task in tasks:
        if args.task == task.__name__:
            task()
            sys.exit(0)
    print("Could not find a task with that name. Try one of the following:")
    list_tasks(False)


if __name__ == "__main__":
    main()
