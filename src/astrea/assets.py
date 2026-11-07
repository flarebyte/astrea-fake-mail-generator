"""Packaged project-authored passive assets; fixed byte-for-byte."""

import hashlib
from importlib.resources import files

MEDIA = {
    "logo.png": "image/png",
    "photo.jpg": "image/jpeg",
    "invoice.pdf": "application/pdf",
    "notes.txt": "text/plain",
    "report.csv": "text/csv",
}
ASSETS = {
    name: (kind, files("astrea").joinpath("data/assets", name).read_bytes())
    for name, kind in MEDIA.items()
}


def inventory(names):
    return [
        {
            "id": name,
            "media_type": ASSETS[name][0],
            "size_bytes": len(ASSETS[name][1]),
            "sha256": hashlib.sha256(ASSETS[name][1]).hexdigest(),
            "source": "Astrea project-authored fixture",
            "license": "MIT",
            "safety_review": "Passive content; no external resources, actions, or embedded files; images 1x1",
        }
        for name in sorted(names)
    ]
