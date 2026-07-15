# Information letter for researchers, journalists and data users

**Dataset:** WIREGATE 26 ball-only research data, version 1.0.0  
**Date:** 15 July 2026  
**Repository:** <https://github.com/mhaughom/wiregate26-research-data>  
**Project:** <https://wiregate26.com>  
**Contact and corrections:** <contact@wiregate26.com>

## Why this package exists

This package lets independent researchers inspect and challenge an unusual
recorded change in the flight of a goal kick during Norway–England at the 2026
FIFA World Cup. It publishes the limited ball coordinates needed for that
review, comparison windows from other long kicks by the same goalkeeper, the
independent physics code, integrity hashes and the assumptions behind the
interpretation.

The package is an independent work of reporting and technical analysis. It is
not a FIFA, BBC, Immersiv.io, team, player or match-official finding, and none of
those parties is presented as endorsing it.

## Where the coordinates came from

The coordinates were delivered to a web browser by the BBC Sport FIFA World Cup
3D experience. The experience was described by the BBC as providing a new 3D
way to replay matches with player data. The delivery host identified the event
as `285023`, match `151706`, and used an Immersiv.io tracking path.

Recorded links:

- [BBC Sport description of the 2026 3D experience](https://www.bbc.co.uk/sport/football/articles/c62dy77g8e8o)
- [FIFA overview of Electronic Performance and Tracking Systems](https://football-technology.fifa.com/innovation/standards/epts)
- [FIFA explanation of 2026 connected-ball and optical tracking](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/gueye-pina-connected-ball-technology-leader-boards)
- [Immersiv.io](https://immersiv.io)
- [Recorded source manifest](https://fwc26-bbc-prod.r2.immersiv.cloud/tracking/285023/default/151706/scrubbed/stream.malt)
- [Project rights and provenance page](https://wiregate26.com/rights)

The recorded source manifest was accessible when the data was acquired on 12
July 2026. It returned HTTP 403 when rechecked on 15 July 2026. The repository
therefore publishes SHA-256 hashes and sizes for the retained manifest, the nine
ATS segments that produce the incident extract, and the locally extracted full
ball stream. Those source files are not redistributed here.

## What the data is—and is not

The CSV and JSON coordinates are approximately 50 Hz delivered ball positions.
They are not the ball's internal 500 Hz inertial-measurement-unit stream. No raw
connected-ball IMU telemetry is included. The repository also excludes player
coordinates, skeletons, video, audio, broadcast graphics, stadium geometry and
official 3D assets.

The incident CSV contains 1,203 samples over 24.084 seconds. The modelled flight
uses 205 samples from the kick through the final pre-interruption sample. The
comparison package contains 15 selected kick windows; 14 are in-play
comparisons, while one post-goal restart is retained but marked as excluded.

## What the version 1.0 calculation says

Four models are fitted to the recorded incident flight:

- A: constant quadratic drag and constant Magnus vector;
- B: A with exponential Magnus decay;
- C: A with one velocity impulse at a tracking-sample boundary; and
- D: B with one impulse at the model-C selected boundary.

The impulse time is selected by a disclosed grid search at the native sample
cadence. It is not treated as a differentiable optimizer parameter. Version
1.0 obtains RMS position errors of 18.20 cm for A, 15.46 cm for B, 7.364 cm for
C and 5.770 cm for D. Model C selects a 1.1713 m/s velocity change 1.921 seconds
after launch. That is 95 milliseconds after the cable-alignment time used in
the illustrative reconstruction; the cable geometry and alignment are not
measured data.

For a like-for-like landing comparison, the final three metres before the
recorded interruption are fitted and continued ballistically to ball-centre
ground height. The resulting touchdown is 2.1901 metres horizontally from the
model-C no-impulse touchdown. This replaces the project's older 2.71 metre
endpoint comparison, which compared points at different heights and should not
be cited as the version 1.0 like-for-like result.

These results support the narrower statement that the recorded flight contains
a localized change that the tested impulse models fit better than the tested
smooth aerodynamic models. They do **not** establish what caused that change.
Cable contact is one hypothesis; tracking artefact, filtering, an unmodelled
aerodynamic effect or another interaction must remain alternatives unless
independent evidence resolves them.

## Appropriate uses

Appropriate uses include:

- reproducing or attempting to falsify the calculations;
- testing alternative smoothing, aerodynamic or change-point models;
- checking the coordinate and timing conversions;
- reporting the analysis with its limitations and counter-positions; and
- teaching reproducible sports-data analysis.

The package should not be represented as official officiating evidence,
conclusive proof of cable contact, a complete match dataset, a statement about
player fault, or an openly licensed upstream data source. Commercial reuse or
redistribution of the third-party coordinates requires an independent rights
assessment.

## Known limitations

- The delivered coordinates did not include sensor covariance, accuracy,
  filtering or latency metadata, so no formal confidence interval is claimed.
- The physical model is exploratory and does not exhaust possible aerodynamic
  or tracking-error models.
- Player data used locally to attribute comparison kicks is not distributed;
  the selected timestamps are disclosed so the ball-only windows can be rebuilt.
- Exact cable position, sag, tension and time alignment are not public
  measurements.
- The source endpoint may be unavailable even though local source hashes remain
  verifiable.

## Reproduction, citation and corrections

Start with [README.md](README.md), then read [METHODOLOGY.md](METHODOLOGY.md),
[PROVENANCE.md](PROVENANCE.md) and [DATA_NOTICE.md](DATA_NOTICE.md). Cite the
version tag and full commit SHA. Machine-readable citation metadata is in
`CITATION.cff`.

Independent disagreement is welcome. A correction should identify the release
or commit, affected file, method and reproducible evidence. Public technical
reports may use the scientific-review issue template; sensitive rights or
privacy concerns may be sent to <contact@wiregate26.com>.
