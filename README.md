<div align="center">

<img src="https://img.shields.io/badge/Vypl-Python%20REPL%20%E2%80%93%20Vim%20Keybinds-white?style=for-the-badge&labelColor=0d1117&color=2f81f7" alt="Vypl" />

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-2f81f7?style=flat-square&labelColor=0d1117" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.11+-2f81f7?style=flat-square&labelColor=0d1117" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20WSL-2f81f7?style=flat-square&labelColor=0d1117" alt="Platform" />
</p>
<a href="https://codecov.io/github/HoraDomu/Vypl">
  <img src="https://codecov.io/github/HoraDomu/Vypl/graph/badge.svg?token=S21MLJFZ19" alt="codecov" />
</a>

</div>

---

<div align="center">
  <img src="assets/demo.gif" alt="Vypl demo" />
</div>

---

Vypl is a terminal Python REPL built for Vim users. It gives you a real Python environment with syntax highlighting, smart autocompletion, and full modal editing — normal mode, motions, operators, named registers, and ex commands, all inside the REPL.

## Install

```bash
pip install vypl
```

Or from source:

```bash
git clone https://github.com/HoraDomu/Vypl
cd Vypl
pip install -e .
```

## Usage

```bash
vypl
```

## Vim Features

Press `ESC` to enter normal mode. Press `i`, `a`, `A`, or `I` to return to insert.

| Keybind | Action |
|---|---|
| `ESC` | Normal mode |
| `i` / `a` / `A` / `I` | Insert mode |
| `h` `j` `k` `l` | Move cursor / navigate history |
| `w` `b` `e` | Word motions |
| `0` `$` | Line start / end |
| `f{char}` / `F{char}` | Find character forward / backward |
| `;` / `,` | Repeat last find / reverse |
| `r{char}` | Replace character under cursor |
| `x` | Delete char under cursor |
| `d` `c` `y` + motion | Delete / change / yank |
| `dd` `cc` `yy` | Operate on whole line |
| `[count]op[count]motion` | e.g. `3dd`, `d3w`, `2x` |
| `p` `P` | Paste after / before cursor |
| `"a` … `"z` | Named registers |
| `v` | Visual mode — then `d` / `y` / `c` |
| `o` / `O` | Open new line below / above |
| `gg` / `G` | Jump to first / last line in buffer |
| `K` | Inspect symbol under cursor |
| `.` | Repeat last change |
| `u` | Undo |
| `q{a-z}` | Record macro into register |
| `@{a-z}` | Replay macro |
| `/` | Search history |
| `n` / `N` | Next / previous search match |

### Text Objects

In operator-pending mode (`d`, `c`, `y`), press `i` or `a` followed by a delimiter:

| Object | Description |
|---|---|
| `iw` / `aw` | Inner / around word |
| `i"` / `a"` | Inner / around double quotes |
| `i'` / `a'` | Inner / around single quotes |
| `i(` / `a(` | Inner / around parentheses |
| `i[` / `a[` | Inner / around brackets |
| `i{` / `a{` | Inner / around braces |

### Ex Commands

Type `:` in normal mode to enter command mode.

| Command | Action |
|---|---|
| `:w [file]` | Save session to file |
| `:r file.py` | Load and run a Python file |
| `:s/old/new/` | Substitute in current line |
| `:s/old/new/g` | Substitute all occurrences |
| `:history` | Search command history |
| `:clear` | Clear the screen |
| `:q` | Quit |

## Platform

Vypl requires a Unix terminal. On Linux and macOS, it runs natively. On Windows, use WSL or Docker.

## Running on Windows (Docker)

```bash
git clone https://github.com/HoraDomu/Vypl
cd Vypl
docker build -t vypl .
docker run -it vypl
```

## Contributing

Contributions are welcome. Open an issue or pull request on [GitHub](https://github.com/HoraDomu/Vypl). Vypl is licensed under GPL v3 — contributions must remain open source.

## Special Thanks

[bpython](https://bpython-interpreter.org/) provided the original REPL foundation. Vypl builds on that core with a complete Vim modal editing layer, a minimal aesthetic, and Docker support.
