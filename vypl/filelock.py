from types import TracebackType
from typing import IO, Literal


class BaseLock:
    """Base class for file locking"""

    def __init__(self) -> None:
        self.locked = False

    def acquire(self) -> None:
        pass

    def release(self) -> None:
        pass

    def __enter__(self) -> "BaseLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        if self.locked:
            self.release()
        return False

    def __del__(self) -> None:
        if self.locked:
            self.release()

try:
    import errno
    import fcntl

    class UnixFileLock(BaseLock):
        """Simple file locking for Unix using fcntl"""

        def __init__(self, fileobj, mode: int = 0) -> None:
            super().__init__()
            self.fileobj = fileobj
            self.mode = mode | fcntl.LOCK_EX

        def acquire(self) -> None:
            try:
                fcntl.flock(self.fileobj, self.mode)
                self.locked = True
            except OSError as e:
                if e.errno != errno.ENOLCK:
                    raise e

        def release(self) -> None:
            self.locked = False
            fcntl.flock(self.fileobj, fcntl.LOCK_UN)

    has_fcntl = True
except ImportError:
    has_fcntl = False

try:
    import msvcrt
    import os

    class WindowsFileLock(BaseLock):
        """Simple file locking for Windows using msvcrt"""

        def __init__(self, filename: str) -> None:
            super().__init__()
            self.filename = f"{filename}.lock"
            self.fileobj = -1

        def acquire(self) -> None:
            self.fileobj = os.open(
                self.filename, os.O_RDWR | os.O_CREAT | os.O_TRUNC
            )
            msvcrt.locking(self.fileobj, msvcrt.LK_NBLCK, 1)

            self.locked = True

        def release(self) -> None:
            self.locked = False

            msvcrt.locking(self.fileobj, msvcrt.LK_UNLCK, 1)
            os.close(self.fileobj)
            self.fileobj = -1

            try:
                os.remove(self.filename)
            except OSError:
                pass

    has_msvcrt = True
except ImportError:
    has_msvcrt = False

def FileLock(
    fileobj: IO, mode: int = 0, filename: str | None = None
) -> BaseLock:
    if has_fcntl:
        return UnixFileLock(fileobj, mode)
    elif has_msvcrt and filename is not None:
        return WindowsFileLock(filename)
    return BaseLock()

