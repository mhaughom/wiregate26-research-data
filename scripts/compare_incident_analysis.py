#!/usr/bin/env python3
"""Compare regenerated incident analysis with the published artifact."""

from pathlib import Path

from compare_outputs import compare_files


ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    compare_files(
        ROOT / "data" / "incident_analysis.json",
        ROOT / "data" / "incident_analysis.regenerated.json",
    )
