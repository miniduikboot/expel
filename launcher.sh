#!/usr/bin/env bash
set -euo pipefail

exec docker run -it --rm \
    --mount type=bind,src="$(pwd)",dst=/work \
    --mount type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
    expel-launcher \
    --working-directory="$(pwd)" \
    "$@"
