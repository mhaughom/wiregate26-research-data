#!/usr/bin/env python3
"""Compare regenerated kick models with the published artifact."""

from __future__ import annotations

from pathlib import Path

from compare_outputs import compare_files

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "kick_models.json"
REGENERATED = ROOT / "data" / "kick_models.regenerated.json"


def main() -> None:
    compare_files(REFERENCE, REGENERATED)


if __name__ == "__main__":
    main()
