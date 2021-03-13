#!/bin/bash
set -euo pipefail
# This script copies the EXILED files into the proper place

# Directory with outputs of the build process
SOURCE_DIR=/home/build/EXILED/bin/Release
# Directory where we'll copy everything to
TARGET_DIR=/home/build/artifacts/EXILED

mkdir -p $TARGET_DIR/Plugins/dependencies

cp $SOURCE_DIR/Exiled.Loader.dll $TARGET_DIR
# NOTE Updater is removed to remove the auto-updating feature of EXILED
cp $SOURCE_DIR/Exiled.{CreditTags,CustomItems,Events,Permissions}.dll $TARGET_DIR/Plugins
cp $SOURCE_DIR/{0Harmony,Exiled.API,YamlDotNet}.dll $TARGET_DIR/Plugins/dependencies
