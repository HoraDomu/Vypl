<div align="center">

<img src="https://img.shields.io/badge/VYPL-A%20Python%20REPL%20with%20Vim%20Keybinds-white?style=for-the-badge&labelColor=0d1117&color=2f81f7" alt="Vypl" />

<h3>A Python REPL with Vim Keybinds</h3>

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Vypl-2f81f7?style=flat-square&labelColor=0d1117" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.11+-2f81f7?style=flat-square&labelColor=0d1117" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20WSL-2f81f7?style=flat-square&labelColor=0d1117" alt="Platform" />
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square&labelColor=0d1117" alt="Code style: black" /></a>
</p>

</div>

---

Vypl is a terminal Python REPL built around the idea that your editor keybinds shouldn't disappear the moment you open an interactive session. It runs in the terminal, gives you a real Python environment with syntax highlighting and smart autocompletion, and is being built to work the way Vim users think modal, keyboard-driven, and fast.

## Features

| Feature | Status |
|---|---|
| Syntax highlighting | ✅ |
| Autocompletion (simple + Jedi) | ✅ |
| Function signature display | ✅ |
| Bracket / paren matching | ✅ |
| Persistent history + reverse search | ✅ |
| Multi-line editing with auto-indent | ✅ |
| Open session in external editor | ✅ |
| Auto-reload on file change | ✅ |
| Color themes | ✅ |
| Vim normal / insert mode | 🔧 in progress |
| Vim motions (`w`, `b`, `e`, `0`, `$`) | 🔧 in progress |
| Vim operators (`d`, `c`, `y`, `p`) | 🔧 in progress |
| History navigation with `j` / `k` | 🔧 in progress |

## Install

```bash
pip install vypl
```

Or from source:

```bash
git clone https://github.com/dommcpro/Vypl
cd Vypl
pip install -e .
```

## Usage

```bash
vypl
```
## Configuration

Vypl reads its config from `~/.config/vypl/config`. Themes live in the same directory. A default config will be generated on first run.

## Platform

Vypl requires a Unix terminal. On Windows, run it inside WSL.

## Contributing

See [LICENSE](LICENSE) contributions are welcome, attribution is required, and modifications must be contributed back.
