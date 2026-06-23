"""Positional file writer for concurrent chunked downloads.

All writes go through a single OS file descriptor using seek+write pairs
serialized by a threading lock. This is intentionally simple and correct:

* No in-memory buffering layer, so there is no zero-padding of gaps and no
  coalescing of unrelated chunks into one dirty region.
* No mixing of ``aiofiles`` (which wraps a Python buffered IO object) with
  direct ``os.write`` on the underlying fd, which would desynchronize the
  buffer and corrupt data.
* Writes are dispatched to a thread executor, so the lock guarantees the
  seek+write pair executes atomically even when several chunks write
  concurrently.

The target file is preallocated with ``ftruncate`` (a sparse allocation on
every modern filesystem) so that positional writes to any offset are valid
before the chunk owning that offset has run.
"""

from __future__ import annotations

import asyncio
import os
import threading
from pathlib import Path


class FileWriter:
    """Race-free positional writer backed by a raw OS file descriptor."""

    def __init__(self, file_path: Path, file_size: int = -1, *, resume: bool = False) -> None:
        self.file_path = file_path
        self.file_size = file_size
        self._resume = resume
        self._fd: int | None = None
        self._lock = threading.Lock()

    async def open(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # A fresh (non-resume) start must not inherit bytes left over in a stale
        # .part file: ftruncate only adjusts length, it does not zero existing
        # content. Remove the file first so preallocation produces clean space.
        if not self._resume and self.file_path.exists():
            await asyncio.to_thread(os.unlink, str(self.file_path))

        already_sized = (
            self._resume
            and self.file_size > 0
            and self.file_path.exists()
            and self.file_path.stat().st_size == self.file_size
        )

        # O_NOFOLLOW (where available) refuses to open a symlink planted at the
        # .part path, preventing an attacker in the output directory from
        # redirecting positional writes to an arbitrary file.
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = await asyncio.to_thread(os.open, str(self.file_path), flags, 0o644)
        self._fd = fd

        if not already_sized and self.file_size > 0:
            await asyncio.to_thread(os.ftruncate, fd, self.file_size)

    async def write_at(self, offset: int, data: bytes) -> int:
        if not data:
            return 0
        if self._fd is None:
            raise OSError("File writer is not opened")
        return await asyncio.to_thread(self._seek_and_write, offset, data)

    async def flush(self) -> None:
        if self._fd is not None:
            await asyncio.to_thread(os.fsync, self._fd)

    async def close(self) -> None:
        fd = self._fd
        if fd is None:
            return
        try:
            await self.flush()
        finally:
            self._fd = None
            await asyncio.to_thread(os.close, fd)

    def _seek_and_write(self, offset: int, data: bytes) -> int:
        assert self._fd is not None
        with self._lock:
            os.lseek(self._fd, offset, os.SEEK_SET)
            return os.write(self._fd, data)
