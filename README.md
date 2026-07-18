# WIREGATE 26 research data

Versioned ball-only tracking extracts and independent physics calculations for
the Norway–England 2026 World Cup goal-kick incident.

**Read the [information letter](DATA_INFORMATION_LETTER.md) before using or
citing the data.** It explains where the coordinates came from, what the claim
can support, what it cannot establish, and the rights limitations.

This is an independent research and reporting package. It is not a FIFA, BBC,
Immersiv.io, team, player or match-official finding.

## Version 1.0 result in one paragraph

The public 205-sample flight is better fit by the tested impulse models than by
the tested smooth aerodynamic models: RMS position error is 18.20 cm for model
A, 15.46 cm for B, 7.364 cm for C and 5.770 cm for D. Model C's explicit
sample-cadence search selects a 1.1713 m/s velocity change 1.921 seconds after
launch. A like-for-like touchdown comparison places the three-metre recorded
continuation 2.1901 m from the no-impulse touchdown. This supports a localized
recorded discontinuity; ball tracking alone does not identify its cause.

The older 2.71 m endpoint comparison is superseded because it compared points
at different heights. See [METHODOLOGY.md](METHODOLOGY.md) and the complete
machine-readable result in `data/incident_analysis.json`.

## Quick reproduction

Python 3.12 is the reference runtime.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt

python scripts/verify_dataset.py
python scripts/analyze_incident.py
python scripts/compare_incident_analysis.py
python scripts/generate_kick_models.py
python scripts/compare_model_outputs.py
```

The analysis commands write ignored `*.regenerated.json` files and never
overwrite the published reference artifacts. GitHub Actions runs this sequence
on every push and pull request.

## Repository contents

| Path | Contents |
| --- | --- |
| `DATA_INFORMATION_LETTER.md` | Plain-language origin, intended use, claim limits and links |
| `data/incident_ball_track.csv` | 1,203 delivered ball samples over 24.084 seconds |
| `data/incident_analysis.json` | Reproducible A–D incident models, impulse localization and counterfactual |
| `data/kick_analysis_arcs.json` | 15 selected long-kick arcs; 14 form the in-play comparison |
| `data/kick_playback_tracks.json` | Fifteen five-second ball-only playback windows |
| `data/kick_models.json` | Launch-to-apex all-kicks physics fits and continuations |
| `data/kick_selection.json` | Disclosed selected timestamps and post-goal exclusion |
| `data/source_integrity.json` | Hashes and sizes for retained, undistributed source material |
| `data/manifest.json` | Distributed-file hashes, schemas, counts and timing |
| `schemas/` | JSON Schemas and the CSV data dictionary |
| `scripts/analyze_incident.py` | Reproduces the headline incident result |
| `scripts/generate_kick_models.py` | Reproduces the all-kicks comparison models |
| `scripts/extract_ball_track.py` | Rebuilds normalized ball CSV from lawfully held ATS files |
| `scripts/rebuild_extracts.py` | Rebuilds comparison JSON from a full ball CSV |
| `scripts/verify_dataset.py` | Validates hashes, schemas, counts, timing, coordinates and exclusions |

No player stream, skeleton data, video, audio, broadcast graphic, stadium model,
connected-ball IMU telemetry or official 3D asset is distributed.

## Rebuilding from locally held source files

The recorded source endpoint may be unavailable and the repository does not
grant rights to obtain or redistribute third-party files. If a researcher
lawfully possesses them, the public hashes and extraction path are:

```bash
python scripts/verify_source_files.py /path/to/segments \
  --manifest /path/to/stream.malt \
  --full-ball-csv /path/to/ball_full.csv

python scripts/extract_ball_track.py /path/to/segments/*.ats \
  --start-ms 1783806426627 --end-ms 1783806450711 \
  --output incident_ball_track.regenerated.csv

python scripts/rebuild_extracts.py /path/to/ball_full.csv
python scripts/compare_extracts.py
```

With the nine source segments recorded in `data/source_integrity.json`, the CSV
extract is byte-for-byte identical to `data/incident_ball_track.csv`. The full
ball CSV rebuilds both comparison JSON files exactly. Repeating the original
goalkeeper attribution requires undistributed player data; the resulting
selection is disclosed rather than presented as independently reproduced.

## Documentation

- [Information letter](DATA_INFORMATION_LETTER.md)
- [Methodology](METHODOLOGY.md)
- [Provenance and integrity](PROVENANCE.md)
- [Connected-ball IMU magnitude graphic](CONNECTED_BALL_EVIDENCE.md)
- [Data notice](DATA_NOTICE.md)
- [Independent review request](REVIEW_REQUEST.md)
- [Contributing and corrections](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Citation, release and licensing

Cite version `v1.0.0` and the full commit SHA; `CITATION.cff` provides
machine-readable metadata. Original scripts and documentation use the MIT
licence in `LICENSE-CODE`. That licence does not cover the third-party tracking
extracts under `data/`; no open-data licence is asserted for them. Read
[DATA_NOTICE.md](DATA_NOTICE.md) before reuse or redistribution.
