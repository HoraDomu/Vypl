from typing import Any, TextIO
from collections.abc import MutableMapping, Iterable
from pygments.formatter import Formatter
from pygments.token import (
    _TokenType,
    Keyword,
    Name,
    Comment,
    String,
    Error,
    Number,
    Operator,
    Token,
    Whitespace,
    Literal,
    Punctuation,
)

"""These format strings are pretty ugly.
\x01 represents a colour marker, which
    can be preceded by one or two of
    the following letters:
    k, r, g, y, b, m, c, w, d
    Which represent:
    blacK, Red, Green, Yellow, Blue, Magenta,
    Cyan, White, Default
    e.g. \x01y for yellow,
        \x01gb for green on blue background

\x02 represents the bold attribute

\x03 represents the start of the actual
    text that is output (in this case it's
    a %s for substitution)

\x04 represents the end of the string; this is
    necessary because the strings are all joined
    together at the end so the parser needs them
    as delimiters

"""

Parenthesis = Token.Punctuation.Parenthesis

theme_map = {
    Keyword: "keyword",
    Name: "name",
    Comment: "comment",
    String: "string",
    Literal: "string",
    Error: "error",
    Number: "number",
    Token.Literal.Number.Float: "number",
    Operator: "operator",
    Punctuation: "punctuation",
    Token: "token",
    Whitespace: "background",
    Parenthesis: "paren",
    Parenthesis.UnderCursor: "operator",
}

class VyplFormatter(Formatter):
    """This is the custom formatter for vypl.
    Its format() method receives the tokensource
    and outfile params passed to it from the
    Pygments highlight() method and slops
    them into the appropriate format string
    as defined above, then writes to the outfile
    object the final formatted string.

    See the Pygments source for more info; it's pretty
    straightforward."""

    def __init__(
        self, color_scheme: MutableMapping[str, str], **options: Any
    ) -> None:
        self.f_strings = {}
        for k, v in theme_map.items():
            self.f_strings[k] = f"\x01{color_scheme[v]}"
            if k is Parenthesis:
                self.f_strings[k] += "I"
        super().__init__(**options)

    def format(
        self,
        tokensource: Iterable[MutableMapping[_TokenType, str]],
        outfile: TextIO,
    ) -> None:
        o: str = ""
        for token, text in tokensource:
            if text == "\n":
                continue

            while token not in self.f_strings:
                if token.parent is None:
                    break
                else:
                    token = token.parent
            o += f"{self.f_strings[token]}\x03{text}\x04"
        outfile.write(o.rstrip())

