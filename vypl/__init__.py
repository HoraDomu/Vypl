import os.path
from typing import Any

try:
    from ._version import __version__ as version
except ImportError:
    version = "unknown"

__version__ = version
package_dir = os.path.abspath(os.path.dirname(__file__))


def embed(locals_=None, args=None, banner=None) -> Any:
    if args is None:
        args = ["-i", "-q"]

    from .curtsies import main

    return main(args, locals_, banner)
