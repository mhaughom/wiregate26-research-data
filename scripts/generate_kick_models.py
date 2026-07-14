#!/usr/bin/env python3
"""Generate out-of-sample physics continuations for every Nyland goal kick.

Each model is fitted only from the first tracked flight sample through the
apex.  Samples after the apex are retained solely for validation; they never
enter the optimizer.  This makes the rendered tail a genuine prediction
rather than a curve fitted to the outcome it is meant to estimate.

The equations and parameterization match ``predict_second_half.py``:

    a = gravity - k |v| v + |v| (w x v)

with launch position, launch velocity, drag coefficient and a constant Magnus
vector fitted by non-linear least squares.  Integration uses RK4 at the native
tracking timestamps and at 20 ms for the exported continuation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "kick_analysis_arcs.json"
OUTPUT = ROOT / "data" / "kick_models.regenerated.json"

G = 9.81
RHO = 1.225
M = 0.43
R = 0.11
A = math.pi * R * R
REST_Z = 0.11
EXPORT_DT = 0.02


def accel(v: np.ndarray, drag_k: float, magnus: np.ndarray) -> np.ndarray:
    speed = np.linalg.norm(v)
    return (
        np.array([0.0, 0.0, -G])
        - drag_k * speed * v
        + speed * np.cross(magnus, v)
    )


def integrate(
    p0: np.ndarray,
    v0: np.ndarray,
    cd: float,
    times: np.ndarray,
    magnus: np.ndarray,
) -> np.ndarray:
    drag_k = RHO * cd * A / (2 * M)
    p = np.array(p0, dtype=float)
    v = np.array(v0, dtype=float)
    out = [p.copy()]
    for i in range(len(times) - 1):
        h = times[i + 1] - times[i]
        k1v = accel(v, drag_k, magnus)
        k1p = v
        k2v = accel(v + h / 2 * k1v, drag_k, magnus)
        k2p = v + h / 2 * k1v
        k3v = accel(v + h / 2 * k2v, drag_k, magnus)
        k3p = v + h / 2 * k2v
        k4v = accel(v + h * k3v, drag_k, magnus)
        k4p = v + h * k3v
        p = p + h / 6 * (k1p + 2 * k2p + 2 * k3p + k4p)
        v = v + h / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
        out.append(p.copy())
    return np.asarray(out)


def first_flight_apex(times: np.ndarray, heights: np.ndarray) -> int:
    """Return the first sustained high point, not a later headed/bounced arc."""
    # A short centred smooth rejects single-frame tracker jitter.  Some exports
    # contain a second airborne segment after a player contact, so argmax over
    # the whole clip can select a completely different flight.
    smooth = np.convolve(heights, np.ones(5) / 5, mode="same")
    start = int(np.searchsorted(times, 0.45))
    for i in range(max(start, 10), len(heights) - 15):
        rose = smooth[i] - smooth[i - 10]
        fell = smooth[i] - smooth[i + 15]
        turns = smooth[i] >= smooth[i - 1] and smooth[i] > smooth[i + 1]
        if turns and rose > 0.08 and fell > 0.08 and smooth[i] > 2.0:
            lo, hi = max(0, i - 4), min(len(heights), i + 5)
            return lo + int(np.argmax(heights[lo:hi]))
    return int(np.argmax(heights))


def local_velocity(
    times: np.ndarray, positions: np.ndarray, start: int, stop: int
) -> np.ndarray:
    """Least-squares velocity over a short window (less noisy than differences)."""
    window_t = times[start:stop]
    window_p = positions[start:stop]
    centred_t = window_t - np.mean(window_t)
    denominator = float(np.sum(centred_t**2))
    if denominator <= 0:
        return np.zeros(3)
    return np.sum(
        centred_t[:, np.newaxis] * (window_p - np.mean(window_p, axis=0)),
        axis=0,
    ) / denominator


def first_interruption(
    times: np.ndarray, positions: np.ndarray, apex: int
) -> tuple[int, str, float]:
    """Locate the first bounce/player touch after the first apex.

    A five-sample regression on either side of a candidate rejects the normal
    frame-to-frame EPTS wobble. A change of 4 m/s is far above the smooth
    aerodynamic evolution seen in uninterrupted controls. When tracking ends
    before a visible discontinuity, the last measured point is the honest
    comparison bound; it is not silently called a landing.
    """
    window = 5
    first = max(apex + window, window * 2)
    for i in range(first, len(times) - window):
        before = local_velocity(times, positions, i - window, i)
        after = local_velocity(times, positions, i + 1, i + 1 + window)
        velocity_change = float(np.linalg.norm(after - before))
        if velocity_change >= 4.0:
            # The discontinuity is bracketed by the two regression windows;
            # keep the last unquestionably pre-contact sample.
            return max(apex, i - 1), "velocity_discontinuity", velocity_change
    return len(times) - 1, "track_end", 0.0


def descending_crossing(
    times: np.ndarray, positions: np.ndarray, height: float
) -> tuple[float, np.ndarray]:
    """Interpolate the model's first descending crossing of ``height``."""
    apex = int(np.argmax(positions[:, 2]))
    for i in range(apex + 1, len(times)):
        a, b = positions[i - 1], positions[i]
        if a[2] >= height >= b[2]:
            fraction = (height - a[2]) / (b[2] - a[2])
            return (
                float(times[i - 1] + fraction * (times[i] - times[i - 1])),
                a + fraction * (b - a),
            )
    return float(times[-1]), positions[-1].copy()


def extrapolate_touchdown(
    times: np.ndarray,
    positions: np.ndarray,
    end_index: int,
    window_metres: float = 3.0,
) -> tuple[float, np.ndarray, int, np.ndarray]:
    """Continue the final pre-interruption 3 m ballistically to the grass.

    Horizontal velocity is fitted by least squares. Vertical velocity is
    fitted after removing known gravitational displacement, then gravity is
    restored for the short continuation. The extrapolation begins at the last
    recorded pre-interruption point so the displayed path stays continuous.
    """
    start_index = end_index
    travelled = 0.0
    while start_index > 0 and travelled < window_metres:
        travelled += float(
            np.linalg.norm(positions[start_index] - positions[start_index - 1])
        )
        start_index -= 1

    window_t = times[start_index : end_index + 1]
    window_p = positions[start_index : end_index + 1]
    tau = window_t - times[end_index]
    design = np.column_stack([np.ones(len(tau)), tau])
    vx = float(np.linalg.lstsq(design, window_p[:, 0], rcond=None)[0][1])
    vy = float(np.linalg.lstsq(design, window_p[:, 1], rcond=None)[0][1])
    gravity_removed_z = window_p[:, 2] + 0.5 * G * tau**2
    vz = float(np.linalg.lstsq(design, gravity_removed_z, rcond=None)[0][1])

    p0 = positions[end_index]
    discriminant = max(0.0, vz * vz + 2 * G * (p0[2] - REST_Z))
    flight_time = (vz + math.sqrt(discriminant)) / G
    touchdown = np.array(
        [p0[0] + vx * flight_time, p0[1] + vy * flight_time, REST_Z]
    )
    return (
        float(times[end_index] + flight_time),
        touchdown,
        start_index,
        np.array([vx, vy, vz]),
    )


def fit_kick(kick: dict) -> dict:
    traj = np.asarray(kick["traj"], dtype=float)
    times = traj[:, 0]
    positions = traj[:, 1:4]
    apex = first_flight_apex(times, positions[:, 2])
    fit_times = times[: apex + 1]
    fit_positions = positions[: apex + 1]

    guess_i = min(5, len(positions) - 1)
    v_guess = (positions[guess_i] - positions[0]) / (
        times[guess_i] - times[0]
    )
    theta0 = np.concatenate(
        [positions[0], v_guess, np.array([0.25, 0.0, 0.0, 0.0])]
    )

    def residuals(theta: np.ndarray) -> np.ndarray:
        predicted = integrate(
            theta[0:3], theta[3:6], theta[6], fit_times, theta[7:10]
        )
        return (predicted - fit_positions).ravel()

    # This deliberately matches the original validation script.  There are
    # many more observations than parameters for every kick in this export.
    result = least_squares(residuals, theta0, method="lm", max_nfev=2500)
    p0, v0 = result.x[0:3], result.x[3:6]
    cd, magnus = float(result.x[6]), result.x[7:10]

    fitted = integrate(p0, v0, cd, fit_times, magnus)
    fit_error = np.linalg.norm(fitted - fit_positions, axis=1)
    rms = float(math.sqrt(np.mean(fit_error**2)))

    max_time = max(float(times[-1]) + 4.0, 10.0)
    export_times = np.arange(0.0, max_time + EXPORT_DT / 2, EXPORT_DT)
    predicted = integrate(p0, v0, cd, export_times, magnus)
    after_apex = np.where(
        (export_times > float(times[apex])) & (predicted[:, 2] <= REST_Z)
    )[0]
    land_i = int(after_apex[0]) if len(after_apex) else len(predicted) - 1

    # Interpolate the final step to exactly ball-centre ground height so the
    # exported line does not visibly pass below the pitch.
    model_times = export_times[: land_i + 1].copy()
    model_positions = predicted[: land_i + 1].copy()
    if land_i > 0 and model_positions[-1, 2] < REST_Z:
        a, b = model_positions[-2], model_positions[-1]
        f = (REST_Z - a[2]) / (b[2] - a[2])
        model_positions[-1] = a + f * (b - a)
        model_times[-1] = export_times[land_i - 1] + f * EXPORT_DT

    interruption_i, interruption_source, velocity_change = first_interruption(
        times, positions, apex
    )
    observed_interruption = positions[interruption_i]
    comparison_time, model_at_height = descending_crossing(
        model_times, model_positions, float(observed_interruption[2])
    )
    interruption_miss = float(
        np.linalg.norm(model_at_height[:2] - observed_interruption[:2])
    )
    (
        extrapolated_touchdown_time,
        extrapolated_touchdown,
        continuation_start_i,
        continuation_velocity,
    ) = extrapolate_touchdown(times, positions, interruption_i)
    touchdown_miss = float(
        np.linalg.norm(model_positions[-1, :2] - extrapolated_touchdown[:2])
    )
    continuation_duration = extrapolated_touchdown_time - float(times[interruption_i])
    continuation_times = np.arange(
        0.0, continuation_duration, EXPORT_DT
    ).tolist() + [continuation_duration]
    continuation = []
    for elapsed in continuation_times:
        point = observed_interruption + continuation_velocity * elapsed
        point[2] -= 0.5 * G * elapsed * elapsed
        continuation.append(
            [
                round(float(times[interruption_i] + elapsed), 4),
                *[round(float(value), 4) for value in point],
            ]
        )

    # Retain the old endpoint-to-ground result as a named legacy diagnostic so
    # old exports remain auditable. It must not be presented as interception
    # error: the two points can be at different heights and different events.
    legacy_endpoint_to_ground_miss = float(
        np.linalg.norm(model_positions[-1, :2] - positions[-1, :2])
    )
    cl = float(np.linalg.norm(magnus) * 2 * M / (RHO * A))
    model = [
        [round(float(t), 4), *[round(float(x), 4) for x in p]]
        for t, p in zip(model_times, model_positions)
    ]

    return {
        "ts": kick["ts"],
        "fit": "launch_to_apex",
        "fit_until_s": round(float(times[apex]), 3),
        "fit_samples": apex + 1,
        "fit_rms_m": round(rms, 4),
        "launch_speed_mps": round(float(np.linalg.norm(v0)), 3),
        "cd": round(cd, 5),
        "cl": round(cl, 5),
        "landing_time_s": round(float(model_times[-1]), 3),
        "interruption_time_s": round(float(times[interruption_i]), 3),
        "interruption_height_m": round(float(observed_interruption[2]), 3),
        "interruption_source": interruption_source,
        "interruption_velocity_change_mps": round(velocity_change, 3),
        "observed_interruption": [
            round(float(value), 4) for value in observed_interruption
        ],
        "model_same_height_time_s": round(comparison_time, 3),
        "model_at_interruption_height": [
            round(float(value), 4) for value in model_at_height
        ],
        "interruption_miss_m": round(interruption_miss, 3),
        "continuation_window_m": 3.0,
        "continuation_start_time_s": round(float(times[continuation_start_i]), 3),
        "extrapolated_touchdown_time_s": round(extrapolated_touchdown_time, 3),
        "extrapolated_touchdown": [
            round(float(value), 4) for value in extrapolated_touchdown
        ],
        "continuation_velocity_mps": [
            round(float(value), 4) for value in continuation_velocity
        ],
        "continuation": continuation,
        "touchdown_miss_m": round(touchdown_miss, 3),
        "legacy_endpoint_to_ground_miss_m": round(
            legacy_endpoint_to_ground_miss, 3
        ),
        "apex_index": apex,
        "model": model,
    }


def main() -> None:
    source = json.loads(INPUT.read_text())
    estimates = [fit_kick(kick) for kick in source["kicks"]]
    payload = {
        "method": {
            "name": "quadratic drag + constant Magnus",
            "fit_window": "first tracked flight sample through apex (inclusive)",
            "fit_uses_later_samples": False,
            "integrator": "RK4",
            "export_step_s": EXPORT_DT,
            "comparison": "model touchdown versus a ballistic continuation fitted from the final 3 m before the recorded interruption",
            "comparison_uses_post_interruption_samples": False,
        },
        "estimates": estimates,
    }
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")))

    print(f"wrote {len(estimates)} estimates -> {OUTPUT}")
    for estimate in estimates:
        print(
            f"{estimate['ts']}  fit {estimate['fit_until_s']:>5.2f}s / "
            f"{estimate['fit_samples']:>3} samples  "
            f"RMS {estimate['fit_rms_m'] * 100:>5.1f}cm  "
            f"Cd {estimate['cd']:>7.3f}  Cl {estimate['cl']:>6.3f}  "
            f"3m-continuation touchdown miss "
            f"{estimate['touchdown_miss_m']:>5.2f}m "
            f"({estimate['interruption_source']})"
        )


if __name__ == "__main__":
    main()
