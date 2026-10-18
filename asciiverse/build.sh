#!/bin/sh
# Builds nudoku into out/ without autotools: the three sources in one
# compiler run (one process, so no parallel jobs to limit), and with
# NLS=1 the translations compiled by msgfmt into out/locale, where the
# game looks for them beside itself. The cairo PDF/PNG export (-p, -i)
# is not built. The compiler, flags and curses library come from the
# environment, so one script serves every target (see
# .github/workflows/release.yml):
#
#   asciiverse/build.sh                                        # Linux
#   LDFLAGS="-static -s" asciiverse/build.sh                   # Alpine, static
#   NLS=0 LIBS=-lncurses CFLAGS="-O2 -arch arm64" \
#     LDFLAGS="-arch arm64" asciiverse/build.sh                # macOS
#   CC=x86_64-w64-mingw32-gcc NLS=0 CFLAGS="-O2 -I$PDC" \
#     LIBS="$PDC/wincon/pdcurses.a" LDFLAGS="-static -s" EXE=.exe \
#     asciiverse/build.sh                                      # Windows
#
# NLS=0 leaves gettext out (macOS and Windows have none in their C
# libraries), so the game is in English only there.
set -eu
cd "$(dirname "$0")/.."
CC="${CC:-cc}"
CFLAGS="${CFLAGS:--O2}"
LDFLAGS="${LDFLAGS:-}"
LIBS="${LIBS:--lncursesw}"
NLS="${NLS:-1}"
EXE="${EXE:-}"
VERSION=$(sed -n 's/^AC_INIT(\[nudoku\], \[\([^]]*\)\].*/\1/p' configure.ac)
mkdir -p out
rm -rf out/*
# shellcheck disable=SC2086
nice -n 10 $CC $CFLAGS -DVERSION="\"$VERSION\"" -DPACKAGE='"nudoku"' -DENABLE_NLS="$NLS" \
  -DLOCALEDIR='"/usr/share/locale"' -o "out/nudoku$EXE" \
  src/main.c src/sudoku.c src/utils.c $LDFLAGS $LIBS
if [ "$NLS" = 1 ]; then
  for lang in $(cat po/LINGUAS); do
    mkdir -p "out/locale/$lang/LC_MESSAGES"
    msgfmt -o "out/locale/$lang/LC_MESSAGES/nudoku.mo" "po/$lang.po"
  done
fi
cp man/nudoku.6 out/
echo "built nudoku$EXE $VERSION"
