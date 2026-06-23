"""Tests for VimState and word-motion helpers."""

from enum import Enum
from unittest.mock import MagicMock

from vypl.vim import (
    VimMode,
    VimState,
    _back_word,
    _end_word,
    _forward_word,
    _word_at,
)


class _SearchMode(Enum):
    NO_SEARCH = 0
    INCREMENTAL_SEARCH = 1
    REVERSE_INCREMENTAL_SEARCH = 2


class MockRepl:
    def __init__(self, line: str = "", col: int = 0):
        self._current_line = line
        self._cursor_offset = col
        self.buffer: list[str] = []
        self.history: list[str] = []
        self.incr_search_mode = _SearchMode.NO_SEARCH
        self.status_bar = MagicMock()
        self.interact = MagicMock()
        self.interp = MagicMock()
        self.interp.locals = {}

    @property
    def current_line(self) -> str:
        return self._current_line

    @current_line.setter
    def current_line(self, val: str) -> None:
        self._current_line = val

    @property
    def cursor_offset(self) -> int:
        return self._cursor_offset

    @cursor_offset.setter
    def cursor_offset(self, val: int) -> None:
        self._cursor_offset = val

    def up_one_line(self) -> None:
        pass

    def down_one_line(self) -> None:
        pass

    def on_enter(self, **kwargs) -> None:
        pass

    def prompt_undo(self) -> None:
        pass

    def incremental_search(self, **kwargs) -> None:
        pass


def make(line: str = "", col: int = 0) -> tuple[VimState, MockRepl]:
    vim = VimState()
    repl = MockRepl(line, col)
    return vim, repl


def normal(vim: VimState, repl: MockRepl) -> None:
    vim.handle("<ESC>", repl)


# ---------------------------------------------------------------------------
# Word motion helpers
# ---------------------------------------------------------------------------

class TestForwardWord:
    def test_simple(self):
        assert _forward_word("hello world", 0) == 6

    def test_from_middle(self):
        assert _forward_word("hello world", 3) == 6

    def test_end_of_string(self):
        assert _forward_word("hello", 0) == 5

    def test_skips_whitespace(self):
        assert _forward_word("hello   world", 0) == 8

    def test_at_last_word(self):
        assert _forward_word("foo bar", 4) == 7


class TestBackWord:
    def test_simple(self):
        assert _back_word("hello world", 6) == 0

    def test_from_end(self):
        assert _back_word("hello world", 11) == 6

    def test_already_at_start(self):
        assert _back_word("hello", 0) == 0

    def test_over_whitespace(self):
        assert _back_word("hello   world", 11) == 8


class TestEndWord:
    def test_simple(self):
        assert _end_word("hello world", 0) == 4

    def test_from_middle(self):
        assert _end_word("hello world", 3) == 4

    def test_next_word(self):
        assert _end_word("hello world", 5) == 10


class TestWordAt:
    def test_on_word(self):
        assert _word_at("hello world", 3) == "hello"

    def test_on_second_word(self):
        assert _word_at("hello world", 8) == "world"

    def test_on_space(self):
        assert _word_at("hello world", 5) is None

    def test_empty(self):
        assert _word_at("", 0) is None


# ---------------------------------------------------------------------------
# Mode switching
# ---------------------------------------------------------------------------

class TestModeSwitching:
    def test_starts_in_insert(self):
        vim, _ = make()
        assert vim.mode == VimMode.INSERT

    def test_esc_enters_normal(self):
        vim, repl = make("hello", 3)
        normal(vim, repl)
        assert vim.mode == VimMode.NORMAL

    def test_i_returns_to_insert(self):
        vim, repl = make("hello", 3)
        normal(vim, repl)
        vim.handle("i", repl)
        assert vim.mode == VimMode.INSERT

    def test_a_inserts_after(self):
        # enter_normal shifts cursor left by 1 (col 2 → 1), then a moves right one more
        vim, repl = make("hello", 2)
        normal(vim, repl)
        vim.handle("a", repl)
        assert vim.mode == VimMode.INSERT
        assert repl._cursor_offset == 2

    def test_A_inserts_at_end(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("A", repl)
        assert vim.mode == VimMode.INSERT
        assert repl._cursor_offset == 5

    def test_I_inserts_at_start(self):
        vim, repl = make("hello", 3)
        normal(vim, repl)
        vim.handle("I", repl)
        assert vim.mode == VimMode.INSERT
        assert repl._cursor_offset == 0

    def test_insert_events_pass_through(self):
        vim, repl = make("hello", 0)
        result = vim.handle("x", repl)
        assert result is False
        assert repl._current_line == "hello"


# ---------------------------------------------------------------------------
# Cursor motions
# ---------------------------------------------------------------------------

class TestMotions:
    def test_h_moves_left(self):
        vim, repl = make("hello", 3)
        normal(vim, repl)
        vim.handle("h", repl)
        assert repl._cursor_offset == 1

    def test_h_clamps_at_zero(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("h", repl)
        assert repl._cursor_offset == 0

    def test_l_moves_right(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("l", repl)
        assert repl._cursor_offset == 1

    def test_zero_goes_to_start(self):
        vim, repl = make("hello", 3)
        normal(vim, repl)
        vim.handle("0", repl)
        assert repl._cursor_offset == 0

    def test_dollar_goes_to_end(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("$", repl)
        assert repl._cursor_offset == 4

    def test_w_moves_forward(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("w", repl)
        assert repl._cursor_offset == 6

    def test_b_moves_back(self):
        vim, repl = make("hello world", 6)
        normal(vim, repl)
        vim.handle("b", repl)
        # after ESC cursor moves left by 1 to 5, then b moves to start
        assert repl._cursor_offset == 0

    def test_e_moves_to_word_end(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("e", repl)
        assert repl._cursor_offset == 4


# ---------------------------------------------------------------------------
# Operators and delete
# ---------------------------------------------------------------------------

class TestOperators:
    def test_x_deletes_char(self):
        # enter_normal shifts col 2 → 1, so x deletes char at index 1 ('e')
        vim, repl = make("hello", 2)
        normal(vim, repl)
        vim.handle("x", repl)
        assert repl._current_line == "hllo"

    def test_x_stores_in_register(self):
        vim, repl = make("hello", 2)
        normal(vim, repl)
        vim.handle("x", repl)
        assert vim.registers['"'] == "e"

    def test_dd_clears_line(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("d", repl)
        vim.handle("d", repl)
        assert repl._current_line == ""

    def test_dd_yanks_to_register(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("d", repl)
        vim.handle("d", repl)
        assert vim.registers['"'] == "hello"

    def test_dw_deletes_word(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("d", repl)
        vim.handle("w", repl)
        assert repl._current_line == "world"

    def test_yy_yanks_line(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("y", repl)
        vim.handle("y", repl)
        assert vim.registers['"'] == "hello"

    def test_cc_clears_and_enters_insert(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("c", repl)
        vim.handle("c", repl)
        assert repl._current_line == ""
        assert vim.mode == VimMode.INSERT

    def test_p_pastes_after(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.registers['"'] = "world"
        vim.handle("p", repl)
        assert "world" in repl._current_line


# ---------------------------------------------------------------------------
# Named registers
# ---------------------------------------------------------------------------

class TestNamedRegisters:
    def test_yank_to_named_register(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle('"', repl)
        vim.handle("a", repl)
        vim.handle("y", repl)
        vim.handle("y", repl)
        assert vim.registers.get("a") == "hello"

    def test_paste_from_named_register(self):
        vim, repl = make("x", 0)
        normal(vim, repl)
        vim.registers["a"] = "abc"
        vim.handle('"', repl)
        vim.handle("a", repl)
        vim.handle("p", repl)
        assert "abc" in repl._current_line

    def test_registers_are_independent(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.registers["a"] = "aaa"
        vim.registers["b"] = "bbb"
        assert vim.registers["a"] == "aaa"
        assert vim.registers["b"] == "bbb"


# ---------------------------------------------------------------------------
# Command mode
# ---------------------------------------------------------------------------

class TestCommandMode:
    def test_colon_enters_command_mode(self):
        vim, repl = make()
        normal(vim, repl)
        vim.handle(":", repl)
        assert vim.mode == VimMode.COMMAND

    def test_esc_exits_command_mode(self):
        vim, repl = make()
        normal(vim, repl)
        vim.handle(":", repl)
        vim.handle("<ESC>", repl)
        assert vim.mode == VimMode.NORMAL

    def test_command_buffer_builds(self):
        vim, repl = make()
        normal(vim, repl)
        vim.handle(":", repl)
        vim.handle("c", repl)
        vim.handle("l", repl)
        vim.handle("e", repl)
        assert vim.cmd == "cle"

    def test_backspace_removes_char(self):
        vim, repl = make()
        normal(vim, repl)
        vim.handle(":", repl)
        vim.handle("c", repl)
        vim.handle("<BACKSPACE>", repl)
        assert vim.cmd == ""
        assert vim.mode == VimMode.NORMAL

    def test_substitute_command(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        for ch in ":s/hello/goodbye\n":
            vim.handle(ch, repl)
        assert repl._current_line == "goodbye world"

    def test_substitute_global(self):
        vim, repl = make("aa bb aa", 0)
        normal(vim, repl)
        for ch in ":s/aa/cc/g\n":
            vim.handle(ch, repl)
        assert repl._current_line == "cc bb cc"


# ---------------------------------------------------------------------------
# Dot repeat
# ---------------------------------------------------------------------------

class TestDotRepeat:
    def test_dot_reruns_last_history(self):
        vim, repl = make("", 0)
        repl.history = ["x = 1"]
        entered = []
        repl.on_enter = lambda **kw: entered.append(repl._current_line)
        normal(vim, repl)
        vim.handle(".", repl)
        assert entered == ["x = 1"]

    def test_dot_does_nothing_with_empty_history(self):
        vim, repl = make()
        normal(vim, repl)
        vim.handle(".", repl)
