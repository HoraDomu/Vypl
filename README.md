<div align="center">

<img src="https://img.shields.io/badge/VYPL-A%20Python%20REPL%20with%20Vim%20Keybinds-00ff00?style=for-the-badge&labelColor=000000&color=000000" alt="Vypl" />

<h3>A Python REPL with Vim Keybinds</h3>

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Vypl-00ff00?style=flat-square&labelColor=111111" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.11+-00ff00?style=flat-square&labelColor=111111" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20WSL-00ff00?style=flat-square&labelColor=111111" alt="Platform" />
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square&labelColor=111111" alt="Code style: black" /></a>
</p>

</div>

---

Vypl is a terminal Python REPL built around the idea that your editor keybinds shouldn't disappear the moment you open an interactive session. It runs in the terminal, gives you a real Python environment with syntax highlighting and smart autocompletion, and is being built to work the way Vim users think — modal, keyboard-driven, and fast.

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

Optional extras:

```bash
pip install vypl[jedi]       # better autocompletion
pip install vypl[clipboard]  # system clipboard support
pip install vypl[watch]      # auto-reload on file change
```

## Configuration

Vypl reads its config from `~/.config/vypl/config`. Themes live in the same directory. A default config will be generated on first run.

## Platform

Vypl requires a Unix terminal. On Windows, run it inside WSL.

## Contributing

See [LICENSE](LICENSE) — contributions are welcome, attribution is required, and modifications must be contributed back.
