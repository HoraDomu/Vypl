import os.path
from typing import Any

__version__ = "0.6.4"
package_dir = os.path.abspath(os.path.dirname(__file__))


def embed(locals_=None, args=None, banner=None) -> Any:
    if args is None:
        args = ["-i", "-q"]

    from .curtsies import main

    return main(args, locals_, banner)
