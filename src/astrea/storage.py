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
def directory(path, trusted=False):
    path = Path(path)
    if ".." in path.parts:
        raise AstreaError("E_UNSAFE_PATH", "Parent traversal is not allowed")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open("/" if path.is_absolute() else ".", flags)
    try:
        if trusted:
            trusted_directory(fd)
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
            if trusted:
                trusted_directory(fd)
        yield fd
    finally:
        os.close(fd)


def write(fd, name, data):
    write_chunks(fd, name, [data])


def write_chunks(fd, name, chunks):
    safe_name(name)
    descriptor = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
    )
    with os.fdopen(descriptor, "wb") as stream:
        for chunk in chunks:
            stream.write(chunk)
        stream.flush()
        os.fsync(stream.fileno())


def restrictive_darwin_acl(fd):
    """Allow absent/deny-only ACLs; extended allow entries need a private parent."""
    libc = ctypes.CDLL(None, use_errno=True)
    libc.acl_get_fd.argtypes = [ctypes.c_int]
    libc.acl_get_fd.restype = ctypes.c_void_p
    libc.acl_to_text.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ssize_t)]
    libc.acl_to_text.restype = ctypes.c_void_p
    libc.acl_free.argtypes = [ctypes.c_void_p]
    libc.acl_free.restype = ctypes.c_int
    acl = libc.acl_get_fd(fd)
    if not acl:
        return ctypes.get_errno() == errno.ENOENT
    try:
        length = ctypes.c_ssize_t()
        text = libc.acl_to_text(acl, ctypes.byref(length))
        if not text:
            return False
        try:
            lines = ctypes.string_at(text, length.value).splitlines()
            return all(
                line.count(b":") >= 2
                and line.rsplit(b":", 2)[-2].split(b",")[0] == b"deny"
                for line in lines
                if line and not line.startswith(b"!#acl")
            )
        finally:
            libc.acl_free(text)
    finally:
        libc.acl_free(acl)


def trusted_directory(fd):
    """Only root/the current user may control output ancestry or staging names."""
    info = os.fstat(fd)
    shared = info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    if (
        info.st_uid not in {0, os.geteuid()}
        or (shared and not info.st_mode & stat.S_ISVTX)
        or (sys.platform == "darwin" and not restrictive_darwin_acl(fd))
    ):
        raise AstreaError(
            "E_UNSAFE_PATH",
            "Output ancestry must be trusted and not shared writable; use a private directory",
        )


def verify_identity(parent, name, identity):
    try:
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except OSError as exc:
        raise AstreaError(
            "E_UNSAFE_PATH", "Staging directory was moved or replaced"
        ) from exc
    if not stat.S_ISDIR(current.st_mode) or (current.st_ino, current.st_dev) != (
        identity.st_ino,
        identity.st_dev,
    ):
        raise AstreaError("E_UNSAFE_PATH", "Staging directory was moved or replaced")


def publish(parent, staging, destination, identity):
    """Use OS no-replace rename, never an existence-check followed by rename."""
    trusted_directory(parent)
    verify_identity(parent, staging, identity)
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

    verify_identity(parent, destination, identity)


@contextmanager
def staging(output):
    path = Path(output)
    destination = safe_name(path.name)
    with directory(path.parent, trusted=True) as parent:
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
            trusted_directory(fd)
            publish(parent, name, destination, identity)
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
