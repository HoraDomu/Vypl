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
| `x` | Delete char under cursor |
| `d` `c` `y` + motion | Delete / change / yank |
| `dd` `cc` `yy` | Operate on whole line |
| `p` `P` | Paste after / before cursor |
| `"a` … `"z` | Named registers |
| `K` | Inspect symbol under cursor |
| `.` | Re-run last expression |
| `u` | Undo |

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
