#!/usr/bin/env python3
"""Reproduce the incident-flight model comparison from the public ball track.

The impulse time is a discrete tracking-sample boundary.  It is therefore
selected by an explicit grid search, not passed to a gradient optimizer as if
it were a differentiable parameter.  At every candidate time, all continuous
parameters are refitted from the same initial state.
"""

from __future__ import annotations

import csv
import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "incident_ball_track.csv"
OUTPUT = ROOT / "data" / "incident_analysis.regenerated.json"

PITCH_LENGTH_M = 105.03
PITCH_WIDTH_M = 68.03
SOURCE_TIMELINE_ORIGIN_MS = 1783806352112
KICK_TIMESTAMP_MS = 1783806435336
FLIGHT_END_TIMESTAMP_MS = 1783806439420
DISPLAYED_CABLE_ALIGNMENT_TIMESTAMP_MS = 1783806437162

G = 9.81
AIR_DENSITY = 1.225
BALL_MASS_KG = 0.43
BALL_RADIUS_M = 0.11
BALL_AREA_M2 = math.pi * BALL_RADIUS_M**2
REST_HEIGHT_M = BALL_RADIUS_M
EXPORT_STEP_S = 0.02


def load_flight() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows: list[tuple[int, float, float, float]] = []
    with INPUT.open(newline="") as handle:
        for row in csv.DictReader(handle):
            timestamp = int(row["ts_ms"])
            if KICK_TIMESTAMP_MS <= timestamp <= FLIGHT_END_TIMESTAMP_MS:
                rows.append(
                    (
                        timestamp,
                        float(row["x"]) * PITCH_LENGTH_M,
                        float(row["y"]) * PITCH_WIDTH_M,
                        float(row["z"]),
                    )
                )
    rows.sort()
    if not rows or rows[0][0] != KICK_TIMESTAMP_MS:
        raise RuntimeError("incident flight does not start at the declared kick timestamp")
    if rows[-1][0] != FLIGHT_END_TIMESTAMP_MS:
        raise RuntimeError("incident flight does not end at the declared pre-interruption sample")
    timestamps = np.asarray([row[0] for row in rows], dtype=np.int64)
    times = (timestamps - timestamps[0]) / 1000.0
    positions = np.asarray([row[1:] for row in rows], dtype=float)
    return timestamps, times, positions


def acceleration(velocity: np.ndarray, drag_k: float, magnus: np.ndarray) -> np.ndarray:
    speed = np.linalg.norm(velocity)
    return (
        np.array([0.0, 0.0, -G])
        - drag_k * speed * velocity
        + speed * np.cross(magnus, velocity)
    )


def integrate(
    parameters: np.ndarray,
    times: np.ndarray,
    *,
    spin_decay: bool = False,
    impulse_time_s: float | None = None,
) -> np.ndarray:
    position = parameters[0:3].copy()
    velocity = parameters[3:6].copy()
    drag_k = AIR_DENSITY * parameters[6] * BALL_AREA_M2 / (2 * BALL_MASS_KG)
    magnus0 = parameters[7:10]
    offset = 10
    tau = max(abs(float(parameters[offset])), 1e-6) if spin_decay else None
    if spin_decay:
        offset += 1
    delta_velocity = parameters[offset : offset + 3] if impulse_time_s is not None else None

    output = [position.copy()]
    impulse_applied = False
    for index in range(len(times) - 1):
        step = float(times[index + 1] - times[index])
        magnus = (
            magnus0 * math.exp(-float(times[index]) / tau)
            if tau is not None
            else magnus0
        )
        k1v = acceleration(velocity, drag_k, magnus)
        k1p = velocity
        k2v = acceleration(velocity + step / 2 * k1v, drag_k, magnus)
        k2p = velocity + step / 2 * k1v
        k3v = acceleration(velocity + step / 2 * k2v, drag_k, magnus)
        k3p = velocity + step / 2 * k2v
        k4v = acceleration(velocity + step * k3v, drag_k, magnus)
        k4p = velocity + step * k3v
        position = position + step / 6 * (k1p + 2 * k2p + 2 * k3p + k4p)
        velocity = velocity + step / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
        if (
            delta_velocity is not None
            and not impulse_applied
            and times[index + 1] >= impulse_time_s
        ):
            velocity = velocity + delta_velocity
            impulse_applied = True
        output.append(position.copy())
    return np.asarray(output)


def rms_metres(residuals: np.ndarray) -> float:
    vectors = residuals.reshape(-1, 3)
    return float(math.sqrt(np.mean(np.sum(vectors**2, axis=1))))


def initial_parameters(times: np.ndarray, positions: np.ndarray) -> np.ndarray:
    velocity = (positions[5] - positions[0]) / (times[5] - times[0])
    return np.concatenate([positions[0], velocity, [0.25], [0.0, 0.0, 0.0]])


def fit_no_impulse(
    times: np.ndarray, positions: np.ndarray, *, spin_decay: bool
) -> tuple[np.ndarray, float]:
    initial = initial_parameters(times, positions)
    if spin_decay:
        initial = np.concatenate([initial, [10.0]])

    def residuals(parameters: np.ndarray) -> np.ndarray:
        return (
            integrate(parameters, times, spin_decay=spin_decay) - positions
        ).ravel()

    result = least_squares(residuals, initial, method="lm", max_nfev=20_000)
    return result.x, rms_metres(result.fun)


def fit_fixed_impulse(
    times: np.ndarray,
    positions: np.ndarray,
    impulse_time_s: float,
    base_parameters: np.ndarray,
    *,
    spin_decay: bool,
) -> tuple[np.ndarray, float]:
    initial = np.concatenate([base_parameters, [0.0, 0.0, 0.0]])

    def residuals(parameters: np.ndarray) -> np.ndarray:
        return (
            integrate(
                parameters,
                times,
                spin_decay=spin_decay,
                impulse_time_s=impulse_time_s,
            )
            - positions
        ).ravel()

    result = least_squares(residuals, initial, method="lm", max_nfev=20_000)
    return result.x, rms_metres(result.fun)


def locate_impulse(
    times: np.ndarray, positions: np.ndarray, base_parameters: np.ndarray
) -> tuple[float, np.ndarray, float, list[dict]]:
    coarse_times = np.arange(0.8, 3.601, 0.2)
    coarse: list[tuple[float, float, np.ndarray]] = []
    localization: list[dict] = []
    for candidate in coarse_times:
        parameters, rms = fit_fixed_impulse(
            times, positions, float(candidate), base_parameters, spin_decay=False
        )
        impulse = parameters[-3:]
        coarse.append((rms, float(candidate), parameters))
        localization.append(
            {
                "time_from_kick_s": round(float(candidate), 3),
                "source_timestamp_ms": int(KICK_TIMESTAMP_MS + round(candidate * 1000)),
                "rms_cm": round(rms * 100, 3),
                "impulse_mps": round(float(np.linalg.norm(impulse)), 4),
            }
        )

    _, coarse_best_time, _ = min(coarse, key=lambda item: item[0])
    native_candidates = [
        float(candidate)
        for candidate in times[1:-1]
        if coarse_best_time - 0.25 <= candidate <= coarse_best_time + 0.25
    ]
    fine: list[tuple[float, float, np.ndarray]] = []
    for candidate in native_candidates:
        parameters, rms = fit_fixed_impulse(
            times, positions, candidate, base_parameters, spin_decay=False
        )
        fine.append((rms, candidate, parameters))
    best_rms, best_time, best_parameters = min(fine, key=lambda item: item[0])
    return best_time, best_parameters, best_rms, localization


def integrate_to_ground(parameters: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    times = np.arange(0.0, 8.0 + EXPORT_STEP_S / 2, EXPORT_STEP_S)
    positions = integrate(parameters[:10], times)
    apex = int(np.argmax(positions[:, 2]))
    crossing = next(
        (
            index
            for index in range(apex + 1, len(positions))
            if positions[index, 2] <= REST_HEIGHT_M
        ),
        len(positions) - 1,
    )
    times = times[: crossing + 1].copy()
    positions = positions[: crossing + 1].copy()
    if crossing > 0 and positions[-1, 2] < REST_HEIGHT_M:
        before, after = positions[-2], positions[-1]
        fraction = (REST_HEIGHT_M - before[2]) / (after[2] - before[2])
        positions[-1] = before + fraction * (after - before)
        times[-1] = times[-2] + fraction * EXPORT_STEP_S
    return times, positions


def crossing_at_height(
    times: np.ndarray, positions: np.ndarray, height: float
) -> tuple[float, np.ndarray]:
    apex = int(np.argmax(positions[:, 2]))
    for index in range(apex + 1, len(positions)):
        before, after = positions[index - 1], positions[index]
        if before[2] >= height >= after[2]:
            fraction = (height - before[2]) / (after[2] - before[2])
            return (
                float(times[index - 1] + fraction * (times[index] - times[index - 1])),
                before + fraction * (after - before),
            )
    raise RuntimeError("counterfactual did not cross the interruption height")


def extrapolate_touchdown(
    times: np.ndarray, positions: np.ndarray, window_metres: float = 3.0
) -> tuple[float, np.ndarray, int, np.ndarray]:
    end = len(positions) - 1
    start = end
    travelled = 0.0
    while start > 0 and travelled < window_metres:
        travelled += float(np.linalg.norm(positions[start] - positions[start - 1]))
        start -= 1
    window_times = times[start : end + 1]
    window_positions = positions[start : end + 1]
    relative = window_times - times[end]
    design = np.column_stack([np.ones(len(relative)), relative])
    vx = float(np.linalg.lstsq(design, window_positions[:, 0], rcond=None)[0][1])
    vy = float(np.linalg.lstsq(design, window_positions[:, 1], rcond=None)[0][1])
    gravity_removed = window_positions[:, 2] + 0.5 * G * relative**2
    vz = float(np.linalg.lstsq(design, gravity_removed, rcond=None)[0][1])
    velocity = np.array([vx, vy, vz])
    start_position = positions[end]
    discriminant = max(0.0, vz * vz + 2 * G * (start_position[2] - REST_HEIGHT_M))
    duration = (vz + math.sqrt(discriminant)) / G
    touchdown = np.array(
        [
            start_position[0] + vx * duration,
            start_position[1] + vy * duration,
            REST_HEIGHT_M,
        ]
    )
    return float(times[end] + duration), touchdown, start, velocity


def rounded_vector(vector: np.ndarray, digits: int = 4) -> list[float]:
    return [round(float(value), digits) for value in vector]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    arguments = parser.parse_args()
    timestamps, times, positions = load_flight()
    model_a, rms_a = fit_no_impulse(times, positions, spin_decay=False)
    model_b, rms_b = fit_no_impulse(times, positions, spin_decay=True)
    impulse_time, model_c, rms_c, localization = locate_impulse(
        times, positions, model_a
    )
    model_d, rms_d = fit_fixed_impulse(
        times, positions, impulse_time, model_b, spin_decay=True
    )

    impulse_c = model_c[-3:]
    impulse_d = model_d[-3:]
    model_times, no_impulse_positions = integrate_to_ground(model_c)
    interruption = positions[-1]
    same_height_time, same_height_position = crossing_at_height(
        model_times, no_impulse_positions, float(interruption[2])
    )
    continuation_time, continuation_touchdown, continuation_start, continuation_velocity = (
        extrapolate_touchdown(times, positions)
    )
    touchdown_miss = float(
        np.linalg.norm(no_impulse_positions[-1, :2] - continuation_touchdown[:2])
    )
    same_height_miss = float(
        np.linalg.norm(same_height_position[:2] - interruption[:2])
    )

    launch_velocity = model_c[3:6]
    lift_coefficient = float(
        np.linalg.norm(model_c[7:10]) * 2 * BALL_MASS_KG / (AIR_DENSITY * BALL_AREA_M2)
    )
    payload = {
        "analysis_version": 1,
        "claim_scope": (
            "The recorded trajectory contains a localized discontinuity that is better "
            "fit by an impulse model; ball tracking alone does not identify its cause."
        ),
        "source": {
            "file": "data/incident_ball_track.csv",
            "source_timeline_origin_ms": SOURCE_TIMELINE_ORIGIN_MS,
            "kick_timestamp_ms": KICK_TIMESTAMP_MS,
            "flight_end_timestamp_ms": FLIGHT_END_TIMESTAMP_MS,
            "sample_count": int(len(times)),
            "duration_s": round(float(times[-1]), 3),
            "displayed_cable_alignment_timestamp_ms": DISPLAYED_CABLE_ALIGNMENT_TIMESTAMP_MS,
            "displayed_cable_alignment_is_measured": False,
        },
        "method": {
            "acceleration": "gravity - k*|v|*v + |v|*(w cross v)",
            "integrator": "RK4 at recorded timestamps; 20 ms for continuation",
            "models": {
                "A": "constant drag and constant Magnus vector",
                "B": "A with exponential Magnus decay",
                "C": "A with one velocity impulse at a discrete sample boundary",
                "D": "B with one velocity impulse at the model-C selected boundary",
            },
            "impulse_time_selection": (
                "0.2 s coarse grid followed by every native sample boundary within 0.25 s "
                "of the coarse minimum; continuous parameters are refitted at each time"
            ),
            "optimizer": "SciPy nonlinear least squares, Levenberg-Marquardt",
            "formal_confidence_interval_available": False,
            "formal_confidence_interval_reason": (
                "The delivered source did not include sensor covariance or filtering metadata."
            ),
        },
        "results": {
            "model_rms_cm": {
                "A": round(rms_a * 100, 3),
                "B": round(rms_b * 100, 3),
                "C": round(rms_c * 100, 3),
                "D": round(rms_d * 100, 3),
            },
            "selected_impulse_time_from_kick_s": round(float(impulse_time), 3),
            "selected_impulse_timestamp_ms": int(
                KICK_TIMESTAMP_MS + round(impulse_time * 1000)
            ),
            "impulse_vector_mps": rounded_vector(impulse_c),
            "impulse_magnitude_mps": round(float(np.linalg.norm(impulse_c)), 4),
            "model_d_impulse_vector_mps": rounded_vector(impulse_d),
            "model_d_impulse_magnitude_mps": round(float(np.linalg.norm(impulse_d)), 4),
            "drag_coefficient": round(float(model_c[6]), 6),
            "lift_coefficient": round(lift_coefficient, 6),
            "launch_speed_mps": round(float(np.linalg.norm(launch_velocity)), 4),
            "launch_elevation_deg": round(
                math.degrees(
                    math.atan2(
                        float(launch_velocity[2]),
                        float(np.linalg.norm(launch_velocity[:2])),
                    )
                ),
                4,
            ),
            "observed_interruption": rounded_vector(interruption),
            "model_at_same_height": rounded_vector(same_height_position),
            "same_height_time_from_kick_s": round(same_height_time, 4),
            "same_height_horizontal_miss_m": round(same_height_miss, 4),
            "continuation_window_m": 3.0,
            "continuation_start_time_from_kick_s": round(float(times[continuation_start]), 4),
            "continuation_velocity_mps": rounded_vector(continuation_velocity),
            "extrapolated_touchdown_time_from_kick_s": round(continuation_time, 4),
            "extrapolated_touchdown": rounded_vector(continuation_touchdown),
            "no_impulse_touchdown_time_from_kick_s": round(float(model_times[-1]), 4),
            "no_impulse_touchdown": rounded_vector(no_impulse_positions[-1]),
            "touchdown_horizontal_miss_m": round(touchdown_miss, 4),
        },
        "impulse_time_sensitivity": localization,
        "recorded_flight": [
            [round(float(time), 3), *rounded_vector(position, 4)]
            for time, position in zip(times, positions)
        ],
        "no_impulse_counterfactual": [
            [round(float(time), 4), *rounded_vector(position, 4)]
            for time, position in zip(model_times, no_impulse_positions)
        ],
    }
    arguments.output.write_text(json.dumps(payload, indent=2) + "\n")
    try:
        output_label = arguments.output.relative_to(ROOT)
    except ValueError:
        output_label = arguments.output
    print(f"wrote {output_label}")
    print(
        "RMS A/B/C/D: "
        f"{rms_a * 100:.2f}/{rms_b * 100:.2f}/{rms_c * 100:.2f}/{rms_d * 100:.2f} cm"
    )
    print(
        f"selected impulse {np.linalg.norm(impulse_c):.3f} m/s at "
        f"t+{impulse_time:.3f} s; touchdown separation {touchdown_miss:.3f} m"
    )


if __name__ == "__main__":
    main()
