# Metrics and transition logs

This reference is the compact evidence record for the evaluation route. The
runtime helpers are linked at the end so a Researcher can reproduce or inspect
the exact offline behavior without the original checkout.

## Session layout and units

`logger.py` creates a timestamped session directory (or reuses one when
continuing) with these output areas:

```text
info/                         camera and heightmap metadata
data/                         image outputs
  color-images/               RGB images
  depth-images/               depth PNGs
  color-heightmaps/           RGB heightmaps
  depth-heightmaps/           depth heightmaps
models/                       snapshots
visualizations/               optional prediction images
recordings/                   optional RGB-D recordings
transitions/                  scalar logs below, plus transitions/data/ depth PNGs
```

The logger stores depth images as unsigned 16-bit PNG values after multiplying
metres by `10,000` (1e-4 m), heightmaps and transition depth PNGs after
multiplying by `100,000` (1e-5 m). Those image scales are not applied to the
scalar evaluator: it reads only the whitespace-separated transition logs.
It writes lists using `numpy.savetxt(..., delimiter=' ')`. The evaluator needs:

| File | Shape/meaning | Unit or scale |
|---|---|---|
| `executed-action.log.txt` | one row per executed primitive; column 0 is action ID, columns 1--3 are rotation/pixel coordinates | action ID `0` push, `1` grasp; coordinates are indices, not metres |
| `reward-value.log.txt` | one scalar per logged transition | method-dependent class/reward value; no image/depth scaling |
| `clearance.log.txt` | one scalar endpoint per completed/reset trial | integer action/iteration index, not a percentage |

The evaluator uses the action and reward histories from index zero. It
prepends boundary `0` to the clearance endpoints. Endpoint `e` is exclusive,
so a trial with boundaries `s,e` consumes rows `s:e`; the endpoint row is the
first row of the following interval. Endpoints are emitted by the main loop
when the table is empty or, in simulation testing, when more than 10
consecutive failed/no-change attempts cause a reset. They are not per-action
success labels.

The plotting helper intentionally follows the source plot program's
`action_rows - 2` limit, because the historical loop can leave two trailing
action rows without corresponding rewards. The evaluator itself preserves the
source evaluator's full action-row behavior and validates that rewards cover
those rows. Do not silently concatenate logs from multiple sessions: each
session has its own clearance origin.

## Method-specific grasp success

The source training code returns/records values that are interpreted
differently:

- **reactive:** `reward_value` is a classification-like label. A grasp
  succeeds exactly when `reward == 0`.
- **reinforcement:** `reward_value` is an MDP/Q-learning signal. A grasp
  succeeds when `reward >= 0.5`; a successful grasp's immediate reward is 1.0
  in the source trainer, while a successful push can contribute 0.5. The
  evaluator only applies the threshold to rows whose action ID is `1`.

A push reward does not count as a grasp success. Thus a large reinforcement
reward on a push cannot make a trial complete.

## Per-trial formulas

For trial `t`, let `A_t` be all action rows in its clearance interval, `G_t`
the rows whose action ID is `1`, and `S_t` the method-specific successful
subset of `G_t`. Let `N` be `--num_obj_complete`.

```text
number of actions before completion = len(A_t)
grasp success rate_t = len(S_t) / len(G_t)
grasp-to-push ratio_t = len(G_t) / len(A_t)
completed_t = (len(S_t) >= N)
action efficiency_t = N / len(A_t), only when completed_t
```

The source names the first aggregate “clearance” even though the criterion is
successful grasp count. The three README metrics are:

```text
average completion (%) = 100 * sum(completed_t) / number_of_trials
average grasp success per completion (%) =
    100 * mean(grasp success rate_t for completed_t)
average action efficiency (%) =
    100 * mean(N / len(A_t) for completed_t)
```

The source evaluator additionally prints:

```text
average grasp-to-push ratio (%) =
    100 * mean(grasp-to-push ratio_t for completed_t)
```

The bundled evaluator retains this fourth value as a diagnostic. It does not
replace any of the three reported metrics. If no trial completes, restricted
means have no mathematical value; the helper emits `undefined` in text and
`null` plus a warning in JSON. A zero-grasp interval cannot be completed when `N` is positive and is
reported with an actionable per-trial warning; its grasp-rate field is
`null` rather than an invented zero. This avoids the source's undefined division
while preserving the source formula for ordinary trials.

## Plot curves and warm-up behavior

The historical plot uses `interval_size = 200` and
`max_plot_iteration = 2500`. At each step `k`:

1. collect grasp attempts with action index `< k`, retain the latest
   `interval_size` attempts, and divide successful values by
   `min(interval_size, max(k, 1))`;
2. for `k < interval_size`, multiply the result by `k / interval_size`;
3. repeat the same operation for grasps immediately following a push (a row
   with action `0` followed by a row with action `1`);
4. draw the ordinary grasp curve solid and the push-then-grasp curve dashed.

The helper also validates a positive interval and max iteration, uses a fixed
color palette, and writes with Matplotlib `Agg`. It never opens a GUI. A
session's method is inferred deterministically from sorted regular filenames
in `models/`; a filename containing `reactive` or `reinforcement` is enough.
Use `--method` as an explicit override for a log-only fixture.

## Exact commands

Source-compatible evaluation flags are exposed by the bundled helpers. Let
`<skill-root>` mean the directory containing the root `SKILL.md`:

```console
python <skill-root>/sub-skills/evaluation/scripts/evaluate_session.py \
  --session_directory SESSION \
  --method reactive|reinforcement \
  --num_obj_complete N
```

Additional helper flags are `--format text|json` and `--output PATH`. Plot
inputs are positional, matching the source:

```console
python <skill-root>/sub-skills/evaluation/scripts/plot_session.py SESSION [SESSION ...] \
  --output performance.png \
  [--method auto|reactive|reinforcement] \
  [--interval-size 200] [--max-plot-iteration 2500]
```

Both `--help` surfaces are safe and require no model, simulator, or robot.

- [`../scripts/evaluate_session.py`](../scripts/evaluate_session.py) —
  validated formula implementation.
- [`../scripts/plot_session.py`](../scripts/plot_session.py) — headless
  training-curve implementation.
- [`troubleshooting.md`](troubleshooting.md) — actionable failures and
  recovery ordering.
