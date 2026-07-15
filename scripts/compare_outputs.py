#!/usr/bin/env python3
"""Compare generated JSON with field-aware numerical tolerances."""

from __future__ import annotations

import json
import math
from pathlib import Path


def tolerance_for(path: str, left: int | float, right: int | float) -> float:
    if isinstance(left, int) and isinstance(right, int):
        return 0.0
    leaf = path.rsplit("/", 1)[-1]
    if any(token in leaf for token in ("timestamp_ms", "sample_count", "track_count")):
        return 0.0
    if leaf in {"analysis_version", "apex_index", "fit_samples"}:
        return 0.0
    if leaf in {"drag_coefficient", "lift_coefficient", "cd", "cl"}:
        return 1.1e-5
    if leaf.endswith("_cm"):
        return 0.1
    if leaf.endswith(("_m", "_mps", "_s")):
        return 0.0011
    # Array values inherit no field name and may mix seconds and metres. The
    # tolerance is therefore explicitly in each value's native unit; it must
    # never be described generically as millimetres.
    if leaf.isdigit():
        return 0.0011
    return 1e-8


def compare(left, right, path: str = "") -> tuple[float, float, str]:
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            raise ValueError(f"object keys differ at {path or '/'}")
        results = [compare(left[key], right[key], f"{path}/{key}") for key in left]
        return max(results, default=(0.0, 0.0, path), key=lambda item: item[0])

    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise ValueError(f"array length differs at {path or '/'}")
        results = [
            compare(a, b, f"{path}/{index}")
            for index, (a, b) in enumerate(zip(left, right))
        ]
        return max(results, default=(0.0, 0.0, path), key=lambda item: item[0])

    if (
        isinstance(left, (int, float))
        and not isinstance(left, bool)
        and isinstance(right, (int, float))
        and not isinstance(right, bool)
    ):
        difference = abs(float(left) - float(right))
        tolerance = tolerance_for(path, left, right)
        if tolerance == 0.0:
            ratio = 0.0 if difference == 0.0 else math.inf
        else:
            ratio = difference / tolerance
        return ratio, difference, path

    if left != right:
        raise ValueError(f"value differs at {path or '/'}: {left!r} != {right!r}")
    return 0.0, 0.0, path


def compare_files(reference_path: Path, regenerated_path: Path) -> None:
    if not regenerated_path.is_file():
        raise SystemExit(f"missing regenerated output: {regenerated_path}")
    reference = json.loads(reference_path.read_text())
    regenerated = json.loads(regenerated_path.read_text())
    ratio, difference, path = compare(reference, regenerated)
    if not math.isfinite(ratio) or ratio > 1.0:
        raise SystemExit(
            f"comparison failed at {path}: difference {difference:.8g}, "
            f"allowed {tolerance_for(path, 0.0, 0.0):.8g}"
        )
    print(
        f"Structure and values match; largest tolerance usage {ratio * 100:.1f}% "
        f"at {path} (difference {difference:.8g})."
    )
