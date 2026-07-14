#!/usr/bin/env python3
"""Compare regenerated model output with the exact published artifact."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "kick_models.json"
REGENERATED = ROOT / "data" / "kick_models.regenerated.json"
TOLERANCE = 0.0011


def compare(left, right, path: str = "") -> tuple[float, str]:
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            raise ValueError(f"object keys differ at {path or '/'}")
        results = [compare(left[key], right[key], f"{path}/{key}") for key in left]
        return max(results, default=(0.0, path))

    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise ValueError(f"array length differs at {path or '/'}")
        results = [compare(a, b, f"{path}/{i}") for i, (a, b) in enumerate(zip(left, right))]
        return max(results, default=(0.0, path))

    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)), path

    if left != right:
        raise ValueError(f"value differs at {path or '/'}: {left!r} != {right!r}")
    return 0.0, path


def main() -> None:
    if not REGENERATED.is_file():
        raise SystemExit("Run scripts/generate_kick_models.py first.")
    reference = json.loads(REFERENCE.read_text())
    regenerated = json.loads(REGENERATED.read_text())
    maximum, path = compare(reference, regenerated)
    if not math.isfinite(maximum) or maximum > TOLERANCE:
        raise SystemExit(
            f"Model comparison failed: maximum difference {maximum:.6g} "
            f"at {path}; tolerance is {TOLERANCE}."
        )
    print(
        f"Model structure matches; maximum numerical difference "
        f"{maximum:.6g} at {path} (tolerance {TOLERANCE})."
    )


if __name__ == "__main__":
    main()
