#!/usr/bin/env bash
set -euo pipefail

# Create containers and push them to the local registry

export DOCKER_BUILDKIT=1
# As plugin-build is just copying files and server-run actually installs things, create server-run first to save time.
for target in server-run plugin-build
do
    docker build -t expel-$target --target $target . 
done

# The launcher is in a seperate file because it is completely independent of the other stages
docker build -t expel-launcher -f Dockerfile.launcher .
