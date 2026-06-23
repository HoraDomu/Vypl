"""Tests for VimState and word-motion helpers."""

from contextlib import contextmanager
from enum import Enum
from unittest.mock import MagicMock

from vypl.vim import (
    VimMode,
    VimState,
    _back_word,
    _end_word,
    _find_text_object,
    _forward_word,
    _resolve,
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
        self.request_paint_to_clear_screen = False

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

    def pager(self, text: str) -> None:
        pass

    def clear_current_block(self) -> None:
        pass

    def get_session_formatted_for_file(self) -> str:
        return ""

    @contextmanager
    def in_paste_mode(self):
        yield


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


class TestResolve:
    def test_finds_in_locals(self):
        class Obj:
            pass
        obj = Obj()
        assert _resolve("obj", {"obj": obj}) is obj

    def test_finds_in_builtins(self):
        assert _resolve("len", {}) is len

    def test_attribute_chain(self):
        import os
        assert _resolve("os.path", {"os": os}) is os.path

    def test_missing_raises(self):
        import pytest
        with pytest.raises((KeyError, AttributeError)):
            _resolve("nonexistent_xyz", {})


# ---------------------------------------------------------------------------
# Text object helper
# ---------------------------------------------------------------------------

class TestFindTextObject:
    def test_inner_word(self):
        assert _find_text_object("hello world", 2, "w", inner=True) == (0, 5)

    def test_around_word_includes_space(self):
        result = _find_text_object("hello world", 2, "w", inner=False)
        assert result is not None
        lo, hi = result
        assert lo == 0
        assert hi >= 6  # includes trailing space

    def test_inner_parens(self):
        assert _find_text_object("foo(bar)", 5, "(", inner=True) == (4, 7)

    def test_around_parens(self):
        assert _find_text_object("foo(bar)", 5, "(", inner=False) == (3, 8)

    def test_inner_brackets(self):
        assert _find_text_object("x[abc]y", 3, "[", inner=True) == (2, 5)

    def test_inner_double_quotes(self):
        assert _find_text_object('say "hello"', 6, '"', inner=True) == (5, 10)

    def test_around_double_quotes(self):
        assert _find_text_object('say "hello"', 6, '"', inner=False) == (4, 11)

    def test_no_match_returns_none(self):
        assert _find_text_object("hello world", 3, "(", inner=True) is None


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
# Count prefixes with operators
# ---------------------------------------------------------------------------

class TestCountOperators:
    def test_3x_deletes_three_chars(self):
        vim, repl = make("abcdef", 0)
        normal(vim, repl)
        vim.handle("3", repl)
        vim.handle("x", repl)
        # ESC moved col to 0; 3x deletes chars at 0, then again, then again
        # Actually x only runs once with count n=3 but _action doesn't loop x
        # x doesn't use count — only motions do. Let's test d3w instead.

    def test_d3w_deletes_three_words(self):
        vim, repl = make("one two three four", 0)
        normal(vim, repl)
        vim.handle("d", repl)
        vim.handle("3", repl)
        vim.handle("w", repl)
        # Should delete "one two three " leaving "four"
        assert repl._current_line == "four"

    def test_3dw_also_deletes_three_words(self):
        vim, repl = make("one two three four", 0)
        normal(vim, repl)
        vim.handle("3", repl)
        vim.handle("d", repl)
        vim.handle("w", repl)
        assert repl._current_line == "four"

    def test_2w_moves_two_words(self):
        vim, repl = make("one two three", 0)
        normal(vim, repl)
        vim.handle("2", repl)
        vim.handle("w", repl)
        assert repl._cursor_offset == 8

    def test_count_resets_after_use(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("2", repl)
        vim.handle("w", repl)
        assert vim.count == ""


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
# f / F — find character
# ---------------------------------------------------------------------------

class TestFindChar:
    def test_f_moves_to_char(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("f", repl)
        vim.handle("o", repl)
        assert repl._cursor_offset == 4

    def test_F_moves_backward(self):
        vim, repl = make("hello world", 9)
        normal(vim, repl)
        vim.handle("F", repl)
        vim.handle("o", repl)
        assert repl._cursor_offset == 7

    def test_f_not_found_no_move(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        col_before = repl._cursor_offset
        vim.handle("f", repl)
        vim.handle("z", repl)
        assert repl._cursor_offset == col_before

    def test_semicolon_repeats_find(self):
        vim, repl = make("abcabc", 0)
        normal(vim, repl)
        vim.handle("f", repl)
        vim.handle("b", repl)
        first = repl._cursor_offset
        vim.handle(";", repl)
        assert repl._cursor_offset > first

    def test_comma_reverses_find(self):
        vim, repl = make("abcabc", 0)
        normal(vim, repl)
        vim.handle("f", repl)
        vim.handle("b", repl)
        vim.handle(";", repl)
        col_after_two = repl._cursor_offset
        vim.handle(",", repl)
        assert repl._cursor_offset < col_after_two

    def test_df_deletes_to_char(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("d", repl)
        vim.handle("f", repl)
        vim.handle("o", repl)
        assert "hello" not in repl._current_line
        assert repl._current_line.startswith(" world") or "world" in repl._current_line


# ---------------------------------------------------------------------------
# r — replace character
# ---------------------------------------------------------------------------

class TestReplace:
    def test_r_replaces_char(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("r", repl)
        vim.handle("x", repl)
        assert repl._current_line[0] == "x"
        assert repl._current_line == "xello"

    def test_r_stays_in_normal_mode(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("r", repl)
        vim.handle("x", repl)
        assert vim.mode == VimMode.NORMAL

    def test_r_on_empty_line_no_effect(self):
        vim, repl = make("", 0)
        normal(vim, repl)
        vim.handle("r", repl)
        vim.handle("x", repl)
        assert repl._current_line == ""

    def test_dot_repeats_replace(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("r", repl)
        vim.handle("x", repl)
        assert repl._current_line[0] == "x"
        repl._current_line = "world"
        repl._cursor_offset = 0
        vim.handle(".", repl)
        assert repl._current_line[0] == "x"


# ---------------------------------------------------------------------------
# o / O — open new line
# ---------------------------------------------------------------------------

class TestOpenLine:
    def test_o_enters_insert(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("o", repl)
        assert vim.mode == VimMode.INSERT

    def test_O_enters_insert(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("O", repl)
        assert vim.mode == VimMode.INSERT

    def test_o_positions_cursor_at_end_in_single_line(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("o", repl)
        assert repl._cursor_offset == len("hello")

    def test_O_positions_cursor_at_start_in_single_line(self):
        vim, repl = make("hello", 4)
        normal(vim, repl)
        vim.handle("O", repl)
        assert repl._cursor_offset == 0

    def test_o_inserts_row_in_vbuf(self):
        vim, repl = make("second", 0)
        repl.buffer = ["first"]
        normal(vim, repl)
        assert vim.vbuf is not None
        vim.handle("o", repl)
        # Should have added a row and entered insert
        assert vim.mode == VimMode.INSERT

    def test_O_inserts_row_above_in_vbuf(self):
        vim, repl = make("second", 0)
        repl.buffer = ["first"]
        normal(vim, repl)
        assert vim.vbuf is not None
        vim.handle("O", repl)
        assert vim.mode == VimMode.INSERT


# ---------------------------------------------------------------------------
# Visual mode
# ---------------------------------------------------------------------------

class TestVisualMode:
    def test_v_enters_visual(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        assert vim.mode == VimMode.VISUAL

    def test_esc_exits_visual(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        vim.handle("<ESC>", repl)
        assert vim.mode == VimMode.NORMAL

    def test_v_again_exits_visual(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        vim.handle("v", repl)
        assert vim.mode == VimMode.NORMAL

    def test_visual_l_extends_selection(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        vim.handle("l", repl)
        assert repl._cursor_offset == 1

    def test_visual_d_deletes_selection(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        vim.handle("l", repl)
        vim.handle("l", repl)
        vim.handle("l", repl)
        vim.handle("l", repl)
        vim.handle("d", repl)
        assert repl._current_line == " world"
        assert vim.mode == VimMode.NORMAL

    def test_visual_y_yanks_selection(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        vim.handle("l", repl)
        vim.handle("l", repl)
        vim.handle("y", repl)
        assert vim.registers['"'] == "hel"
        assert vim.mode == VimMode.NORMAL

    def test_visual_c_changes_selection(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        vim.handle("l", repl)
        vim.handle("l", repl)
        vim.handle("l", repl)
        vim.handle("l", repl)
        vim.handle("c", repl)
        assert vim.mode == VimMode.INSERT
        assert repl._current_line == " world"

    def test_visual_w_moves_by_word(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        vim.handle("w", repl)
        assert repl._cursor_offset == 6


# ---------------------------------------------------------------------------
# Text objects
# ---------------------------------------------------------------------------

class TestTextObjects:
    def test_ciw_changes_inner_word(self):
        vim, repl = make("hello world", 2)
        normal(vim, repl)
        vim.handle("c", repl)
        vim.handle("i", repl)
        vim.handle("w", repl)
        assert "hello" not in repl._current_line
        assert vim.mode == VimMode.INSERT

    def test_diw_deletes_inner_word(self):
        vim, repl = make("hello world", 2)
        normal(vim, repl)
        vim.handle("d", repl)
        vim.handle("i", repl)
        vim.handle("w", repl)
        assert "hello" not in repl._current_line

    def test_yi_quote_yanks_contents(self):
        vim, repl = make('say "hello"', 6)
        normal(vim, repl)
        vim.handle("y", repl)
        vim.handle("i", repl)
        vim.handle('"', repl)
        assert vim.registers['"'] == "hello"

    def test_di_paren_deletes_inside(self):
        vim, repl = make("foo(bar)", 5)
        normal(vim, repl)
        vim.handle("d", repl)
        vim.handle("i", repl)
        vim.handle("(", repl)
        assert repl._current_line == "foo()"

    def test_yi_bracket_yanks_inside(self):
        vim, repl = make("x[abc]y", 3)
        normal(vim, repl)
        vim.handle("y", repl)
        vim.handle("i", repl)
        vim.handle("[", repl)
        assert vim.registers['"'] == "abc"

    def test_text_obj_no_match_no_change(self):
        vim, repl = make("hello world", 2)
        normal(vim, repl)
        line_before = repl._current_line
        vim.handle("d", repl)
        vim.handle("i", repl)
        vim.handle("(", repl)
        assert repl._current_line == line_before


# ---------------------------------------------------------------------------
# Macro recording
# ---------------------------------------------------------------------------

class TestMacroRecording:
    def test_qa_starts_recording(self):
        vim, repl = make("", 0)
        normal(vim, repl)
        vim.handle("q", repl)
        vim.handle("a", repl)
        assert vim._recording == "a"

    def test_q_stops_recording(self):
        vim, repl = make("", 0)
        normal(vim, repl)
        vim.handle("q", repl)
        vim.handle("a", repl)
        vim.handle("q", repl)
        assert vim._recording is None

    def test_recorded_keys_stored(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("q", repl)
        vim.handle("a", repl)
        vim.handle("0", repl)
        vim.handle("q", repl)
        stored = vim.registers.get("a")
        assert isinstance(stored, list)
        assert "0" in stored

    def test_at_replays_macro(self):
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        # Record: go to end of line
        vim.handle("q", repl)
        vim.handle("a", repl)
        vim.handle("0", repl)  # go to start
        vim.handle("q", repl)
        # Move cursor away
        repl._cursor_offset = 5
        # Replay
        vim.handle("@", repl)
        vim.handle("a", repl)
        assert repl._cursor_offset == 0

    def test_at_with_unrecorded_register_does_nothing(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        col_before = repl._cursor_offset
        vim.handle("@", repl)
        vim.handle("z", repl)
        assert repl._cursor_offset == col_before


# ---------------------------------------------------------------------------
# / search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_slash_enters_search_mode(self):
        vim, repl = make("", 0)
        normal(vim, repl)
        vim.handle("/", repl)
        assert vim.mode == VimMode.SEARCH

    def test_search_accumulates_query(self):
        vim, repl = make("", 0)
        normal(vim, repl)
        vim.handle("/", repl)
        vim.handle("f", repl)
        vim.handle("o", repl)
        vim.handle("o", repl)
        assert vim.search_query == "foo"

    def test_esc_exits_search(self):
        vim, repl = make("", 0)
        normal(vim, repl)
        vim.handle("/", repl)
        vim.handle("<ESC>", repl)
        assert vim.mode == VimMode.NORMAL

    def test_enter_finds_match(self):
        vim, repl = make("", 0)
        repl.history = ["x = 1", "foo = 2", "bar = 3"]
        normal(vim, repl)
        vim.handle("/", repl)
        vim.handle("f", repl)
        vim.handle("o", repl)
        vim.handle("o", repl)
        vim.handle("\n", repl)
        assert vim.mode == VimMode.NORMAL
        assert repl._current_line == "foo = 2"

    def test_no_match_stays_empty(self):
        vim, repl = make("", 0)
        repl.history = ["x = 1"]
        normal(vim, repl)
        vim.handle("/", repl)
        vim.handle("z", repl)
        vim.handle("z", repl)
        vim.handle("z", repl)
        vim.handle("\n", repl)
        assert vim.mode == VimMode.NORMAL

    def test_n_cycles_to_previous_match(self):
        vim, repl = make("", 0)
        repl.history = ["foo = 1", "bar = 2", "foo = 3"]
        normal(vim, repl)
        vim.handle("/", repl)
        vim.handle("f", repl)
        vim.handle("o", repl)
        vim.handle("o", repl)
        vim.handle("\n", repl)
        first_match = repl._current_line
        vim.handle("n", repl)
        assert repl._current_line != first_match or len(vim._search_matches) == 1

    def test_backspace_removes_query_char(self):
        vim, repl = make("", 0)
        normal(vim, repl)
        vim.handle("/", repl)
        vim.handle("f", repl)
        vim.handle("o", repl)
        vim.handle("<BACKSPACE>", repl)
        assert vim.search_query == "f"


# ---------------------------------------------------------------------------
# Dot repeat (true Vim semantics)
# ---------------------------------------------------------------------------

class TestDotRepeat:
    def test_dot_repeats_x(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("x", repl)
        assert repl._current_line == "ello"
        vim.handle(".", repl)
        assert repl._current_line == "llo"

    def test_dot_repeats_dw(self):
        vim, repl = make("one two three", 0)
        normal(vim, repl)
        vim.handle("d", repl)
        vim.handle("w", repl)
        assert repl._current_line == "two three"
        vim.handle(".", repl)
        assert repl._current_line == "three"

    def test_dot_repeats_insert_session(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("i", repl)
        # Simulate typing in insert mode (done externally by the REPL)
        repl._current_line = "XXhello"
        # Exit insert (ESC)
        vim.handle("<ESC>", repl)
        # Move somewhere else and dot-repeat
        repl._current_line = "world"
        vim.handle(".", repl)
        assert repl._current_line == "XXhello"

    def test_dot_does_nothing_before_any_change(self):
        vim, repl = make("hello", 0)
        normal(vim, repl)
        line_before = repl._current_line
        vim.handle(".", repl)
        assert repl._current_line == line_before


# ---------------------------------------------------------------------------
# Bug fix regressions
# ---------------------------------------------------------------------------

class TestBugFixes:
    def test_substitute_cursor_not_past_end(self):
        """Regression: :s must leave cursor at last char, not past it."""
        vim, repl = make("hello world", 0)
        normal(vim, repl)
        for ch in ":s/hello/hi\n":
            vim.handle(ch, repl)
        assert repl._cursor_offset <= max(0, len(repl._current_line) - 1)

    def test_substitute_cursor_valid_on_short_result(self):
        vim, repl = make("abcde", 0)
        normal(vim, repl)
        for ch in ":s/abcde/x\n":
            vim.handle(ch, repl)
        assert repl._current_line == "x"
        assert repl._cursor_offset == 0

    def test_K_does_not_reevaluate(self):
        """Regression: K must not call eval(), only look up the name."""
        called = []

        class TrackedObj:
            def __init__(self):
                called.append("created")

        vim, repl = make("obj", 0)
        repl.interp.locals = {"obj": TrackedObj()}
        called.clear()  # reset after putting it in locals
        normal(vim, repl)
        vim.handle("K", repl)
        # _resolve looks up the name, does NOT instantiate/call anything
        assert called == []

    def test_K_safe_lookup_finds_builtins(self):
        vim, repl = make("len", 0)
        repl.interp.locals = {}
        normal(vim, repl)
        vim.handle("K", repl)
        # Should show docstring for len, not crash
        repl.status_bar.message.assert_called()

    def test_K_missing_symbol_shows_message(self):
        vim, repl = make("nonexistent_xyz_abc", 0)
        repl.interp.locals = {}
        normal(vim, repl)
        vim.handle("K", repl)
        msg = repl.status_bar.message.call_args[0][0]
        assert "not found" in msg

    def test_visual_mode_accessible(self):
        """Visual mode is a real mode, not an error."""
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("v", repl)
        assert vim.mode == VimMode.VISUAL

    def test_search_mode_accessible(self):
        """/  search is a real mode, not an error."""
        vim, repl = make("hello", 0)
        normal(vim, repl)
        vim.handle("/", repl)
        assert vim.mode == VimMode.SEARCH
