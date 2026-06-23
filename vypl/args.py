import argparse
import code
import importlib.util
import logging
import os
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Never

from . import __version__
from .config import Config, default_config_path
from .translations import _

logger = logging.getLogger(__name__)


class ArgumentParserFailed(ValueError):
    pass


class RaisingArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise ArgumentParserFailed()


def version_banner(base: str = "vypl") -> str:
    return _("{} version {} on top of Python {} {}").format(
        base,
        __version__,
        sys.version.split()[0],
        sys.executable,
    )


def log_version(module: ModuleType, name: str) -> None:
    logger.info("%s: %s", name, module.__version__ if hasattr(module, "__version__") else "unknown version")


Options = tuple[str, str, Callable[[argparse._ArgumentGroup], None]]


def parse(
    args: list[str] | None,
    extras: Options | None = None,
    ignore_stdin: bool = False,
) -> tuple[Config, argparse.Namespace, list[str]]:
    if args is None:
        args = sys.argv[1:]

    parser = RaisingArgumentParser(
        usage=_(
            "Usage: %(prog)s [options] [file [args]]\n"
            "NOTE: If vypl sees an argument it does "
            "not know, execution falls back to the "
            "regular Python interpreter."
        )
    )
    parser.add_argument(
        "--config",
        default=default_config_path(),
        type=Path,
        help=_("Use CONFIG instead of default config file."),
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help=_("Drop to vypl shell after running file instead of exiting."),
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help=_("Don't print version banner."),
    )
    parser.add_argument(
        "--version",
        "-V",
        action="store_true",
        help=_("Print version and exit."),
    )
    parser.add_argument(
        "--log-level",
        "-l",
        choices=("debug", "info", "warning", "error", "critical"),
        default="error",
        help=_("Set log level for logging"),
    )
    parser.add_argument(
        "--log-output",
        "-L",
        help=_("Log output file"),
    )

    if extras is not None:
        extras_group = parser.add_argument_group(extras[0], extras[1])
        extras[2](extras_group)

    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help=_(
            "File to execute and additional arguments passed on to the executed script."
        ),
    )

    try:
        options = parser.parse_args(args)
    except ArgumentParserFailed:
        os.execv(sys.executable, [sys.executable] + args)

    if options.version:
        print(version_banner())
        raise SystemExit

    if not ignore_stdin and not (sys.stdin.isatty() and sys.stdout.isatty()):
        os.execv(sys.executable, [sys.executable] + args)

    vypl_logger = logging.getLogger("vypl")
    curtsies_logger = logging.getLogger("curtsies")
    vypl_logger.setLevel(options.log_level.upper())
    curtsies_logger.setLevel(options.log_level.upper())
    if options.log_output:
        handler = logging.FileHandler(filename=options.log_output)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s: %(name)s: %(levelname)s: %(message)s"
            )
        )
        vypl_logger.addHandler(handler)
        curtsies_logger.addHandler(handler)
        vypl_logger.propagate = curtsies_logger.propagate = False
    else:
        vypl_logger.addHandler(logging.NullHandler())
        curtsies_logger.addHandler(logging.NullHandler())

    import cwcwidth
    import greenlet
    import pygments
    import requests
    import xdg

    logger.info("Starting vypl %s", __version__)
    logger.info("Python %s: %s", sys.executable, sys.version_info)
    try:
        import curtsies

        log_version(curtsies, "curtsies")
    except ImportError:
        logger.info("curtsies: not available")
    log_version(cwcwidth, "cwcwidth")
    log_version(greenlet, "greenlet")
    log_version(pygments, "pygments")
    log_version(xdg, "pyxdg")
    log_version(requests, "requests")

    try:
        import pyperclip

        log_version(pyperclip, "pyperclip")
    except ImportError:
        logger.info("pyperclip: not available")
    try:
        import jedi

        log_version(jedi, "jedi")
    except ImportError:
        logger.info("jedi: not available")
    try:
        import importlib.util as _ilu

        if _ilu.find_spec("watchdog") is not None:
            logger.info("watchdog: available")
        else:
            logger.info("watchdog: not available")
    except Exception:
        logger.info("watchdog: not available")

    logger.info("environment:")
    for key, value in sorted(os.environ.items()):
        if key.startswith("LC") or key.startswith("LANG") or key == "TERM":
            logger.info("%s: %s", key, value)

    return Config(options.config), options, options.args


def exec_code(
    interpreter: code.InteractiveInterpreter, args: list[str]
) -> None:
    try:
        with open(args[0]) as sourcefile:
            source = sourcefile.read()
    except OSError as e:
        print(f"vypl: can't open file '{args[0]}: {e}", file=sys.stderr)
        raise SystemExit(e.errno)
    old_argv, sys.argv = sys.argv, args
    sys.path.insert(0, os.path.abspath(os.path.dirname(args[0])))
    spec = importlib.util.spec_from_loader("__main__", loader=None)
    assert spec
    mod = importlib.util.module_from_spec(spec)
    sys.modules["__main__"] = mod
    interpreter.locals.update(mod.__dict__)
    interpreter.locals["__file__"] = args[0]
    interpreter.runsource(source, args[0], "exec")
    sys.argv = old_argv
