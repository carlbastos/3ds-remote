#!/bin/sh
# Downloads the CIA tooling into tools/ (not versioned):
#   makerom 0.19.0 (Project_CTR, prebuilt) and bannertool 1.2.3 (carstene1ns fork, built from source).
set -e
cd "$(dirname "$0")"

MAKEROM_VER=0.19.0
BANNERTOOL_VER=1.2.3

if [ ! -x makerom ]; then
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) platform=macos_arm64 ;;
    Darwin-*)     platform=macos_x86_64 ;;
    Linux-x86_64) platform=ubuntu_x86_64 ;;
    *) echo "no prebuilt makerom for $(uname -s)-$(uname -m)" >&2; exit 1 ;;
  esac
  echo "fetching makerom $MAKEROM_VER ($platform)..."
  curl -sSL -o makerom.zip \
    "https://github.com/3DSGuy/Project_CTR/releases/download/makerom-v$MAKEROM_VER/makerom-v$MAKEROM_VER-$platform.zip"
  unzip -o -q makerom.zip makerom && rm makerom.zip && chmod +x makerom
fi

if [ ! -x bannertool ]; then
  if [ ! -d bannertool-src ]; then
    echo "fetching bannertool $BANNERTOOL_VER source..."
    curl -sSL "https://github.com/carstene1ns/3ds-bannertool/releases/download/$BANNERTOOL_VER/bannertool-$BANNERTOOL_VER.tar.gz" | tar xz
    mv "bannertool-$BANNERTOOL_VER" bannertool-src
    # clang rejects an initialized VLA; the padding is at most 3 bytes
    sed -i.orig 's/u8 pad\[padLength\] = {0};/u8 pad[4] = {0};/' bannertool-src/source/3ds/lz11.cpp
  fi
  echo "building bannertool..."
  c++ -std=c++17 -O2 -w -Ibannertool-src/source -Ibannertool-src/source/pc \
    -DVERSION="\"$BANNERTOOL_VER\"" -DSTBI_ONLY_PNG -DSTBI_NO_LINEAR -DSTBI_NO_STDIO \
    -DSTB_VORBIS_NO_PUSHDATA_API -DSTB_VORBIS_NO_STDIO -DDR_WAV_NO_STDIO \
    bannertool-src/source/*.cpp bannertool-src/source/3ds/*.cpp bannertool-src/source/pc/*.cpp \
    -o bannertool
fi
