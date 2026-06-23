import pydoc
from types import TracebackType
from typing import Literal

from .. import _internal


class NopPydocPager:
    def __enter__(self):
        self._orig_pager = pydoc.pager
        pydoc.pager = self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        pydoc.pager = self._orig_pager
        return False

    def __call__(self, text):
        return None

class _Helper(_internal._Helper):
    def __init__(self, repl=None):
        self._repl = repl
        pydoc.pager = self.pager

        super().__init__()

    def pager(self, output, title=""):
        self._repl.pager(output, title)

    def __call__(self, *args, **kwargs):
        if self._repl.reevaluating:
            with NopPydocPager():
                return super().__call__(*args, **kwargs)
        else:
            return super().__call__(*args, **kwargs)

