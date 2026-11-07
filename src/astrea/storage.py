"""Descriptor-confined file access and exclusive publication of staged batches."""

import ctypes
import errno
import os
import shutil
import stat
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path

from .errors import AstreaError


def safe_name(name):
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or "/" in name
        or "\\" in name
        or "\x00" in name
    ):
        raise AstreaError("E_UNSAFE_PATH", "Expected a confined relative filename")
    return name


@contextmanager
def directory(path):
    path = Path(path)
    if ".." in path.parts:
        raise AstreaError("E_UNSAFE_PATH", "Parent traversal is not allowed")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open("/" if path.is_absolute() else ".", flags)
    try:
        for part in path.parts:
            if part in {"/", "."}:
                continue
            try:
                child = os.open(part, flags, dir_fd=fd)
            except OSError as exc:
                code = (
                    "E_UNSAFE_PATH"
                    if exc.errno in {errno.ELOOP, errno.ENOTDIR}
                    else "E_IO"
                )
                raise AstreaError(
                    code, "Cannot open a safe directory", exit_code=1
                ) from exc
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def write(fd, name, data):
    safe_name(name)
    descriptor = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def publish(parent, staging, destination):
    """Use OS no-replace rename, never an existence-check followed by rename."""
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        rename = libc.renameatx_np
        flag = 4  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        flag = 1  # RENAME_NOREPLACE
    else:
        raise AstreaError(
            "E_IO",
            "Exclusive directory publication is unavailable on this platform",
            exit_code=1,
        )
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    if rename(parent, os.fsencode(staging), parent, os.fsencode(destination), flag):
        error = ctypes.get_errno()
        if error in {errno.EEXIST, errno.ENOTEMPTY}:
            raise AstreaError("E_OUTPUT_EXISTS", "Output destination already exists")
        raise AstreaError("E_IO", "Cannot complete output directory", exit_code=1)


@contextmanager
def staging(output):
    path = Path(output)
    destination = safe_name(path.name)
    with directory(path.parent) as parent:
        try:
            os.stat(destination, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise AstreaError("E_OUTPUT_EXISTS", "Output destination already exists")
        name = ".astrea-" + uuid.uuid4().hex
        os.mkdir(name, 0o700, dir_fd=parent)
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        identity = os.fstat(fd)
        try:
            yield fd
            publish(parent, name, destination)
        finally:
            os.close(fd)
            try:
                current = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if stat.S_ISDIR(current.st_mode) and (
                    current.st_ino,
                    current.st_dev,
                ) == (identity.st_ino, identity.st_dev):
                    shutil.rmtree(name, dir_fd=parent)
            except FileNotFoundError:
                pass
