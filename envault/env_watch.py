"""Watch a vault file for changes and notify the user."""

import time
import os
from dataclasses import dataclass, field
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when a watch operation fails."""


@dataclass
class WatchEvent:
    """Represents a detected change in a vault file."""

    path: str
    previous_mtime: float
    current_mtime: float
    previous_size: int
    current_size: int

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "previous_mtime": self.previous_mtime,
            "current_mtime": self.current_mtime,
            "previous_size": self.previous_size,
            "current_size": self.current_size,
        }

    def __repr__(self) -> str:
        return (
            f"WatchEvent(path={self.path!r}, "
            f"mtime={self.previous_mtime}->{self.current_mtime}, "
            f"size={self.previous_size}->{self.current_size})"
        )


def _stat(path: str) -> tuple[float, int]:
    """Return (mtime, size) for the given path."""
    try:
        st = os.stat(path)
        return st.st_mtime, st.st_size
    except FileNotFoundError:
        raise WatchError(f"Vault file not found: {path}")


def watch_vault(
    path: str,
    callback: Callable[[WatchEvent], None],
    interval: float = 1.0,
    timeout: Optional[float] = None,
    _stop_flag: Optional[Callable[[], bool]] = None,
) -> None:
    """Poll the vault file for changes and invoke callback on each change.

    Args:
        path: Path to the vault file to watch.
        callback: Called with a WatchEvent whenever the file changes.
        interval: Polling interval in seconds.
        timeout: Maximum total watch time in seconds (None = forever).
        _stop_flag: Optional callable returning True to stop watching (for tests).
    """
    if interval <= 0:
        raise WatchError("interval must be positive")

    last_mtime, last_size = _stat(path)
    start = time.monotonic()

    while True:
        time.sleep(interval)

        if timeout is not None and (time.monotonic() - start) >= timeout:
            break

        if _stop_flag is not None and _stop_flag():
            break

        current_mtime, current_size = _stat(path)
        if current_mtime != last_mtime or current_size != last_size:
            event = WatchEvent(
                path=path,
                previous_mtime=last_mtime,
                current_mtime=current_mtime,
                previous_size=last_size,
                current_size=current_size,
            )
            last_mtime, last_size = current_mtime, current_size
            callback(event)
