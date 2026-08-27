---
name: evaluation
description: "Validate completed Visual Pushing and Grasping sessions and
  produce source-compatible metrics or headless training curves from transition
  logs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Evaluation

Use this route after a VPG test or training session has produced a session
folder. It owns offline session-log validation, the completion/grasp/action-
efficiency measurements, and the training-curve plot. It does **not** train a
model, start V-REP/CoppeliaSim, move a UR5, or capture camera data.

## Choose the operation

Let `<skill-root>` mean the directory containing the root `SKILL.md`.

- **Report a completed test session:** run the bundled helper
  `<skill-root>/sub-skills/evaluation/scripts/evaluate_session.py`. It accepts
  the source-compatible flags `--session_directory`, `--method`, and
  `--num_obj_complete`; add `--format json` for machine-readable output or
  `--output PATH` to save the text/JSON report.
- **Plot one or more training sessions:** run the bundled helper
  `<skill-root>/sub-skills/evaluation/scripts/plot_session.py` with one or
  more positional session directories and `--output PATH`. It uses
  Matplotlib's `Agg` backend and never requires a display. By default it uses
  the source interval of 200 steps and x-axis maximum of 2,500 steps; override
  them with `--interval-size` and `--max-plot-iteration`.

Read [`references/metrics-and-logs.md`](references/metrics-and-logs.md) before
interpreting a result, and use
[`references/troubleshooting.md`](references/troubleshooting.md) when a log
layout, method, or plotting error is reported. The two helpers are bundled
standalone artifacts adapted from the historical evaluation and plotting
programs; they are not a claim that the original full training loop is
modern-runtime compatible.

## Required session contract

`SESSION` is the root directory created for one logging run. It must contain:

```text
SESSION/
  transitions/
    executed-action.log.txt
    reward-value.log.txt
    clearance.log.txt       # required by evaluate_session.py
  models/                   # needed for plot auto method detection
```

`logger.py` writes the transition files as whitespace-separated text. Each
executed-action row has at least four values; column 0 is the primitive ID:
`0` for push and `1` for grasp. Reward rows are scalar values aligned to the
same action history. A clearance value is an integer action/iteration index at
which the workspace is reset for the next trial. In the documented test
interpretation, completion is expected before more than 10 consecutive
failed/no-change attempts trigger that reset. The evaluator prepends a
zero boundary, so trial `i` is the half-open range
`[clearance[i-1], clearance[i])`.

The helper validates finite values, aligned action/reward lengths, legal
primitive IDs, monotonic in-range clearance boundaries, and nonempty trials.
Failures name the offending file or boundary and explain the expected layout.
Paths are resolved from the caller's current directory, so both helpers run
from an arbitrary working directory and do not import repository modules.

## Method and threshold

Pass `--method reactive` for the supervised/classification policy or
`--method reinforcement` for the Q-learning policy. The same grasp action has
different success evidence:

- reactive: a grasp is successful when its reward/class value equals `0`;
- reinforcement: a grasp is successful when its reward value is at least
  `0.5` (the source evaluator's threshold).

Set `--num_obj_complete N` to the positive number of successful grasps needed
to count a trial as completed. Do not infer this number from the number of
objects in a preset. A trial is valid for the three aggregate metrics only
when its counted grasp successes are at least `N`; pushing contributes actions
but never success count.

## Report interpretation

The evaluator preserves the source formulas and prints the three README
metrics (all percentages, higher is better):

1. average completion/clearance rate over all trials;
2. average grasp success rate, restricted to completed trials;
3. average action efficiency, `100 * mean(N / actions_in_completed_trial)`.

For source compatibility it also reports the diagnostic grasp-to-push ratio,
`100 * mean(grasp_attempts / all_actions)` over completed trials. If no trial
completes, the restricted metrics are reported as `undefined`/`null` with a
warning rather than emitting an unhelpful divide-by-zero or NaN. This is a
valid negative result, not evidence that the logs are malformed.

## Plot interpretation

`plot_session.py SESSION [SESSION ...] --output PATH` draws a solid grasp
success curve and a dashed push-then-grasp success curve for each session.
The curves use the preceding `interval_size` action attempts and preserve the
source's warm-up scaling for steps before 200. The plot uses at most
`min(number_of_action_rows - 2, max_plot_iteration)` rows, matching the source
program's exclusion of two trailing action rows whose rewards may not yet be
available. A model filename containing `reactive` or `reinforcement` selects
the method; pass `--method` to override detection when no model snapshot is
available. The output is a PNG by default (or the format implied by the output
suffix) and is written without `plt.show()`.

## Boundaries and provenance

This operating route was distilled from source commit
`580e2334beec0d83b49e6ca89d7542b79d1d4350`, especially the historical
`evaluate.py`, `plot.py`, `logger.py`, README evaluation instructions, and
`main.py` clearance logging. Bounded checks with a current Python numerical
stack can validate the bundled offline helpers, but do not establish a modern
full-loop training, simulator, or robot run. See [`references/metrics-and-logs.md`](references/metrics-and-logs.md)
for formulas and [`references/troubleshooting.md`](references/troubleshooting.md)
for recovery steps.
