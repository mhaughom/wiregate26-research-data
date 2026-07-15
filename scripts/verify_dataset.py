#!/usr/bin/env python3
"""Verify integrity, schemas, declared counts, timing, and core invariants."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_json(payload, schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        rendered = []
        for error in errors[:20]:
            location = "/" + "/".join(str(part) for part in error.path)
            rendered.append(f"{schema_path.name} {location}: {error.message}")
        raise ValueError("\n".join(rendered))


def validate_trajectory(trajectory: list, label: str) -> None:
    if not trajectory:
        raise ValueError(f"{label}: empty trajectory")
    previous = -math.inf
    for index, row in enumerate(trajectory):
        if len(row) != 4 or not all(
            isinstance(value, (int, float)) and math.isfinite(value) for value in row
        ):
            raise ValueError(f"{label}/{index}: invalid trajectory row")
        if row[0] <= previous:
            raise ValueError(f"{label}/{index}: time is not strictly increasing")
        previous = row[0]


def validate_csv(path: Path, entry: dict) -> dict[str, int | float]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["ts_ms", "x", "y", "z"]:
            raise ValueError(f"{path}: expected CSV header ts_ms,x,y,z")
        rows = list(reader)
    previous = None
    for index, row in enumerate(rows):
        timestamp = int(row["ts_ms"])
        values = [float(row[key]) for key in ("x", "y", "z")]
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"{path}:{index + 2}: non-finite coordinate")
        if previous is not None and timestamp <= previous:
            raise ValueError(f"{path}:{index + 2}: timestamps are not strictly increasing")
        if abs(values[0]) > 1.0 or abs(values[1]) > 1.0 or not -1.0 <= values[2] <= 100.0:
            raise ValueError(f"{path}:{index + 2}: coordinate outside broad declared bounds")
        previous = timestamp
    if not rows:
        raise ValueError(f"{path}: empty CSV")
    first = int(rows[0]["ts_ms"])
    last = int(rows[-1]["ts_ms"])
    if first != entry["first_source_timestamp_ms"] or last != entry["last_source_timestamp_ms"]:
        raise ValueError(f"{path}: timestamp endpoints do not match manifest")
    return {"sample_count": len(rows), "duration_s": (last - first) / 1000}


def validate_payload(path: Path, payload: dict, role: str) -> dict[str, int | float]:
    actual: dict[str, int | float] = {}
    if "analysis arcs" in role:
        kicks = payload["kicks"]
        for index, kick in enumerate(kicks):
            validate_trajectory(kick["traj"], f"{path}/kicks/{index}/traj")
            if not (len(kick["s"]) == len(kick["z"]) == len(kick["traj"])):
                raise ValueError(f"{path}/kicks/{index}: s, z, and traj lengths differ")
        actual = {
            "track_count": len(kicks),
            "sample_count": sum(len(kick["traj"]) for kick in kicks),
            "aggregate_duration_s": sum(
                kick["traj"][-1][0] - kick["traj"][0][0] for kick in kicks
            ),
        }
    elif "playback windows" in role:
        tracks = payload["tracks"]
        for index, track in enumerate(tracks):
            validate_trajectory(track["traj"], f"{path}/tracks/{index}/traj")
        actual = {
            "track_count": len(tracks),
            "sample_count": sum(len(track["traj"]) for track in tracks),
            "aggregate_duration_s": sum(
                track["traj"][-1][0] - track["traj"][0][0] for track in tracks
            ),
        }
    elif "model output" in role:
        actual = {"estimate_count": len(payload["estimates"])}
    elif "incident impulse-model" in role:
        validate_trajectory(payload["recorded_flight"], f"{path}/recorded_flight")
        validate_trajectory(
            payload["no_impulse_counterfactual"], f"{path}/no_impulse_counterfactual"
        )
        actual = {"sample_count": len(payload["recorded_flight"])}
    elif "selection record" in role:
        kicks = payload["kicks"]
        excluded = [kick for kick in kicks if not kick["in_play_comparison"]]
        declared_excluded = MANIFEST["comparison"]["excluded_after_goal_timestamp_ms"]
        if len(excluded) != 1 or excluded[0]["timestamp_ms"] != declared_excluded:
            raise ValueError(f"{path}: excluded comparison kick does not match manifest")
        actual = {"track_count": len(kicks)}
    elif "undistributed source files" in role:
        actual = {"source_file_count": len(payload["retained_source_files"])}
    return actual


def close_enough(left: int | float, right: int | float) -> bool:
    if isinstance(left, int) and isinstance(right, int):
        return left == right
    return math.isclose(float(left), float(right), abs_tol=0.001, rel_tol=0.0)


def main() -> None:
    failures: list[str] = []
    try:
        validate_json(
            MANIFEST,
            ROOT / "schemas" / "manifest.schema.json",
        )
    except Exception as error:
        failures.append(f"manifest schema: {error}")

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
            continue
        try:
            if path.suffix == ".csv":
                actual = validate_csv(path, entry)
            else:
                payload = json.loads(path.read_text())
                schema_path = ROOT / entry["schema"]
                validate_json(payload, schema_path)
                actual = validate_payload(path, payload, entry["role"])
            for key, value in actual.items():
                if key not in entry:
                    failures.append(f"manifest omits {key} for {entry['path']}")
                elif not close_enough(value, entry[key]):
                    failures.append(
                        f"{key} mismatch: {entry['path']} expected {entry[key]}, actual {value}"
                    )
        except Exception as error:
            failures.append(f"validation failed: {entry['path']}: {error}")

    if failures:
        raise SystemExit("Dataset verification failed:\n" + "\n".join(failures))
    print(
        f"Verified {len(MANIFEST['files'])} data files: hashes, schemas, counts, "
        "timing, coordinates, and declared exclusions."
    )


if __name__ == "__main__":
    main()
