# EPDMS and PDM scoring reference

## Score structure

NAVSIM v2's Extended Predictive Driver Model Score (EPDMS) has four
multiplicative compliance metrics and five weighted metrics. The multiplicative
terms are:

- **NC**: no at-fault collisions, with values 0, 0.5, or 1;
- **DAC**: drivable-area compliance, 0 or 1;
- **DDC**: driving-direction compliance, 0, 0.5, or 1;
- **TLC**: traffic-light compliance, 0 or 1.

The weighted terms are **EP** ego progress, **TTC** time-to-collision within
bound, **LK** lane keeping, **HC** history comfort, and **EC** two-frame
extended comfort. Default weights are:

| Term | Default weight | Role |
|---|---:|---|
| EP | 5 | weighted |
| TTC | 5 | weighted |
| LK | 2 | weighted |
| HC | 2 | weighted |
| EC | 2 | weighted |

For a planner score `m` and human reference score `h`, the false-positive
filter uses `1.0` for a metric when `h == 0`; otherwise it retains `m`. Thus,
with the filter applied to each term:

```text
EPDMS = product(NC, DAC, DDC, TLC)
        * (5*EP + 5*TTC + 2*LK + 2*HC + 2*EC) / 16
```

The implementation stores the weighted values and the weight vector in each
result row. A multiplicative failure can zero the whole score even when the
weighted terms are strong. Conversely, the weighted average cannot repair a
multiplicative violation. Human-penalty filtering is only meaningful where a
human trajectory is available; synthetic follow-up scenes do not have the same
human future reference.

The row fields include each subscore, the multiplicative product, the weighted
arrays, and the preliminary `pdm_score`. Read the final `score` after stage
aggregation, not only the preliminary field.

## Metric behavior and thresholds

The default scorer configuration defines these operational thresholds:

- progress normalization threshold: 5 m;
- driving-direction horizon: 1 s;
- DDC compliance below 2 m of oncoming progress and violation at 6 m;
- stopped-speed TTC threshold: 0.005 m/s;
- future collision horizon for TTC: 1 s;
- lane-keeping lateral deviation limit: 0.5 m sustained for a 2 s window.

DDC accumulates oncoming progress over the configured horizon and ignores
intersection positions. LK is disabled on intersections where centerline
annotations can disagree with perceived lane markings; outside those areas it
is a weighted term and can be zero while multiplicative compliance remains one.
HC evaluates comfort using the current plan plus the ego motion history. EC
compares overlapping simulated states from adjacent frames and is supplied by
the scene aggregator after the ordinary PDM metrics have been computed.

## Why the preliminary score differs from final score

`PDMScorer` computes NC/DAC/TLC/DDC, EP/TTC/LK/HC, and a preliminary weighted
score while deliberately excluding EC because EC needs the neighboring frame.
The result still carries the EC slot and its weight. `run_pdm_score.py`, the
submission scorer, and the one-stage adjacency path fill EC, recompute the
weighted average, and multiply by the multiplicative product. A CSV that only
shows the preliminary PDM field is not evidence that extended comfort was
included.

## Trajectory transformation and simulation

An agent returns `Trajectory.poses` in local rear-axle coordinates as
`(x, y, heading)` rows. The trajectory dataclass requires a two-dimensional
array with exactly three columns and a row count equal to its
`TrajectorySampling.num_poses`. The evaluator transforms those relative SE(2)
poses to absolute poses using the initial ego rear axle, creates an
`InterpolatedTrajectory`, and prepends the initial ego state. It intentionally
ignores predicted velocity and acceleration when building that interpolated
trajectory: the PDM LQR tracker and batch kinematic bicycle model determine the
simulated ego dynamics.

The evaluator samples both the cached PDM reference and the transformed agent
trajectory at the simulator's `proposal_sampling` times, beginning at the
initial time and clipping query times to the interpolated trajectory bounds.
The resulting arrays have shape `(proposals, num_poses + 1, state_size)` before
simulation. The simulator and scorer assert the same proposal sampling and the
same `num_poses + 1` state length. Therefore:

1. set the agent's declared trajectory sampling to its actual output;
2. cover the full configured 4 s horizon;
3. keep simulator, scorer, and cache proposal sampling consistent;
4. if changing the 40 x 0.1 s default, change every affected config and rebuild
   the cache rather than relying on interpolation to hide a mismatch.

A trajectory that has the wrong pose count, too short a horizon, or a different
sampling declaration is a contract failure, even if its first few poses look
reasonable. See [configuration](configuration.md) for override examples.

## Four-second simulation

The default proposal sampling is 40 future poses at 0.1 s, representing a
four-second horizon plus the initial state in evaluator arrays. The PDM
simulator uses an LQR tracker to follow each proposal and propagates the ego
state with a batch kinematic bicycle model. Background traffic is then supplied
by the selected traffic policy before PDMScorer evaluates map, collision,
traffic-light, direction, progress, TTC, lane, and comfort metrics.

This is pseudo closed loop: the ego commits to one plan, and the planner is not
recalled based on simulated observations. In two-stage evaluation, precomputed
follow-up scenes approximate what a closed-loop continuation would see.
