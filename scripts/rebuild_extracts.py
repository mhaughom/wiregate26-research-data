#!/usr/bin/env python3
"""Rebuild the published ball-only kick extracts from a full ball CSV.

The selected launch timestamps are a disclosed research decision recorded in
``data/kick_selection.json``. Rebuilding the ball windows does not require the
undistributed player stream, but independently repeating player attribution
does.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SELECTION = json.loads((ROOT / "data" / "kick_selection.json").read_text())
PITCH_LENGTH_M = 105.03
PITCH_WIDTH_M = 68.03


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ball_full_csv", type=Path)
    parser.add_argument("--output-directory", type=Path, default=ROOT / "data")
    arguments = parser.parse_args()

    rows = []
    with arguments.ball_full_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                (
                    int(row["ts_ms"]),
                    float(row["x"]) * PITCH_LENGTH_M,
                    float(row["y"]) * PITCH_WIDTH_M,
                    float(row["z"]),
                )
            )
    rows.sort()
    timestamps = [row[0] for row in rows]
    analysis_kicks = []
    playback_tracks = []
    incident = SELECTION["incident_timestamp_ms"]

    for selection in SELECTION["kicks"]:
        timestamp = selection["timestamp_ms"]
        start = bisect.bisect_left(timestamps, timestamp)
        if start >= len(rows) or rows[start][0] != timestamp:
            raise RuntimeError(f"full ball track does not align at {timestamp}")
        analysis_rows = rows[start : start + selection["analysis_sample_count"]]
        points = np.asarray([row[1:] for row in analysis_rows])
        direction = points[-1, :2] - points[0, :2]
        direction = direction / (np.linalg.norm(direction) or 1.0)
        projected = (points[:, :2] - points[0, :2]) @ direction
        trajectory = [
            [
                round((row[0] - timestamp) / 1000, 3),
                round(row[1], 3),
                round(row[2], 3),
                round(row[3], 3),
            ]
            for row in analysis_rows
        ]
        kick = {
            "ts": timestamp,
            "t_min": selection["match_minute"],
            "ours": timestamp == incident,
            "apex_m": round(float(np.max(points[:, 2])), 1),
            "dur_s": round((analysis_rows[-1][0] - timestamp) / 1000, 2),
            "s": [round(float(value), 2) for value in projected],
            "z": [round(float(value), 2) for value in points[:, 2]],
            "traj": trajectory,
        }
        if timestamp == incident:
            kick["strike_i"] = int(
                np.searchsorted(
                    np.asarray([row[0] - timestamp for row in analysis_rows]), 1830
                )
            )
        analysis_kicks.append(kick)

        end = bisect.bisect_right(
            timestamps, timestamp + round(SELECTION["playback_window_s"] * 1000)
        )
        playback_tracks.append(
            {
                "ts": timestamp,
                "traj": [
                    [
                        round((row[0] - timestamp) / 1000, 3),
                        round(row[1], 4),
                        round(row[2], 4),
                        round(row[3], 4),
                    ]
                    for row in rows[start:end]
                ],
            }
        )

    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    analysis_output = arguments.output_directory / "kick_analysis_arcs.regenerated.json"
    playback_output = arguments.output_directory / "kick_playback_tracks.regenerated.json"
    analysis_output.write_text(
        json.dumps({"taker": {"team": 1, "num": 1}, "kicks": analysis_kicks}, separators=(",", ":"))
    )
    playback_output.write_text(
        json.dumps(
            {
                "source": "scraped/ball_full.csv (FIFA EPTS)",
                "window_s": SELECTION["playback_window_s"],
                "tracks": playback_tracks,
            },
            separators=(",", ":"),
        )
    )
    print(f"wrote {analysis_output}")
    print(f"wrote {playback_output}")


if __name__ == "__main__":
    main()
