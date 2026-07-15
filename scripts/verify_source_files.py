#!/usr/bin/env python3
"""Verify locally retained, undistributed source files against public hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = json.loads((ROOT / "data" / "source_integrity.json").read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments_directory", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--full-ball-csv", type=Path)
    arguments = parser.parse_args()
    failures = []
    checked = 0
    for entry in RECORD["retained_source_files"]:
        if entry["name"] == "stream.malt" and arguments.manifest is not None:
            path = arguments.manifest
        elif entry["name"] == "ball_full.csv" and arguments.full_ball_csv is not None:
            path = arguments.full_ball_csv
        else:
            path = arguments.segments_directory / entry["name"]
        if not path.is_file():
            failures.append(f"missing {path}")
            continue
        checked += 1
        if path.stat().st_size != entry["size_bytes"]:
            failures.append(f"size mismatch for {path}")
        actual = sha256(path)
        if actual != entry["sha256"]:
            failures.append(f"SHA-256 mismatch for {path}: {actual}")
    if failures:
        raise SystemExit("Source verification failed:\n" + "\n".join(failures))
    print(f"Verified {checked} locally retained source files.")


if __name__ == "__main__":
    main()
