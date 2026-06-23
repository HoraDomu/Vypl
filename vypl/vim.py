"""Vim modal editing for Vypl."""

import re
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .curtsiesfrontend.repl import BaseRepl


class VimMode(Enum):
    INSERT = auto()
    NORMAL = auto()
    COMMAND = auto()


def _is_word(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _forward_word(line: str, col: int) -> int:
    n = len(line)
    i = col
    if i < n and _is_word(line[i]):
        while i < n and _is_word(line[i]):
            i += 1
    elif i < n and not line[i].isspace():
        while i < n and not line[i].isspace() and not _is_word(line[i]):
            i += 1
    while i < n and line[i].isspace():
        i += 1
    return min(i, n)


def _back_word(line: str, col: int) -> int:
    i = col - 1
    if i < 0:
        return 0
    while i > 0 and line[i].isspace():
        i -= 1
    if _is_word(line[i]):
        while i > 0 and _is_word(line[i - 1]):
            i -= 1
    else:
        while i > 0 and not line[i - 1].isspace() and not _is_word(line[i - 1]):
            i -= 1
    return i


def _end_word(line: str, col: int) -> int:
    n = len(line)
    i = col + 1
    while i < n and line[i].isspace():
        i += 1
    if i < n and _is_word(line[i]):
        while i + 1 < n and _is_word(line[i + 1]):
            i += 1
    elif i < n and not line[i].isspace():
        while i + 1 < n and not line[i + 1].isspace() and not _is_word(line[i + 1]):
            i += 1
    return min(i, max(0, n - 1))


def _word_at(line: str, col: int) -> str | None:
    for m in re.finditer(r"\w+", line):
        if m.start() <= col <= m.end():
            return m.group()
    return None


class VimBuffer:
    """Cursor-tracked view over all lines of the current multi-line block."""

    def __init__(self, lines: list[str], row: int, col: int) -> None:
        self.lines = list(lines)
        self.row = row
        self.col = min(col, max(0, len(lines[row]) - 1)) if lines[row] else 0

    def _clamp(self) -> None:
        limit = max(0, len(self.lines[self.row]) - 1)
        self.col = min(self.col, limit)

    def up(self) -> bool:
        if self.row > 0:
            self.row -= 1
            self._clamp()
            return True
        return False

    def down(self) -> bool:
        if self.row < len(self.lines) - 1:
            self.row += 1
            self._clamp()
            return True
        return False

    def first(self) -> None:
        self.row = 0
        self.col = 0

    def last(self) -> None:
        self.row = len(self.lines) - 1
        self._clamp()

    @property
    def current(self) -> str:
        return self.lines[self.row]

    @current.setter
    def current(self, val: str) -> None:
        self.lines[self.row] = val

    def delete_row(self) -> None:
        if len(self.lines) > 1:
            del self.lines[self.row]
            self.row = min(self.row, len(self.lines) - 1)
            self._clamp()
        else:
            self.lines[0] = ""
            self.col = 0


class VimState:
    def __init__(self) -> None:
        self.mode: VimMode = VimMode.INSERT
        self.registers: dict[str, str] = {'"': ""}
        self._pending_reg: str = '"'
        self._awaiting_reg: bool = False
        self._pending_g: bool = False
        self.pending_op: str | None = None
        self.cmd: str = ""
        self.count: str = ""
        self.vbuf: VimBuffer | None = None

    def _store(self, text: str) -> None:
        self.registers[self._pending_reg] = text
        self._pending_reg = '"'

    def _load(self) -> str:
        return self.registers.get(self._pending_reg, "")

    def enter_normal(self, repl: "BaseRepl") -> None:
        self.mode = VimMode.NORMAL
        self.pending_op = None
        self._pending_g = False
        repl._cursor_offset = max(0, repl._cursor_offset - 1)
        repl.incr_search_mode = repl.incr_search_mode.__class__.NO_SEARCH
        if repl.buffer:
            lines = list(repl.buffer) + [repl._current_line]
            self.vbuf = VimBuffer(lines, len(lines) - 1, repl._cursor_offset)
        else:
            self.vbuf = None
        repl.status_bar.message("-- NORMAL --", schedule_refresh=False)

    def enter_insert(self, repl: "BaseRepl") -> None:
        self.mode = VimMode.INSERT
        self.vbuf = None
        repl.status_bar.message("-- INSERT --", schedule_refresh=False)

    def handle(self, e: str, repl: "BaseRepl") -> bool:
        """Process a keypress. Returns True if consumed."""
        if self.mode == VimMode.INSERT:
            if e == "<ESC>":
                self.enter_normal(repl)
                return True
            if e in ("\n", "\r", "<Ctrl-j>", "<Ctrl-m>") and self.vbuf:
                self.vbuf.current = repl._current_line
                if self.vbuf.row == len(self.vbuf.lines) - 1:
                    self.vbuf = None
                    return False
                self._resubmit(repl)
                return True
            return False

        if self.mode == VimMode.COMMAND:
            return self._command_key(e, repl)

        return self._normal_key(e, repl)

    def _command_key(self, e: str, repl: "BaseRepl") -> bool:
        if e in ("\n", "\r", "<Ctrl-j>", "<Ctrl-m>"):
            cmd, self.cmd = self.cmd, ""
            self.mode = VimMode.NORMAL
            self._exec(cmd.strip(), repl)
        elif e == "<ESC>":
            self.cmd = ""
            self.mode = VimMode.NORMAL
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
        elif e in ("<BACKSPACE>", "<Ctrl-h>"):
            self.cmd = self.cmd[:-1]
            if self.cmd:
                repl.status_bar.message(":" + self.cmd, schedule_refresh=False)
            else:
                self.mode = VimMode.NORMAL
                repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
        elif e == "<SPACE>":
            self.cmd += " "
            repl.status_bar.message(":" + self.cmd, schedule_refresh=False)
        elif len(e) == 1:
            self.cmd += e
            repl.status_bar.message(":" + self.cmd, schedule_refresh=False)
        return True

    def _exec(self, cmd: str, repl: "BaseRepl") -> None:
        if not cmd:
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
            return

        if cmd == "w" or cmd.startswith("w "):
            import greenlet as _gl
            parts = cmd.split(None, 1)
            filename = parts[1] if len(parts) > 1 else None
            _gl.greenlet(lambda: self._write(filename, repl)).switch()
        elif cmd.startswith("r "):
            self._read(cmd[2:].strip(), repl)
        elif re.match(r"^s/", cmd):
            self._substitute(cmd, repl)
        elif cmd == "history":
            repl.incremental_search(reverse=True)
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
        elif cmd == "clear":
            repl.request_paint_to_clear_screen = True
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
        else:
            repl.status_bar.message(f"Not a command: {cmd}")

    def _write(self, filename: str | None, repl: "BaseRepl") -> None:
        if not repl.interact.confirm("Continue this session in a file? (y/N) "):
            repl.interact.notify("Save cancelled.")
            return

        fn = filename or repl.interact.file_prompt("Filename (Esc to cancel): ")
        if not fn:
            repl.interact.notify("Save cancelled.")
            return

        from pathlib import Path

        path = Path(fn).expanduser()
        if path.suffix != ".py" and repl.config.save_append_py:
            path = Path(f"{fn}.py")

        mode = "w"
        if path.exists():
            choice = repl.interact.file_prompt(
                f"{path} exists. (o)verwrite, (a)ppend or cancel? "
            )
            if choice in ("o", "overwrite"):
                mode = "w"
            elif choice in ("a", "append"):
                mode = "a"
            else:
                repl.interact.notify("Save cancelled.")
                return

        try:
            with open(path, mode) as f:
                f.write(repl.get_session_formatted_for_file())
        except OSError as exc:
            repl.interact.notify(f"Error writing {path}: {exc}")
        else:
            repl.interact.notify(f"Saved to {path}.")

    def _read(self, filename: str, repl: "BaseRepl") -> None:
        from pathlib import Path

        path = Path(filename).expanduser()
        if not path.exists():
            repl.status_bar.message(f"No such file: {path}")
            return
        try:
            source = path.read_text()
        except OSError as exc:
            repl.status_bar.message(f"Error reading {path}: {exc}")
            return
        repl.interp.runsource(source, str(path))
        repl.status_bar.message(f"Loaded {path}.")

    def _substitute(self, cmd: str, repl: "BaseRepl") -> None:
        m = re.match(r"^s/([^/]*)/([^/]*)(?:/([g]?))?$", cmd)
        if not m:
            repl.status_bar.message(f"Invalid substitution: {cmd}")
            return
        old, new, flags = m.group(1), m.group(2), m.group(3) or ""
        line = repl._current_line
        repl.current_line = (
            line.replace(old, new) if "g" in flags else line.replace(old, new, 1)
        )
        repl._cursor_offset = len(repl._current_line)
        repl.status_bar.message("-- NORMAL --", schedule_refresh=False)

    def _normal_key(self, e: str, repl: "BaseRepl") -> bool:
        if e == '"':
            self._awaiting_reg = True
            return True
        if self._awaiting_reg:
            self._awaiting_reg = False
            if e.isalpha():
                self._pending_reg = e.lower()
            return True

        if e != "g" and self._pending_g:
            self._pending_g = False

        if e.isdigit() and e != "0" and not self.pending_op:
            self.count += e
            return True

        n = int(self.count) if self.count else 1
        self.count = ""

        if self.pending_op:
            return self._operator_motion(e, repl, n)

        return self._action(e, repl, n)

    def _action(self, e: str, repl: "BaseRepl", n: int) -> bool:
        col = repl._cursor_offset
        line = repl._current_line

        if e == "i":
            self.enter_insert(repl)
        elif e == "a":
            repl._cursor_offset = min(len(line), col + 1)
            self.enter_insert(repl)
        elif e == "A":
            repl._cursor_offset = len(line)
            self.enter_insert(repl)
        elif e == "I":
            repl._cursor_offset = 0
            self.enter_insert(repl)

        elif e in ("h", "<LEFT>"):
            repl._cursor_offset = max(0, col - n)
        elif e in ("l", "<RIGHT>"):
            repl._cursor_offset = min(len(line), col + n)
        elif e == "0":
            repl._cursor_offset = 0
        elif e == "$":
            repl._cursor_offset = max(0, len(line) - 1)
        elif e == "w":
            c = col
            for _ in range(n):
                c = _forward_word(line, c)
            repl._cursor_offset = c
        elif e == "b":
            c = col
            for _ in range(n):
                c = _back_word(line, c)
            repl._cursor_offset = c
        elif e == "e":
            c = col
            for _ in range(n):
                c = _end_word(line, c)
            repl._cursor_offset = c

        elif e in ("j", "<DOWN>"):
            if self.vbuf:
                if not self.vbuf.down():
                    self.vbuf = None
                    repl.down_one_line()
                else:
                    self._show(repl)
            else:
                repl.down_one_line()
        elif e in ("k", "<UP>"):
            if self.vbuf:
                self.vbuf.up()
                self._show(repl)
            else:
                repl.up_one_line()
        elif e == "g":
            if self._pending_g:
                self._pending_g = False
                if self.vbuf:
                    self.vbuf.first()
                    self._show(repl)
            else:
                self._pending_g = True
        elif e == "G":
            if self.vbuf:
                self.vbuf.last()
                self._show(repl)

        elif e == "x":
            if col < len(line):
                self._store(line[col])
                repl.current_line = line[:col] + line[col + 1:]
                repl._cursor_offset = min(col, max(0, len(repl._current_line) - 1))

        elif e in ("d", "c", "y"):
            self.pending_op = e

        elif e == "p":
            text = self._load()
            if text:
                pos = col + 1
                repl.current_line = line[:pos] + text + line[pos:]
                repl._cursor_offset = pos + len(text) - 1
        elif e == "P":
            text = self._load()
            if text:
                repl.current_line = line[:col] + text + line[col:]
                repl._cursor_offset = col + len(text) - 1

        elif e == "K":
            self._inspect(repl)
        elif e == ".":
            self._dot_repeat(repl)
        elif e == ":":
            self.mode = VimMode.COMMAND
            self.cmd = ""
            repl.status_bar.message(":", schedule_refresh=False)
        elif e == "u":
            repl.prompt_undo()
        elif e in ("\n", "\r", "<Ctrl-j>", "<Ctrl-m>"):
            if self.vbuf:
                self.vbuf.current = repl._current_line
                self._resubmit(repl)
            else:
                self.enter_insert(repl)
                repl.on_enter()

        return True

    def _operator_motion(self, e: str, repl: "BaseRepl", n: int) -> bool:
        op = self.pending_op
        self.pending_op = None
        col = repl._cursor_offset
        line = repl._current_line
        reg = self._pending_reg

        if e == op:
            self._store(line)
            if op == "d":
                if self.vbuf:
                    self.vbuf.current = ""
                    self.vbuf.delete_row()
                    self._show(repl)
                else:
                    repl.current_line = ""
                    repl._cursor_offset = 0
            elif op == "c":
                repl.current_line = ""
                repl._cursor_offset = 0
                self.enter_insert(repl)
            elif op == "y":
                repl.status_bar.message(f'Yanked to "{reg}.', schedule_refresh=False)
            return True

        target = col
        if e == "w":
            target = _forward_word(line, col)
        elif e == "b":
            target = _back_word(line, col)
        elif e == "e":
            target = _end_word(line, col) + 1
        elif e == "$":
            target = len(line)
        elif e == "0":
            target = 0
        else:
            return True

        lo, hi = sorted((col, target))
        self._store(line[lo:hi])
        if op in ("d", "c"):
            repl.current_line = line[:lo] + line[hi:]
            repl._cursor_offset = lo
        if op == "c":
            self.enter_insert(repl)

        return True

    def _show(self, repl: "BaseRepl") -> None:
        if self.vbuf:
            repl._current_line = self.vbuf.current
            repl._cursor_offset = self.vbuf.col

    def _resubmit(self, repl: "BaseRepl") -> None:
        if not self.vbuf:
            return
        lines = list(self.vbuf.lines)
        self.vbuf = None
        repl.clear_current_block()
        with repl.in_paste_mode():
            for line in lines[:-1]:
                repl._current_line = line
                repl.on_enter(new_code=True, reset_rl_history=False)
        repl._current_line = lines[-1]
        repl._cursor_offset = len(lines[-1])
        self.enter_insert(repl)

    def _inspect(self, repl: "BaseRepl") -> None:
        word = _word_at(repl._current_line, repl._cursor_offset)
        if not word:
            repl.status_bar.message("No symbol under cursor.")
            return
        try:
            obj = eval(word, repl.interp.locals)
        except Exception:
            repl.status_bar.message(f"{word}: not found.")
            return
        import inspect as _ins

        doc = _ins.getdoc(obj)
        if not doc:
            repl.status_bar.message(f"{word}: {type(obj).__name__} (no docstring)")
            return
        if len(doc) > 300:
            repl.pager(doc)
        else:
            repl.status_bar.message(f"{word}: {doc.split(chr(10))[0]}")

    def _dot_repeat(self, repl: "BaseRepl") -> None:
        if not repl.history:
            return
        last = repl.history[-1]
        repl.current_line = last
        repl._cursor_offset = len(last)
        self.enter_insert(repl)
        repl.on_enter()
