#!/bin/bash -e

# Disables the fix for diameter estimation.
#
# This should be done before running non-diameter estimation algs.

source $(dirname "${BASH_SOURCE[0]}")/../common/get-dirs.sh

cd "$GPS_DIR"/src/java/gps/messages/storage
cp -f ArrayBackedIncomingMessageStorage.javaORIGINAL ArrayBackedIncomingMessageStorage.java

$(dirname "${BASH_SOURCE[0]}")/recompile-gps.sh

