#!/usr/bin/env python3
"""Compare rebuilt ball-only extracts with the published files."""

from pathlib import Path

from compare_outputs import compare_files


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    compare_files(
        ROOT / "data" / "kick_analysis_arcs.json",
        ROOT / "data" / "kick_analysis_arcs.regenerated.json",
    )
    compare_files(
        ROOT / "data" / "kick_playback_tracks.json",
        ROOT / "data" / "kick_playback_tracks.regenerated.json",
    )
