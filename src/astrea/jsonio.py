"""Bounded strict JSON input and canonical output."""

import json
import os
import stat
from pathlib import Path

from .errors import AstreaError

MAX_JSON_BYTES = 64 * 1024 * 1024


def iter_json(value, maximum=MAX_JSON_BYTES):
    """Encode canonical JSON incrementally, checking bytes before yielding them."""
    encoder = json.JSONEncoder(
        ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
    )
    total = 0
    for text in encoder.iterencode(value):
        chunk = text.encode("utf-8")
        total += len(chunk)
        if total >= maximum:  # Reserve the terminating newline.
            raise AstreaError(
                "E_LIMIT", "JSON metadata exceeds byte limit", "metadata", maximum
            )
        yield chunk
    yield b"\n"


def json_size(value, maximum=MAX_JSON_BYTES, indent_offset=0):
    """Measure a document or an indented entry without materializing its bytes."""
    total = 0
    for chunk in iter_json(value, maximum):
        total += len(chunk) + indent_offset * chunk.count(b"\n")
        if total > maximum:
            raise AstreaError(
                "E_LIMIT", "JSON metadata exceeds byte limit", "metadata", maximum
            )
    return total


def dumps(value):
    return b"".join(iter_json(value)).decode("utf-8")


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


def load(path, maximum=MAX_JSON_BYTES, nofollow=False, dir_fd=None):
    try:
        return json.loads(
            read_bytes(Path(path), maximum, nofollow, dir_fd).decode("utf-8"),
            object_pairs_hook=unique_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise AstreaError("E_CONFIG", "Invalid UTF-8 JSON") from exc
