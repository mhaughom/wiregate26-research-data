#!/usr/bin/env python3
"""Extract normalized ball coordinates from locally obtained ATS segments."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from parse_ats import parse_segment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--start-ms", type=int)
    parser.add_argument("--end-ms", type=int)
    arguments = parser.parse_args()

    samples: dict[int, tuple[float, float, float]] = {}
    for segment in sorted(arguments.segments):
        for timestamp, entities in parse_segment(segment, wanted_ids={"-1"}):
            ball = entities.get("-1")
            if ball is None or any(value is None for value in ball):
                continue
            if arguments.start_ms is not None and timestamp < arguments.start_ms:
                continue
            if arguments.end_ms is not None and timestamp > arguments.end_ms:
                continue
            coordinates = tuple(float(value) for value in ball)
            existing = samples.get(timestamp)
            if existing is not None and existing != coordinates:
                raise RuntimeError(f"conflicting ball samples at {timestamp}")
            samples[timestamp] = coordinates

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ts_ms", "x", "y", "z"])
        for timestamp, coordinates in sorted(samples.items()):
            writer.writerow([timestamp, *coordinates])
    print(f"wrote {len(samples)} ball samples -> {arguments.output}")


if __name__ == "__main__":
    main()
