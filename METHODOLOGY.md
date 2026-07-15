# Methodology

## Coordinate systems

`incident_ball_track.csv` preserves the delivered incident extract:

- `ts_ms`: source timestamp in milliseconds.
- `x`: normalized position along a 105.03 metre pitch.
- `y`: normalized position across a 68.03 metre pitch.
- `z`: delivered ball height in metres.

Convert the normalized incident coordinates to pitch metres with:

```text
pitch_x_m = x * 105.03
pitch_y_m = y * 68.03
height_m  = z
```

Trajectory rows in the JSON files are already converted to pitch metres and
have the form:

```text
[relative_time_s, pitch_x_m, pitch_y_m, height_m]
```

The website maps these coordinates into a y-up 3D scene as
`(pitch_x_m, height_m, -pitch_y_m)`.

## Kick extraction

Long airborne spans were detected from the full source ball stream using a
height threshold of 1 metre, a minimum 2.2 second duration and a minimum
6 metre apex. The player nearest the ball at each launch was used only during
local attribution to identify kicks by the same goalkeeper. No player entity
identifiers or coordinate samples are distributed; only the delivered team code
and shirt number used to describe the selected taker remain in the arc metadata.

The `s` arrays in `kick_analysis_arcs.json` are horizontal distances projected
onto each kick's launch-to-end direction. The paired `z` arrays are delivered
heights. The `traj` arrays retain the corresponding 3D pitch-frame positions.

Fifteen extracted windows are retained for auditability. The window beginning
at `1783811397013` is excluded from the in-play comparison because it is a
restart after the deciding goal. The other 14 form the comparison displayed by
the site.

## Derived physical model

Two related analyses are published and should not be conflated.

### Incident model comparison

`scripts/analyze_incident.py` uses the 205-sample incident flight from source
timestamp `1783806435336` through `1783806439420`. It fits four models to the
complete flight: constant aerodynamics (A), exponential Magnus decay (B), A
plus one velocity impulse (C), and B plus an impulse at the model-C time (D).

Impulse time is discrete. The script first searches a 0.2-second grid and then
every recorded sample boundary within 0.25 seconds of the coarse minimum. All
continuous parameters are refitted from the same initial state at every
candidate. This avoids describing a discontinuous change time as though a
gradient optimizer could estimate it continuously.

The no-impulse counterfactual uses model C's fitted launch and aerodynamic
parameters with the fitted impulse removed. For a like-for-like touchdown, the
final three recorded metres before interruption are fitted by least squares and
continued ballistically to a ball-centre height of 0.11 m. The published result
is the horizontal distance between those two touchdown points.

`data/incident_analysis.json` contains the fitted parameters, A–D errors,
impulse-time sensitivity curve, recorded flight and counterfactual. The source
did not provide covariance or filtering metadata, so the project does not
convert optimizer curvature into a formal confidence interval.

### All-kicks comparison

`scripts/generate_kick_models.py` fits each kick only from its first tracked
sample through its first sustained apex. Later samples do not enter the
optimizer.

The acceleration model is:

```text
a = gravity - k |v| v + |v| (w × v)
```

It uses quadratic drag, a constant Magnus vector and RK4 integration. Launch
position, launch velocity, drag coefficient and the Magnus vector are fitted
by nonlinear least squares. The exported comparison is between:

1. The model touchdown predicted from the launch-to-apex fit.
2. A short ballistic continuation fitted from the final 3 metres before the
   first detected interruption or the end of the recorded arc.

The second continuation is a local extrapolation, not a separately observed
landing position. The model is exploratory and its assumptions are not unique.

The all-kicks fit uses launch-to-apex samples and answers a different comparison
question from the full-flight A–D incident analysis. Its incident touchdown
number should not be substituted for the versioned incident result without
stating the different fit window.

## Limitations

- Sensor accuracy, filtering and error bounds were not supplied with the
  delivered extract.
- A coordinate discontinuity may be physical or may be a tracking artefact.
- The exact cable geometry, height, sag and tension are not public measurements.
- The dataset contains no raw connected-ball IMU telemetry.
- The comparison set was selected by algorithmic thresholds and should not be
  treated as every possible goalkeeper action in the match.

Independent analyses should report sensitivity to smoothing, derivative
windows, interruption thresholds and physical-model assumptions.
