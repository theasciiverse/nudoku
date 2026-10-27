# Changes from upstream

This is the Asciiverse packaging of [nudoku](https://github.com/jubalh/nudoku)
by Michael Vetter (jubalh) and contributors, an ncurses sudoku,
GPL-3.0-or-later (the sources: "either version 3 of the License, or (at
your option) any later version"; LICENSE is the GPL 3). Upstream is the
`upstream` remote; the `asciiverse` branch starts from its newest
release, 8.0.1 (`96638ad`, 2026-07-08), which is also the head of
`master`.

What is built: the game with its nine translations (de, es, fr, ja, ka,
ru, tr, uk, vi). Not built: the optional cairo export of puzzles to PDF
and PNG (`-p`, `-i`, `-n`, `-S`; `src/outp.c`), which upstream also
leaves off by default; those options print that nudoku was compiled
without cairo.

## Debian

Debian packages nudoku (2.1.0-0.2). Its packaging repo
(salsa.debian.org/debian/nudoku) is the `debian` remote, fetched without
its tags. Its one patch, `fix-build-fail-with-ncurses-6.3.patch`, is
upstream's own `93899a0` and has been in upstream since 2021.

## Code

- **Translations found beside the program** (`src/main.c`). The message
  catalogs were looked for only in the locale folder fixed at build
  time. A `locale` folder beside the running program, found through
  `/proc/self/exe` (so av's symbolic link still works), is used first.
- **Saving works in a fresh home folder.** The game is saved to
  `$XDG_STATE_HOME/nudoku` (`~/.local/state/nudoku`), but only the last
  folder was created, so where `~/.local/state` did not exist yet G
  answered "Can't save the game!". Missing parents are created. An empty
  or relative `XDG_STATE_HOME` counts as unset, as the XDG spec says (an
  empty one pointed the save at `/nudoku/`), and a missing `HOME` no
  longer passes a null path to `fopen()` and `unlink()`. On Windows the
  save is in `%LOCALAPPDATA%\nudoku`.
- **Centred, also after a resize.** The board, the help beside it and
  the status line were drawn from the top left corner. The 75x24 layout
  is centred, and on a resize the windows are made again for the new
  size and the board drawn back as it was. The help window is 21 lines,
  the lines it uses, instead of 25, so the layout fits 80x24.
- **No heap overflow in a terminal too small for the layout.** r (and a
  resize) called `redrawwin()` on windows that no longer fit after the
  terminal shrank, and ncurses then wrote outside its line buffers
  (heap-buffer-overflow in `wredrawln`, found with ASan; upstream 8.0.1
  does the same). r now makes the windows again as a resize does, and
  while the terminal is smaller than 75x24 the game says how big it
  needs to be and waits (Q or Escape quits).
- **Windows.** `<curses.h>` (PDCurses) instead of `<ncurses.h>`; with the
  save folder changes, nudoku builds with MinGW.

## Packaging (new files)

- `asciiverse/build.sh`: no autotools; the three sources in one compiler
  run against wide ncurses (PDCurses on Windows), the version taken from
  `configure.ac`, and with `NLS=1` the translations compiled by `msgfmt`
  into `out/locale`. `NLS=0` (macOS, Windows, whose C libraries have no
  gettext) builds the English-only game through upstream's own
  `gettext.h` fallback.
- `asciiverse/package.sh`: one archive per target with the binary, the
  translations, the man page, LICENSE, README.md and this file.
- `.github/workflows/release.yml`: static Linux in Alpine (x86_64,
  aarch64; musl's own gettext, so the translations work), macOS (x86_64,
  arm64) and Windows x86_64 (MinGW and PDCurses 3.9), plus SHA256SUMS,
  on a tag. Upstream's `linux.yml` and `macos.yml` stay; they run only on
  `master`.
- `asciiverse/record-preview.py`: records `asciiverse/nudoku.cast`; a
  driver reads the givens from the screen, solves the puzzle and types
  the answers, twice.
- `.gitignore`: the build folders.

## Tested

Linux: native (glibc, ncursesw 6.6) and static (Alpine 3.22, musl)
builds; puzzles solved, checked (c), hints, marks, undo, save (G) in a
fresh home and resume (`-r`); `LANG=de_DE.UTF-8` shows the German help
in the static build, also run through a symbolic link; centred at
100x30, 120x40 and 80x24 and re-centred on resize; at 60x20 and 70x26 it
asks for 75x24 and carries on when the terminal grows. ASan and UBSan:
five 40-second runs of random keys (moves, digits, every command but Q)
with random resizes, no reports after the redraw fix (upstream's code
overflows on the same runs). Windows: cross-built with MinGW-w64 against
PDCurses 3.9 and run under Wine (moves, a hint, a save to
`%LOCALAPPDATA%\nudoku\state.save`, Q); Wine's console showed the box
lines as `?` and did not pass the resize on, so both are unchecked on
real Windows. macOS: not built here.

## Ours

- **How to play it, at the top of README.md.** A short note on installing and
  starting it with av, or from a release archive; the original text follows
  unchanged.
