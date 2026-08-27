# Evaluation troubleshooting

Use these checks in order. The helpers fail closed with a concise message and
nonzero exit status; they do not edit session logs.

## `missing required log` or `transitions` errors

Confirm that the argument is the session root, not its `transitions/` child:

```text
SESSION/transitions/executed-action.log.txt
SESSION/transitions/reward-value.log.txt
SESSION/transitions/clearance.log.txt
```

`evaluate_session.py` requires all three files. `plot_session.py` requires
the first two and, in automatic method mode, a `models/` directory with a
regular filename containing `reactive` or `reinforcement`. If snapshots are
not available, pass `--method reactive` or `--method reinforcement` explicitly.
A filename is used only as a method marker; the helper does not load weights.

## Empty, truncated, or misaligned files

A one-row action file is normalized to one action row, but all rows still need
a first column. Reward values must be finite and cover every action row used by
the evaluator. The evaluator reports the file path and row counts when these
lengths disagree. Do not pad with zeros: recover the interrupted run or
choose a clearly bounded prefix outside the helper, then document the choice.
The plot helper follows the source's exclusion of two trailing action rows and
therefore needs at least three action rows after validation.

## Bad action IDs or clearance boundaries

Column 0 must contain only exact `0` or `1`; other values usually indicate a
wrong file (for example a predicted-value log) or a corrupted append. A
clearance endpoint must be an integer in `[1, number_of_action_rows]`, and
endpoints must be strictly increasing. An endpoint is the end of a half-open
trial, not a count to add again. If a reset was logged before any action, the
source format cannot represent a zero-length trial; repair or omit that
malformed interval rather than changing the metric formula.

## All trials fail or no grasp appears

This can be a genuine policy result. With positive `N`, a push-only or
zero-success session has 0% completion and undefined completion-conditioned
grasp/action metrics. Check the chosen method before interpreting it: reactive
uses `reward == 0`, whereas reinforcement uses `reward >= 0.5`. Do not apply
the reinforcement threshold to reactive class labels. If a non-completed trial
has no grasp attempts, inspect it as a diagnostic; the helper reports the
undefined per-trial rate in its JSON/text details rather than inventing a
zero denominator.

## Unexpected completion or efficiency

Verify that `--num_obj_complete` is the number of objects required by the test
case and is positive. The helper counts successful **grasp rows** in each
clearance interval, not object names, pushes, reward sums, or the number of
preset files. Completion is intended to occur before the reset condition
of more than 10 consecutive failed/no-change attempts. Action efficiency is
`N / all actions in the completed trial`; pushes therefore lower efficiency.
The clearance name is historical and does
not mean every row was a successful clearance.

## Plot is blank, clipped, or fails without a display

Always provide `--output results/performance.png`; the helper creates parent
folders and uses the `Agg` backend. A blank-looking first segment is expected:
the source warm-up scales points before 200 by `step / 200`. The plotted range
also stops at `min(action_rows - 2, --max-plot-iteration)`. Increase
`--max-plot-iteration` only when enough rows exist, and use a positive
`--interval-size` no larger than the available history for interpretable
curves. The dashed line counts only a grasp immediately after a push.

## Historical compatibility boundary

The source checkout is Python 2/early Python 3 and has no package metadata.
The bundled scripts are standalone Python helpers. A bounded current numerical
stack check can validate their offline behavior, but passing helper checks does
not prove the original training loop, historical model snapshots, simulator,
GUI, RealSense server, or UR5 path works unchanged. Keep those operations in
their owning routes and resolve service/version failures there.

For a quick safe diagnostic, let `<skill-root>` mean the directory containing
the root `SKILL.md`, then run:

```bash
python <skill-root>/sub-skills/evaluation/scripts/evaluate_session.py --help
python <skill-root>/sub-skills/evaluation/scripts/plot_session.py --help
```

Then use a copied synthetic session. Never modify the original logs merely to
satisfy a parser.

- [`../SKILL.md`](../SKILL.md) — route selection and scope.
- [`metrics-and-logs.md`](metrics-and-logs.md) — source formulas and file
  semantics.
- [`../scripts/evaluate_session.py`](../scripts/evaluate_session.py) and
  [`../scripts/plot_session.py`](../scripts/plot_session.py) — standalone
  validators/helpers.
