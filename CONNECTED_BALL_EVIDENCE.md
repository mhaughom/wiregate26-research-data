# Connected-ball IMU magnitude graphic

This note records a separately published graphic concerning the disputed
Norway–England kick. It is contextual evidence only. The repository does not
contain the underlying connected-ball telemetry.

## Public source

- Publisher: Dale Johnson, BBC Sport
- Post: [X status 2076406878167261575](https://x.com/DaleJohnsonBBC/status/2076406878167261575)
- Graphic title: `Ball 12 IMU — Miami Stadium, Norway vs England, 2026-07-11`
- Labelled time: approximately 46 minutes of the first half, 17:47 EDT / 21:47 UTC
- Recorded here: 18 July 2026

The published graphic contains two magnitude plots over approximately 4.5
seconds:

1. `Acceleration magnitude`, labelled `acc_norm (g)`.
2. `Gyroscope magnitude`, labelled `gyro (rot/s)`.

The visible gyroscope magnitude settles near 9.5 rotations per second after the
Norway launch contact and declines smoothly to approximately 8.5 rotations per
second before the England reception. No abrupt change in gyroscope magnitude is
visually apparent during the airborne interval.

These values are approximate readings from the displayed graph. They are not
machine-readable samples and should not be represented as raw FIFA telemetry.

## What the graphic can and cannot establish

The gyroscope magnitude is consistent with substantial rotation throughout the
flight. It makes a near-zero-spin knuckleball interpretation less plausible.
It does not identify the spin axis, however. Magnitude alone cannot establish
backspin, distinguish backspin from a tilted combination of backspin and
sidespin, or exclude a change in spin-axis direction that preserves total
angular speed.

The acceleration trace is also not documented sufficiently to treat it as a
raw accelerometer-vector norm. adidas states that the TRIONDA 500 Hz IMU is
mounted inside one of the ball's four panels rather than at its centre:

- [Official adidas TRIONDA technical description](https://news.adidas.com/football/adidas-unveils--trionda----the-official-match-ball-of-the-fifa-world-cup26-/s/27042e3a-12ba-482d-8839-8a96e056b33e)

An off-centre accelerometer in a rapidly spinning rigid ball experiences large
rotational acceleration. The near-zero airborne baseline in the published
graphic therefore indicates that compensation, filtering, transformation or a
contact-detection metric may have been applied. The processing method, sensor
range, noise floor and detection threshold have not been published with the
graphic.

## Use in trajectory modelling

WIREGATE 26 may use the approximate 9.5-to-8.5 rotations-per-second magnitude
as a sensitivity constraint when testing plausible aerodynamic models. Any such
model must vary the unknown spin-axis direction and aerodynamic coefficients,
fit only pre-event trajectory samples, and report uncertainty. The graphic does
not justify fixing the spin axis as known backspin.

Conclusive analysis would require synchronized raw samples containing at least
timestamps, three accelerometer axes and three gyroscope axes, together with the
sensor mounting calibration and all filtering or compensation steps.
