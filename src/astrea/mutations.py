"""Recorded non-overlapping byte edits; never parse or repair mutated output."""

import base64
import copy
import hashlib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mutate(root, data, expected, message):
    params = message["parameters"]
    code = params.get("mutation_id")
    key = message["fixture_id"]
    edits = []
    cut = None

    def edit(offset, removed, inserted=b""):
        edits.append(
            {
                "offset": offset,
                "removed_bytes": removed,
                "inserted_base64": base64.b64encode(inserted).decode(),
            }
        )

    boundary = root.get_boundary()
    if code == "MIME_MISSING_CLOSE":
        marker = b"--" + boundary.encode() + b"--\r\n"
        edit(data.rindex(marker), len(marker))
    elif code == "MIME_BOUNDARY_REUSED":
        inner = root.get_payload()[0].get_boundary().encode()
        outer = boundary.encode()
        start = 0
        while (offset := data.find(inner, start)) >= 0:
            edit(offset, len(inner), outer)
            start = offset + len(inner)
    elif code == "MIME_BOUNDARY_MISMATCH":
        marker = b"--" + boundary.encode() + b"--"
        edit(data.rindex(marker) + 2, len(boundary), b"astrea-mismatched-boundary")
    elif code == "HEADER_DUPLICATE_CONTENT_TYPE":
        edit(0, 0, b"Content-Type: text/html\r\n")
    elif code == "HEADER_BROKEN_FOLD":
        edit(0, 0, b" broken fold without a preceding field\r\n")
    elif code == "HEADER_LINE_TOO_LONG":
        edit(0, 0, b"X-Astrea-Long: " + b"a" * 1100 + b"\r\n")
    elif code == "HEADER_BODY_SEPARATOR_MISSING":
        offset = data.index(b"\r\n\r\n")
        edit(offset, 4, b"\r\n")
    elif code in {
        "TRANSFER_INVALID_BASE64",
        "TRANSFER_TRUNCATED_QP",
        "CHARSET_MISMATCH",
    }:
        offset = data.index(b"\r\n\r\n") + 4
        if code == "TRANSFER_INVALID_BASE64":
            header_start = data.index(b"Content-Transfer-Encoding: ")
            end = data.index(b"\r\n", header_start)
            edit(header_start, end - header_start, b"Content-Transfer-Encoding: base64")
            edit(offset, len(data) - offset, b"@@@invalid-base64!!!\r\n")
        elif code == "TRANSFER_TRUNCATED_QP":
            header_start = data.index(b"Content-Transfer-Encoding: ")
            end = data.index(b"\r\n", header_start)
            edit(
                header_start,
                end - header_start,
                b"Content-Transfer-Encoding: quoted-printable",
            )
            edit(offset, len(data) - offset, b"Synthetic text=E")
        else:
            start = data.index(b'charset="utf-8"')
            edit(start, len(b'charset="utf-8"'), b'charset="us-ascii"')
            edit(offset, len(data) - offset, "Texte accentué\r\n".encode())
    elif key == "fixture.stress.truncated":
        code = "MESSAGE_TRUNCATED"
        # The last text child is the HTML alternative. Locate its encoded payload.
        leaf = root.get_payload()[0].get_payload()[-1]
        payload = (
            leaf.get_payload()
            .replace("\r\n", "\n")
            .replace("\n", "\r\n")
            .encode("ascii")
        )
        start = data.index(payload)
        cut = start + len(payload.rstrip(b"\r\n")) // 2
        edit(cut, len(data) - cut)
    output = data
    previous = len(data) + 1
    for item in sorted(edits, key=lambda e: e["offset"], reverse=True):
        offset, removed = item["offset"], item["removed_bytes"]
        if offset + removed > previous:
            raise ValueError("Overlapping mutation edits")
        output = (
            output[:offset]
            + base64.b64decode(item["inserted_base64"])
            + output[offset + removed :]
        )
        previous = offset
    return output, {
        "error_code": code,
        "parameters": params.copy(),
        "original_sha256": sha(data),
        "final_sha256": sha(output),
        "edits": sorted(edits, key=lambda e: e["offset"]),
        "baseline_expectations": copy.deepcopy(expected),
        "cut_offset": cut,
    }
