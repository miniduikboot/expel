@ECHO OFF
REM Create containers and push them to the local registry
REM Run this every time after you updated your EXPEL repoman

REM /!\ Note for contributors: If you make changes here, keep build.sh in sync please

SETLOCAL ENABLEEXTENSIONS
SET "DOCKER_BUILDKIT=1"

docker build -t expel-server-run --target server-run .
docker build -t expel-plugin-build --target plugin-build .
docker build -t expel-launcher -f Dockerfile.launcher .
