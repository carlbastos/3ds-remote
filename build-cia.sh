#!/bin/sh
# Builds 3ds-remote.3dsx and 3ds-remote.cia (title ID 000400000FE3D500), versioned from ./VERSION.
set -e
cd "$(dirname "$0")"
export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
export DEVKITARM="${DEVKITARM:-$DEVKITPRO/devkitARM}"
export PATH="$DEVKITPRO/tools/bin:$DEVKITARM/bin:$PATH"

tools/fetch-tools.sh

VERSION=$(cat VERSION)
MAJOR=$(echo "$VERSION" | cut -d. -f1)
MINOR=$(echo "$VERSION" | cut -d. -f2)
MICRO=$(echo "$VERSION" | cut -d. -f3)

make clean >/dev/null
make
mkdir -p build
tools/bannertool makebanner -i meta/banner.png -a meta/audio.wav -o build/banner.bnr
tools/bannertool makesmdh -s "3DS Remote" -l "HTTP control server" -p "ulfr" -i meta/icon.png -o build/icon.icn
tools/makerom -f cia -o 3ds-remote.cia -elf 3ds-remote.elf -rsf meta/app.rsf \
  -icon build/icon.icn -banner build/banner.bnr -target t -exefslogo \
  -major "$MAJOR" -minor "$MINOR" -micro "$MICRO"
echo "built 3ds-remote.cia v$VERSION"
