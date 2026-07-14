# Provenance and integrity record

Recorded 14 July 2026. This document records origin and transformations; it is
not a licence or statement of permission.

## Editorial delivery source

- Publisher: BBC Sport
- Experience: [FIFA World Cup 3D experience](https://www.bbc.co.uk/sport/football/articles/c62dy77g8e8o)
- Experience provider: Immersiv.io
- Experience host: `https://3d-bbc.co.uk`
- Tracking event ID: `285023`
- Match ID: `151706`
- Source manifest: `https://fwc26-bbc-prod.r2.immersiv.cloud/tracking/285023/default/151706/scrubbed/stream.malt`
- Local acquisition record date: 12 July 2026

The BBC experience described its content as official FIFA tracking and used
Immersiv.io technology. WIREGATE 26 is not affiliated with or endorsed by FIFA,
the BBC or Immersiv.io.

## Scope reduction

The complete source stream is not included. This repository contains only:

- A 24.084-second incident ball extract.
- Fifteen short ball-only kick windows needed to reproduce the comparison.
- Independent derived model output.

Player coordinates, skeletons, video, audio, broadcast graphics, connected-ball
imagery and stadium geometry are excluded.

The incident extract retains raw normalized pitch coordinates. Kick trajectories
were converted to metres using a 105.03 by 68.03 metre pitch. Relative kick
times start at zero for each extracted window.

Run `python3 scripts/verify_dataset.py` to compare every distributed data file
with the SHA-256 values in `data/manifest.json`.
