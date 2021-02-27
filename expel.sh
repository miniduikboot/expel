#!/usr/bin/env bash
set -euo pipefail

# Start EXPEL inside a docker container and forward arguments to there

# /!\ Note for contributors: If you make changes here, keep expel.cmd in sync please.

exec docker run -it --rm \
    --mount type=bind,src="$(pwd)",dst=/work \
    --mount type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
    expel-launcher \
    --working-directory="$(pwd)" \
    "$@"
