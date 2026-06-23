import string
from typing import Generic, TypeVar

T = TypeVar("T")

class KeyMap(Generic[T]):
    def __init__(self, default: T) -> None:
        self.map: dict[str, T] = {}
        self.default = default

    def __getitem__(self, key: str) -> T:
        if not key:
            return self.default
        elif key in self.map:
            return self.map[key]
        else:
            raise KeyError(
                f"Configured keymap ({key}) does not exist in vypl.keys"
            )

    def __delitem__(self, key: str) -> None:
        del self.map[key]

    def __setitem__(self, key: str, value: T) -> None:
        self.map[key] = value

cli_key_dispatch: KeyMap[tuple[str, ...]] = KeyMap(tuple())
urwid_key_dispatch = KeyMap("")

for c in string.ascii_lowercase:
    cli_key_dispatch[f"C-{c}"] = (
        chr(string.ascii_lowercase.index(c) + 1),
        f"^{c.upper()}",
    )

for c in string.ascii_lowercase:
    urwid_key_dispatch[f"C-{c}"] = f"ctrl {c}"
    urwid_key_dispatch[f"M-{c}"] = f"meta {c}"

cli_key_dispatch["C-["] = (chr(27), "^[")
cli_key_dispatch["C-\\"] = (chr(28), "^\\")
cli_key_dispatch["C-]"] = (chr(29), "^]")
cli_key_dispatch["C-^"] = (chr(30), "^^")
cli_key_dispatch["C-_"] = (chr(31), "^_")

for x in range(1, 13):
    cli_key_dispatch[f"F{x}"] = (f"KEY_F({x})",)

for x in range(1, 13):
    urwid_key_dispatch[f"F{x}"] = f"f{x}"
