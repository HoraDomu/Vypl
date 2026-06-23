import curses
import errno
import os
import pydoc
import shlex
import subprocess
import sys


def get_pager_command(default: str = "less -rf") -> list[str]:
    return shlex.split(os.environ.get("PAGER", default))

def page_internal(data: str) -> None:
    """A more than dumb pager function."""
    if hasattr(pydoc, "ttypager"):
        pydoc.ttypager(data)
    else:
        sys.stdout.write(data)

def page(data: str, use_internal: bool = False) -> None:
    command = get_pager_command()
    if not command or use_internal:
        page_internal(data)
    else:
        curses.endwin()
        try:
            popen = subprocess.Popen(command, stdin=subprocess.PIPE)
            assert popen.stdin is not None
            data_bytes = data.encode(sys.__stdout__.encoding, "replace")
            popen.stdin.write(data_bytes)
            popen.stdin.close()
        except OSError as e:
            if e.errno == errno.ENOENT:
                page_internal(data)
                return
            if e.errno != errno.EPIPE:
                raise
        while True:
            try:
                popen.wait()
            except OSError as e:
                if e.errno != errno.EINTR:
                    raise
            else:
                break
        curses.doupdate()

