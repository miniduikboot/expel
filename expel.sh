#!/bin/bash
set -euo pipefail

# Launcher script for Plugin Development Kit for Exiled
# Run this in the directory with your plugin source code.
#
# Before using this, make sure you have built the containers and tagged them in your local registry.
# The simplest way to do this is to run build.sh
pwd=$(pwd)

case $1 in
    "build")
        container=expel-plugin-build
        flags=(
            # Mount the source code read-only
            "--mount" "type=bind,src=$pwd,dst=/home/build/plugin,readonly"
            # EXPEL expects the output directories to be at the root level and as the source directory is readonly,
            "--mount" "type=bind,src=$pwd/.expel/build-bin,dst=/home/build/plugin/bin"
            "--mount" "type=bind,src=$pwd/.expel/build-obj,dst=/home/build/plugin/obj"
            # Mount the nuget cache
            "--mount" "type=bind,src=$pwd/.expel/build-nuget,dst=/home/build/.nuget"
            "--mount" "type=bind,src=$pwd/.expel/build-nuget-cache,dst=/home/build/.local/share/NuGet/"
        )
        args=(
            # Prepend the Managed dir to the default search path
            "-p:AssemblySearchPaths=\"/home/build/Managed;{CandidateAssemblyFiles};{HintPathFromItem};{TargetFrameworkDirectory};{RawFileName}\""
            # Build a release version
            "-p:Configuration=Release"
            # For debugging the build process uncomment the following:
            #"-v:diag" "-bl:LogFile=obj/log.binlog"
        )
        mkdir -p .expel/build-{bin,obj,nuget,nuget-cache}
        ;;
    # Install NuGet dependencies
    "restore")
        container=expel-plugin-build
        flags=(
            "--mount" "type=bind,src=$pwd,dst=/home/build/plugin,readonly"
            "--mount" "type=bind,src=$pwd/.expel/build-obj,dst=/home/build/plugin/obj"
            # These directories are used for NuGet's caching
            "--mount" "type=bind,src=$pwd/.expel/build-nuget,dst=/home/build/.nuget"
            "--mount" "type=bind,src=$pwd/.expel/build-nuget-cache,dst=/home/build/.local/share/NuGet/"
        )
        args=("-t:restore")
        mkdir -p .expel/build-{obj,nuget,nuget-cache}
        ;;
    "run")
        container=expel-server-run
        # Mount the server config, otherwise it gets thrown away at the end.
        flags=("--mount" "type=bind,src='$pwd'/.expel/server-config,dst=/home/run/.config")
        mkdir -p .expel/server-config
        ;;
    
esac

#exec docker run --entrypoint /bin/bash "${flags[@]:-}" -it $container
exec docker run "${flags[@]}" -it $container "${args[@]:-}"
