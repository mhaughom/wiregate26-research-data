#!/usr/bin/env python3
"""Verify integrity and declared record counts for the public dataset."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data" / "manifest.json").read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_count(path: Path, role: str) -> tuple[str, int] | None:
    if path.suffix == ".csv":
        with path.open(newline="") as handle:
            return "sample_count", sum(1 for _ in csv.DictReader(handle))

    payload = json.loads(path.read_text())
    if "analysis arcs" in role:
        return "sample_count", sum(len(kick["traj"]) for kick in payload["kicks"])
    if "playback windows" in role:
        return "sample_count", sum(len(track["traj"]) for track in payload["tracks"])
    if "model output" in role:
        return "estimate_count", len(payload["estimates"])
    return None


def main() -> None:
    failures: list[str] = []
    for entry in MANIFEST["files"]:
        path = ROOT / entry["path"]
        if not path.is_file():
            failures.append(f"missing: {entry['path']}")
            continue

        actual_hash = sha256(path)
        if actual_hash != entry["sha256"]:
            failures.append(
                f"hash mismatch: {entry['path']}\n"
                f"  expected {entry['sha256']}\n"
                f"  actual   {actual_hash}"
            )

        count = record_count(path, entry["role"])
        if count:
            key, actual_count = count
            if actual_count != entry[key]:
                failures.append(
                    f"{key} mismatch: {entry['path']} "
                    f"expected {entry[key]}, actual {actual_count}"
                )

    if failures:
        raise SystemExit("Dataset verification failed:\n" + "\n".join(failures))
    print(f"Verified {len(MANIFEST['files'])} data files and declared counts.")


if __name__ == "__main__":
    main()
