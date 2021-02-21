#!/usr/bin/env bash
set -euo pipefail
# This script copies over EXILED's DLL's, then starts the server
# This is needed to populate the server run directory
cp -R ~/EXILED/* ~/.config/EXILED/

exec "$@"
