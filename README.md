# WIREGATE 26 research data

This repository contains the limited, ball-only tracking extracts used by
[WIREGATE 26](https://wiregate26.com) to examine the Norway–England 2026 World
Cup goal-kick incident and compare it with other long kicks by the same
goalkeeper.

It is published so researchers, physicists, journalists and interested readers
can reproduce the comparisons and challenge the project's interpretation. It
contains no player skeleton streams, video, broadcast graphics, stadium models
or official 3D assets.

## Repository contents

| File | Contents |
| --- | --- |
| `data/incident_ball_track.csv` | 1,203 recorded ball samples covering 24.084 seconds around the incident |
| `data/kick_analysis_arcs.json` | 15 detected long-kick arcs, 3,174 samples and 63.245 aggregate seconds |
| `data/kick_playback_tracks.json` | Fifteen five-second ball-only playback windows, 3,749 samples and 74.774 aggregate seconds |
| `data/kick_models.json` | Independent, derived physics fits and short continuations used by the comparison viewer |
| `data/manifest.json` | File descriptions, counts and SHA-256 integrity values |
| `scripts/generate_kick_models.py` | Regenerates comparable model output from the analysis arcs |
| `scripts/compare_model_outputs.py` | Compares regenerated numerical output with the published model |
| `scripts/verify_dataset.py` | Checks hashes, schemas and declared sample counts |

The dataset contains 15 extracted kick windows. Fourteen are used in the
in-play comparison. The restart at source timestamp `1783811397013` occurred
after the deciding goal and is retained for auditability but explicitly marked
as excluded from the competitive comparison.

## Verify the files

```bash
python3 scripts/verify_dataset.py
```

To regenerate the derived model:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/generate_kick_models.py
python3 scripts/compare_model_outputs.py
python3 scripts/verify_dataset.py
```

Regeneration writes `data/kick_models.regenerated.json`; it never overwrites the
exact model artifact used by the site. Nonlinear optimizer results can differ
slightly across NumPy/SciPy versions, so the comparison checks structure and a
1.1 millimetre maximum numerical tolerance rather than requiring the files to
have identical bytes.

## Interpretation warning

Tracking coordinates can reveal an unusual recorded change in a trajectory.
They cannot, by themselves, establish whether its cause was cable contact,
aerodynamics, a player interaction or a tracking artefact. The physical model
and every conclusion drawn from it are independent WIREGATE 26 calculations,
not FIFA, BBC or Immersiv.io findings.

See [METHODOLOGY.md](METHODOLOGY.md) for coordinate definitions and modelling
details, [PROVENANCE.md](PROVENANCE.md) for the acquisition record, and
[DATA_NOTICE.md](DATA_NOTICE.md) before redistributing the data.

## Licensing

The scripts and original documentation are available under `LICENSE-CODE`.
That licence does **not** cover the underlying third-party tracking extracts.
No open-data licence is asserted for those extracts; see `DATA_NOTICE.md`.
