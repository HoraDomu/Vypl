import pydoc
import sys

from .pager import page

pydoc.pager = page

class _Helper:
    def __init__(self) -> None:
        if hasattr(pydoc.Helper, "output"):
            self.helper = pydoc.Helper(sys.stdin, None)
        else:
            self.helper = pydoc.Helper(sys.stdin, sys.stdout)

    def __repr__(self) -> str:
        return (
            "Type help() for interactive help, "
            "or help(object) for help about object."
        )

    def __call__(self, *args, **kwargs) -> None:
        self.helper(*args, **kwargs)

_help = _Helper()

