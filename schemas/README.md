# Data dictionary

All JSON trajectories use `[relative_time_s, pitch_x_m, pitch_y_m, height_m]`.
Pitch coordinates are metres in the delivered pitch frame. Source timestamps
are Unix milliseconds. Arrays are ordered by increasing time.

## `kick_analysis_arcs.json`

- `taker.team`, `taker.num`: delivered team code and shirt number used for the
  selected goalkeeper; no player position samples are included.
- `ts`: source timestamp of the first trajectory row.
- `t_min`: approximate match-stream minute relative to the locally retained
  source origin.
- `ours`: true only for the investigated 45+1 kick.
- `apex_m`, `dur_s`: delivered maximum height and recorded arc duration.
- `s`: horizontal displacement projected onto the launch-to-end direction.
- `z`: delivered height paired with `s`.
- `traj`: four-column 3D trajectory rows.
- `strike_i`: illustrative alignment index retained only on the incident kick;
  it is not a source measurement of cable position or contact.

## `kick_playback_tracks.json`

- `source`: provenance label for the locally retained full ball CSV.
- `window_s`: requested playback duration.
- `tracks[].ts`: selected launch timestamp.
- `tracks[].traj`: up-to-five-second delivered ball trajectory.

## `kick_models.json`

This file is produced by `scripts/generate_kick_models.py`. Important fields:

- `fit_until_s`, `fit_samples`, `fit_rms_m`: launch-to-apex fit boundary and error.
- `cd`, `cl`: fitted dimensionless drag and lift coefficients.
- `interruption_*`: first detected velocity discontinuity or track end.
- `model_at_interruption_height`, `interruption_miss_m`: like-height comparison.
- `continuation_*`, `extrapolated_touchdown`: three-metre local continuation.
- `touchdown_miss_m`: horizontal distance between model and continued touchdown.
- `legacy_endpoint_to_ground_miss_m`: retained audit field; not a like-for-like result.
- `model`: no-interruption model trajectory.

## `incident_analysis.json`

- `source`: exact published flight window and illustrative alignment timestamp.
- `method`: model definitions, grid search and uncertainty qualification.
- `results.model_rms_cm`: full-flight A–D position errors.
- `selected_impulse_*`, `impulse_*`: model-C discrete change time and vector.
- `same_height_*`: model and recording compared at the interruption height.
- `continuation_*`, `extrapolated_touchdown`: final-three-metre continuation.
- `no_impulse_touchdown`: model-C launch/aerodynamics integrated without impulse.
- `touchdown_horizontal_miss_m`: like-for-like version 1.0 touchdown result.
- `impulse_time_sensitivity`: coarse-grid RMS and impulse magnitude at every time.
- `recorded_flight`, `no_impulse_counterfactual`: plotted trajectories.

## Selection and integrity records

`kick_selection.json` records every chosen launch, analysis sample count, in-play
status and exclusion reason. `source_integrity.json` records the name, role,
byte size and SHA-256 of source files retained privately. `manifest.json`
records the corresponding properties for every distributed data file.

The machine-enforced JSON Schemas live beside this document. CSV constraints
are described in `incident-ball-track.md` and implemented in
`scripts/verify_dataset.py`.
