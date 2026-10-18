#!/usr/bin/env python3
"""Records asciiverse/nudoku.cast, the catalog preview, at 100x30
(hub/RECORDING.md): an easy puzzle solved by a driver that reads the
givens from the screen, solves the puzzle itself, turns on the marks
(m, which light up every copy of the number under the cursor) and types
the answers cell by cell with the h, j, k, l keys, then checks with c
("Solved"); then a new puzzle (N) the same way, and Q to quit.

nudoku runs from out/ (asciiverse/build.sh) by name, so the cast's header
holds no local path, with a throwaway HOME, so nothing touches your own
saved game.

Needs asciinema 3.x and pyte. Usage, from the repo root:
  uv run --with pyte python3 asciiverse/record-preview.py
Any extra argument is used as the cast's path instead (for test runs);
with --dry-run it plays without recording."""
import fcntl, os, pty, select, shutil, struct, sys, tempfile, termios, time
import pyte

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if a != "--dry-run"]
dry = "--dry-run" in sys.argv
cast = args[0] if args else f"{root}/asciiverse/nudoku.cast"
COLS, ROWS = 100, 30

work = tempfile.mkdtemp(prefix="nudoku-preview-")
env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8",
           HOME=work, PATH=f"{root}/out:{os.environ['PATH']}")
for v in ("VTE_VERSION", "TERM_PROGRAM", "TERM_PROGRAM_VERSION", "TMUX", "XDG_STATE_HOME"):
    env.pop(v, None)

pid, fd = pty.fork()
if pid == 0:
    os.chdir(work)
    if dry:
        os.execvpe("nudoku", ["nudoku"], env)
    os.execvpe("asciinema", ["asciinema", "rec", "--overwrite", "-q", "--idle-time-limit", "2",
        "--window-size", f"{COLS}x{ROWS}", "--capture-env", "TERM,COLORTERM,LANG",
        "--title", "nudoku", "--command", "nudoku", cast], env)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
screen = pyte.Screen(COLS, ROWS)
stream = pyte.ByteStream(screen)
start = time.time()


def pump(seconds):
    end = time.time() + seconds
    while True:
        left = end - time.time()
        r, _, _ = select.select([fd], [], [], max(0.0, min(0.02, left)))
        if r:
            try:
                stream.feed(os.read(fd, 65536))
            except OSError:
                return False
        if left <= 0:
            return True


def key(k, wait=0.12):
    os.write(fd, k)
    pump(wait)


def read_puzzle():
    """The 81 cells (0 for empty) and the screen position of the first: the
    grid's top left corner is the first box corner on the screen (ncurses
    draws it from the VT100 line set, which pyte keeps as 'l'), each
    cell four columns wide and two lines high."""
    for y, line in enumerate(screen.display):
        for corner in ("lqqqw", "┌───┬"):
            x = line.find(corner)
            if x >= 0:
                cells = []
                for r in range(9):
                    for c in range(9):
                        ch = screen.display[y + 1 + 2 * r][x + 2 + 4 * c]
                        cells.append(int(ch) if ch.isdigit() else 0)
                return cells
    return None


def solve(cells):
    """Plain backtracking, most constrained cell first."""
    def options(i):
        r, c = divmod(i, 9)
        used = {cells[r * 9 + k] for k in range(9)} | {cells[k * 9 + c] for k in range(9)}
        br, bc = r - r % 3, c - c % 3
        used |= {cells[(br + a) * 9 + bc + b] for a in range(3) for b in range(3)}
        return [n for n in range(1, 10) if n not in used]
    empty = [i for i in range(81) if cells[i] == 0]
    if not empty:
        return True
    i = min(empty, key=lambda j: len(options(j)))
    for n in options(i):
        cells[i] = n
        if solve(cells):
            return True
    cells[i] = 0
    return False


def play():
    """Solves the puzzle on the screen, starting with the cursor top left;
    returns the number of cells filled and whether c said Solved."""
    puzzle = read_puzzle()
    answer = list(puzzle)
    assert solve(answer), "no solution read from the screen"
    r = c = 0
    for i in range(81):
        if puzzle[i]:
            continue
        tr, tc = divmod(i, 9)
        while r < tr:
            key(b"j", 0.05)
            r += 1
        while c < tc:
            key(b"l", 0.05)
            c += 1
        while c > tc:
            key(b"h", 0.05)
            c -= 1
        pump(0.12)
        key(str(answer[i]).encode(), 0.3)
    pump(0.6)
    key(b"c", 2.5)         # check: Solved
    solved = any("Solved" in line for line in screen.display)
    # back to the top left corner for the next puzzle
    for _ in range(r):
        key(b"k", 0.03)
    for _ in range(c):
        key(b"h", 0.03)
    return puzzle.count(0), solved


pump(1.5)
key(b"m", 0.8)             # marks on
first = play()
key(b"N", 1.5)             # a new puzzle
key(b"m", 0.5)             # N turns the marks off; on again
second = play()
key(b"Q", 0.5)
end = time.time() + 5
while time.time() < end:
    if not pump(0.1):
        break
    done, _ = os.waitpid(pid, os.WNOHANG)
    if done:
        break
else:
    os.kill(pid, 9)
try:
    os.waitpid(pid, 0)
except ChildProcessError:
    pass
shutil.rmtree(work, ignore_errors=True)
print(f"{cast}: {time.time() - start:.0f} s, (cells filled, solved): {first} {second}", file=sys.stderr)
