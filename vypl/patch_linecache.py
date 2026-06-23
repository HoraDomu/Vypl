import linecache
from typing import Any


class VyplLinecache(dict):
    """Replaces the cache dict in the standard-library linecache module,
    to also remember (in an unerasable way) vypl console input."""

    def __init__(
        self,
        vypl_history: None | (list[tuple[int, None, list[str], str]]) = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.vypl_history = vypl_history or []

    def is_vypl_filename(self, fname: Any) -> bool:
        return isinstance(fname, str) and fname.startswith("<vypl-input-")

    def get_vypl_history(self, key: str) -> tuple[int, None, list[str], str]:
        """Given a filename provided by remember_vypl_input,
        returns the associated source string."""
        try:
            idx = int(key.split("-")[2][:-1])
            return self.vypl_history[idx]
        except (IndexError, ValueError):
            raise KeyError

    def remember_vypl_input(self, source: str) -> str:
        """Remembers a string of source code, and returns
        a fake filename to use to retrieve it later."""
        filename = f"<vypl-input-{len(self.vypl_history)}>"
        self.vypl_history.append(
            (len(source), None, source.splitlines(True), filename)
        )
        return filename

    def get(self, key: Any, default: Any | None = None) -> Any:
        if self.is_vypl_filename(key):
            return self.get_vypl_history(key)
        return super().get(key, default)

    def __getitem__(self, key: Any) -> Any:
        if self.is_vypl_filename(key):
            return self.get_vypl_history(key)
        return super().__getitem__(key)

    def __contains__(self, key: Any) -> bool:
        if self.is_vypl_filename(key):
            try:
                self.get_vypl_history(key)
                return True
            except KeyError:
                return False
        return super().__contains__(key)

    def __delitem__(self, key: Any) -> None:
        if not self.is_vypl_filename(key):
            super().__delitem__(key)

def _vypl_clear_linecache() -> None:
    if isinstance(linecache.cache, VyplLinecache):
        vypl_history = linecache.cache.vypl_history
    else:
        vypl_history = None
    linecache.cache = VyplLinecache(vypl_history)

linecache.cache = VyplLinecache(None, linecache.cache)
linecache.clearcache = _vypl_clear_linecache

def filename_for_console_input(code_string: str) -> str:
    """Remembers a string of source code, and returns
    a fake filename to use to retrieve it later."""
    if isinstance(linecache.cache, VyplLinecache):
        return linecache.cache.remember_vypl_input(code_string)
    else:
        return "<input>"
