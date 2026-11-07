"""Bounded strict JSON input and canonical output."""

import json
import os
import stat
from pathlib import Path

from .errors import AstreaError


def dumps(value):
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    )


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AstreaError("E_CONFIG", "Duplicate JSON key", key)
        result[key] = value
    return result


def read_bytes(path, maximum, nofollow=False, dir_fd=None):
    flags = os.O_RDONLY | os.O_NONBLOCK
    if nofollow:
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, dir_fd=dir_fd)
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise AstreaError("E_UNSAFE_PATH", "Expected a regular file")
            if info.st_size > maximum:
                raise AstreaError("E_LIMIT", "Input exceeds byte limit", limit=maximum)
            data = stream.read(maximum + 1)
            if len(data) > maximum:
                raise AstreaError("E_LIMIT", "Input exceeds byte limit", limit=maximum)
            return data
    except OSError as exc:
        raise AstreaError("E_IO", "Cannot read input file", exit_code=1) from exc


def load(path, maximum=64 * 1024 * 1024, nofollow=False, dir_fd=None):
    try:
        return json.loads(
            read_bytes(Path(path), maximum, nofollow, dir_fd).decode("utf-8"),
            object_pairs_hook=unique_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise AstreaError("E_CONFIG", "Invalid UTF-8 JSON") from exc
