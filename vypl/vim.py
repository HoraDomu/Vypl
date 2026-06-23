"""Vim modal editing for Vypl."""

import builtins as _builtins
import re
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .curtsiesfrontend.repl import BaseRepl


class VimMode(Enum):
    INSERT = auto()
    NORMAL = auto()
    COMMAND = auto()
    VISUAL = auto()
    SEARCH = auto()


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
        if m.start() <= col < m.end():
            return m.group()
    return None


def _resolve(word: str, locals_: dict) -> object:
    """Look up a dotted name in locals/builtins without calling eval."""
    parts = word.split(".")
    obj = locals_.get(parts[0]) or getattr(_builtins, parts[0], None)
    if obj is None:
        raise KeyError(parts[0])
    for attr in parts[1:]:
        obj = getattr(obj, attr)
    return obj


def _find_text_object(
    line: str, col: int, delimiter: str, inner: bool
) -> tuple[int, int] | None:
    """Return (start, end) indices for a text object, or None if not found."""
    OPEN_FOR = {"(": "(", "[": "[", "{": "{", ")": "(", "]": "[", "}": "{"}
    CLOSE_FOR = {"(": ")", "[": "]", "{": "}"}

    if delimiter == "w":
        start = _back_word(line, col + 1)
        end = _end_word(line, start) + 1
        if not inner:
            while end < len(line) and line[end].isspace():
                end += 1
        return (start, end)

    if delimiter in OPEN_FOR:
        open_ch = OPEN_FOR[delimiter]
        close_ch = CLOSE_FOR[open_ch]
        # Scan left for open bracket
        depth = 0
        start = col
        while start >= 0:
            if line[start] == close_ch:
                depth += 1
            elif line[start] == open_ch:
                if depth == 0:
                    break
                depth -= 1
            start -= 1
        if start < 0:
            return None
        # Scan right for close bracket
        depth = 0
        end = col
        while end < len(line):
            if line[end] == open_ch:
                depth += 1
            elif line[end] == close_ch:
                if depth == 0:
                    break
                depth -= 1
            end += 1
        if end >= len(line):
            return None
        return (start + 1, end) if inner else (start, end + 1)

    # Quote delimiter
    start = col - 1
    while start >= 0 and line[start] != delimiter:
        start -= 1
    if start < 0:
        return None
    end = col + 1
    while end < len(line) and line[end] != delimiter:
        end += 1
    if end >= len(line):
        return None
    return (start + 1, end) if inner else (start, end + 1)


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

    def insert_row_below(self) -> None:
        self.lines.insert(self.row + 1, "")
        self.row += 1
        self.col = 0

    def insert_row_above(self) -> None:
        self.lines.insert(self.row, "")
        self.col = 0


class VimState:
    def __init__(self) -> None:
        self.mode: VimMode = VimMode.INSERT
        self.registers: dict[str, str | list] = {'"': ""}
        self._pending_reg: str = '"'
        self._awaiting_reg: bool = False
        self._pending_g: bool = False
        self.pending_op: str | None = None
        self._op_count: int = 1
        self.cmd: str = ""
        self.count: str = ""
        self.vbuf: VimBuffer | None = None

        # Dot-repeat
        self._last_change: Callable | None = None
        self._insert_line_before: str = ""

        # f/F find
        self._awaiting_find: str | None = None
        self._last_find: tuple[str, bool] | None = None

        # r replace
        self._awaiting_replace: bool = False

        # Text objects
        self._awaiting_text_obj: bool = False
        self._text_obj_inner: bool = True

        # Visual mode
        self._visual_start: int = 0

        # Macro recording/replay
        self._recording: str | None = None
        self._macro_buf: list[str] = []
        self._awaiting_macro_reg: bool = False
        self._awaiting_macro_replay: bool = False

        # / search
        self.search_query: str = ""
        self._search_matches: list[str] = []
        self._search_idx: int = 0

    def _store(self, text: str) -> None:
        self.registers[self._pending_reg] = text
        self._pending_reg = '"'

    def _load(self) -> str:
        val = self.registers.get(self._pending_reg, "")
        self._pending_reg = '"'
        return val if isinstance(val, str) else ""

    def enter_normal(self, repl: "BaseRepl") -> None:
        if self.mode == VimMode.INSERT:
            new_line = repl._current_line
            if new_line != self._insert_line_before:
                captured = new_line
                def _replay_insert(r: "BaseRepl", _ln=captured) -> None:
                    r.current_line = _ln
                    r._cursor_offset = max(0, len(_ln) - 1)
                self._last_change = _replay_insert

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
        self._insert_line_before = repl._current_line
        self.mode = VimMode.INSERT
        self.vbuf = None
        repl.status_bar.message("-- INSERT --", schedule_refresh=False)

    def enter_visual(self, repl: "BaseRepl") -> None:
        self.mode = VimMode.VISUAL
        self._visual_start = repl._cursor_offset
        repl.status_bar.message("-- VISUAL --", schedule_refresh=False)

    def handle(self, e: str, repl: "BaseRepl") -> bool:
        """Process a keypress. Returns True if consumed."""
        if self._recording is not None and self.mode == VimMode.NORMAL and e != "q":
            self._macro_buf.append(e)

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

        if self.mode == VimMode.SEARCH:
            return self._search_key(e, repl)

        if self.mode == VimMode.VISUAL:
            return self._visual_key(e, repl)

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

    def _search_key(self, e: str, repl: "BaseRepl") -> bool:
        if e in ("\n", "\r", "<Ctrl-j>", "<Ctrl-m>"):
            query = self.search_query
            self.mode = VimMode.NORMAL
            if query:
                matches = [h for h in repl.history if query.lower() in h.lower()]
                self._search_matches = matches
                self._search_idx = len(matches) - 1
                if matches:
                    repl.current_line = matches[self._search_idx]
                    repl._cursor_offset = 0
                    repl.status_bar.message(
                        f"/{query} — {len(matches)} match(es)",
                        schedule_refresh=False,
                    )
                else:
                    repl.status_bar.message(
                        f"/{query}: no matches", schedule_refresh=False
                    )
            else:
                repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
        elif e == "<ESC>":
            self.search_query = ""
            self.mode = VimMode.NORMAL
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
        elif e in ("<BACKSPACE>", "<Ctrl-h>"):
            self.search_query = self.search_query[:-1]
            repl.status_bar.message("/" + self.search_query, schedule_refresh=False)
        elif len(e) == 1:
            self.search_query += e
            repl.status_bar.message("/" + self.search_query, schedule_refresh=False)
        return True

    def _visual_key(self, e: str, repl: "BaseRepl") -> bool:
        col = repl._cursor_offset
        line = repl._current_line

        if e in ("<ESC>", "v"):
            self.mode = VimMode.NORMAL
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
            return True

        if e in ("h", "<LEFT>"):
            repl._cursor_offset = max(0, col - 1)
        elif e in ("l", "<RIGHT>"):
            repl._cursor_offset = min(max(0, len(line) - 1), col + 1)
        elif e == "w":
            repl._cursor_offset = _forward_word(line, col)
        elif e == "b":
            repl._cursor_offset = _back_word(line, col)
        elif e == "e":
            repl._cursor_offset = _end_word(line, col)
        elif e == "0":
            repl._cursor_offset = 0
        elif e == "$":
            repl._cursor_offset = max(0, len(line) - 1)
        elif e in ("d", "x"):
            lo = min(self._visual_start, col)
            hi = max(self._visual_start, col) + 1
            self._store(line[lo:hi])
            repl.current_line = line[:lo] + line[hi:]
            repl._cursor_offset = min(lo, max(0, len(repl._current_line) - 1))
            self.mode = VimMode.NORMAL
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
        elif e == "y":
            lo = min(self._visual_start, col)
            hi = max(self._visual_start, col) + 1
            self._store(line[lo:hi])
            self.mode = VimMode.NORMAL
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
        elif e == "c":
            lo = min(self._visual_start, col)
            hi = max(self._visual_start, col) + 1
            self._store(line[lo:hi])
            repl.current_line = line[:lo] + line[hi:]
            repl._cursor_offset = lo
            self.enter_insert(repl)
        return True

    def _exec(self, cmd: str, repl: "BaseRepl") -> None:
        if not cmd:
            repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
            return

        if cmd in ("q", "q!", "quit"):
            raise SystemExit()
        elif cmd == "w" or cmd.startswith("w "):
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
        repl._cursor_offset = max(0, len(repl._current_line) - 1)
        repl.status_bar.message("-- NORMAL --", schedule_refresh=False)

    def _normal_key(self, e: str, repl: "BaseRepl") -> bool:
        # Text object delimiter must be checked before the register prefix so
        # that `ci"` / `di(` etc. are not swallowed by the `"` register check.
        if self._awaiting_text_obj:
            self._awaiting_text_obj = False
            line = repl._current_line
            col = repl._cursor_offset
            result = _find_text_object(line, col, e, self._text_obj_inner)
            if result and self.pending_op:
                lo, hi = result
                op = self.pending_op
                self.pending_op = None
                self._store(line[lo:hi])
                if op in ("d", "c"):
                    repl.current_line = line[:lo] + line[hi:]
                    repl._cursor_offset = min(
                        lo, max(0, len(repl._current_line) - 1)
                    )
                if op == "c":
                    self.enter_insert(repl)
            return True

        if e == '"':
            self._awaiting_reg = True
            return True
        if self._awaiting_reg:
            self._awaiting_reg = False
            if e.isalpha():
                self._pending_reg = e.lower()
            return True

        if self._awaiting_macro_reg:
            self._awaiting_macro_reg = False
            if e.isalpha():
                self._recording = e.lower()
                self._macro_buf = []
                repl.status_bar.message(
                    f"recording @{e.lower()}", schedule_refresh=False
                )
            return True

        if self._awaiting_macro_replay:
            self._awaiting_macro_replay = False
            if e.isalpha():
                keys = self.registers.get(e.lower(), [])
                if isinstance(keys, list):
                    for k in keys:
                        self.handle(k, repl)
            return True

        if self._awaiting_find is not None:
            direction = self._awaiting_find
            self._awaiting_find = None
            forward = direction == "f"
            self._last_find = (e, forward)
            self._do_find(e, forward, repl)
            return True

        if self._awaiting_replace:
            self._awaiting_replace = False
            line = repl._current_line
            col = repl._cursor_offset
            if col < len(line):
                repl.current_line = line[:col] + e + line[col + 1:]
                repl._cursor_offset = col
                ch = e
                def _replay_r(r: "BaseRepl", _ch=ch) -> None:
                    ln = r._current_line
                    c = r._cursor_offset
                    if c < len(ln):
                        r.current_line = ln[:c] + _ch + ln[c + 1:]
                        r._cursor_offset = c
                self._last_change = _replay_r
            return True

        if e != "g" and self._pending_g:
            self._pending_g = False

        # Digits before operator accumulate as op count
        if e.isdigit() and e != "0" and not self.pending_op:
            self.count += e
            return True

        n = int(self.count) if self.count else 1
        self.count = ""

        if self.pending_op:
            # Digits after operator accumulate as motion count
            if e.isdigit() and e != "0":
                self.count += e
                return True
            # Text object
            if e in ("i", "a"):
                self._awaiting_text_obj = True
                self._text_obj_inner = e == "i"
                return True
            return self._operator_motion(e, repl, n)

        return self._action(e, repl, n)

    def _do_find(self, char: str, forward: bool, repl: "BaseRepl") -> None:
        line = repl._current_line
        col = repl._cursor_offset
        idx = line.find(char, col + 1) if forward else line.rfind(char, 0, col)
        if idx == -1:
            return
        if self.pending_op:
            op = self.pending_op
            self.pending_op = None
            hi_offset = 1 if forward else 0
            lo, hi = sorted((col, idx + hi_offset))
            self._store(line[lo:hi])
            if op in ("d", "c"):
                repl.current_line = line[:lo] + line[hi:]
                repl._cursor_offset = lo
            if op == "c":
                self.enter_insert(repl)
        else:
            repl._cursor_offset = idx

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
                def _replay_x(r: "BaseRepl") -> None:
                    ln = r._current_line
                    c = r._cursor_offset
                    if c < len(ln):
                        self._store(ln[c])
                        r.current_line = ln[:c] + ln[c + 1:]
                        r._cursor_offset = min(c, max(0, len(r._current_line) - 1))
                self._last_change = _replay_x

        elif e in ("d", "c", "y"):
            self._op_count = n
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

        elif e == "f":
            self._awaiting_find = "f"
        elif e == "F":
            self._awaiting_find = "F"
        elif e == ";":
            if self._last_find:
                self._do_find(self._last_find[0], self._last_find[1], repl)
        elif e == ",":
            if self._last_find:
                self._do_find(self._last_find[0], not self._last_find[1], repl)

        elif e == "r":
            if col < len(line):
                self._awaiting_replace = True

        elif e == "o":
            if self.vbuf:
                self.vbuf.current = repl._current_line
                self.vbuf.insert_row_below()
                self._show(repl)
                self.enter_insert(repl)
            else:
                repl._cursor_offset = len(line)
                self.enter_insert(repl)
        elif e == "O":
            if self.vbuf:
                self.vbuf.current = repl._current_line
                self.vbuf.insert_row_above()
                self._show(repl)
                self.enter_insert(repl)
            else:
                repl._cursor_offset = 0
                self.enter_insert(repl)

        elif e == "v":
            self.enter_visual(repl)

        elif e == "q":
            if self._recording is not None:
                self.registers[self._recording] = list(self._macro_buf)
                self._recording = None
                self._macro_buf = []
                repl.status_bar.message("-- NORMAL --", schedule_refresh=False)
            else:
                self._awaiting_macro_reg = True
        elif e == "@":
            self._awaiting_macro_replay = True

        elif e == "n":
            if self._search_matches:
                self._search_idx = max(0, self._search_idx - 1)
                repl.current_line = self._search_matches[self._search_idx]
                repl._cursor_offset = 0
        elif e == "N":
            if self._search_matches:
                self._search_idx = min(
                    len(self._search_matches) - 1, self._search_idx + 1
                )
                repl.current_line = self._search_matches[self._search_idx]
                repl._cursor_offset = 0

        elif e == "K":
            self._inspect(repl)
        elif e == ".":
            self._dot_repeat(repl)
        elif e == ":":
            self.mode = VimMode.COMMAND
            self.cmd = ""
            repl.status_bar.message(":", schedule_refresh=False)
        elif e == "/":
            self.mode = VimMode.SEARCH
            self.search_query = ""
            repl.status_bar.message("/", schedule_refresh=False)
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
        total = self._op_count * n

        if e == op:
            # Linewise operation (dd, cc, yy) — repeat _op_count times
            for _ in range(self._op_count):
                self._store(line)
                if op == "d":
                    if self.vbuf:
                        self.vbuf.current = ""
                        self.vbuf.delete_row()
                        self._show(repl)
                        line = repl._current_line
                    else:
                        repl.current_line = ""
                        repl._cursor_offset = 0
                        break
                elif op == "c":
                    repl.current_line = ""
                    repl._cursor_offset = 0
                    break
                elif op == "y":
                    repl.status_bar.message(
                        f'Yanked to "{reg}.', schedule_refresh=False
                    )
                    break
            if op == "c":
                self.enter_insert(repl)

            captured_op = op
            captured_count = self._op_count
            def _replay_linewise(r: "BaseRepl", _op=captured_op, _cnt=captured_count) -> None:
                self._op_count = _cnt
                self.pending_op = _op
                self._operator_motion(_op, r, 1)
            self._last_change = _replay_linewise
            return True

        target = col
        if e == "w":
            c = col
            for _ in range(total):
                c = _forward_word(line, c)
            target = c
        elif e == "b":
            c = col
            for _ in range(total):
                c = _back_word(line, c)
            target = c
        elif e == "e":
            c = col
            for _ in range(total):
                c = _end_word(line, c)
            target = c + 1
        elif e == "$":
            target = len(line)
        elif e == "0":
            target = 0
        elif e in ("f", "F"):
            # Restore pending_op; _do_find will clear it
            self.pending_op = op
            self._awaiting_find = e
            return True
        else:
            return True

        lo, hi = sorted((col, target))
        self._store(line[lo:hi])
        if op in ("d", "c"):
            repl.current_line = line[:lo] + line[hi:]
            repl._cursor_offset = lo

            captured_op2 = op
            captured_motion = e
            captured_total = total
            def _replay_motion(
                r: "BaseRepl", _op=captured_op2, _mot=captured_motion, _tot=captured_total
            ) -> None:
                self._op_count = _tot
                self.pending_op = _op
                self._operator_motion(_mot, r, 1)
            self._last_change = _replay_motion

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
            obj = _resolve(word, repl.interp.locals)
        except (KeyError, AttributeError):
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
        if self._last_change is not None:
            self._last_change(repl)
