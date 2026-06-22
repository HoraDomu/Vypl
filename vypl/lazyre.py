import re
from collections.abc import Iterator
from functools import cached_property
from re import Pattern, Match

class LazyReCompile:
    """Compile regular expressions on first use

    This class allows one to store regular expressions and compiles them on
    first use."""

    def __init__(self, regex: str, flags: int = 0) -> None:
        self.regex = regex
        self.flags = flags

    @cached_property
    def compiled(self) -> Pattern[str]:
        return re.compile(self.regex, self.flags)

    def finditer(self, *args, **kwargs) -> Iterator[Match[str]]:
        return self.compiled.finditer(*args, **kwargs)

    def search(self, *args, **kwargs) -> Match[str] | None:
        return self.compiled.search(*args, **kwargs)

    def match(self, *args, **kwargs) -> Match[str] | None:
        return self.compiled.match(*args, **kwargs)

    def sub(self, *args, **kwargs) -> str:
        return self.compiled.sub(*args, **kwargs)
