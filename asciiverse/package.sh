#!/bin/sh
# Packs the build into dist/nudoku-<target>.tar.gz (.zip for Windows) for
# av: the binary at the top, the translations in locale/ beside it (when
# built), the man page, LICENSE, README.md and PATCHES.md.
#
#   asciiverse/package.sh x86_64-unknown-linux-musl
set -eu
cd "$(dirname "$0")/.."
target="$1"
case "$target" in *windows*) exe=.exe ;; *) exe= ;; esac
stage=stage/nudoku
rm -rf "$stage" && mkdir -p "$stage" dist
cp -R out/. "$stage/"
cp LICENSE README.md PATCHES.md "$stage/"
if [ -n "$exe" ]; then
  (cd "$stage" && zip -qr "../../dist/nudoku-$target.zip" .)
else
  tar -czf "dist/nudoku-$target.tar.gz" -C "$stage" .
fi
ls dist
