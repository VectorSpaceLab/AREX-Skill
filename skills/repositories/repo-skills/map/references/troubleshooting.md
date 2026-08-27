# Cross-cutting troubleshooting

This file covers problems that cut across the three mAP sub-skills.

## Missing `numpy`

If the evaluation helper fails before doing any work, the active environment is
missing `numpy` or is using the wrong Python. Install `numpy` in the runtime
being used for the generated skill and rerun the bundled helper.

## Wrong folder chosen

Symptoms:
- empty GT or DR directory errors
- no matching basenames
- a class missing from both folders

Route:
- Use `data-validation` to inspect the exact folders and class tokens.
- Use `conversion` if the files are not evaluator `.txt` files yet.

## Output directory already exists

The evaluator wrapper refuses to overwrite a non-empty output directory unless
`--overwrite` is supplied. This is intentional.

Fix:
- choose a new output directory for each comparison run, or
- confirm that the old directory is disposable and rerun with `--overwrite`.

## Optional visualization failures

Plotting and animation are optional. If the user does not need PNG plots or
annotated frames, rerun without the optional flags.

- `matplotlib` missing -> rerun without plots or install it.
- `opencv-python` missing -> rerun without animation or install it.

## Legacy script safety

The source repository contains small legacy scripts that assume a fixed checkout
layout and may move or rename files. The generated skill uses bundled helpers
with explicit paths and safer defaults.

If a future agent is tempted to use the source scripts directly, route the task
to the bundled sub-skill helper instead.

## Evaluation errors that are really data problems

If AP/mAP fails with missing-file or malformed-row messages, do not guess at the
metric. Fix the data layout first:

- class lookup or basename mismatch -> `data-validation`
- unsupported source annotation format -> `conversion`
- evaluator-ready inputs with metric errors -> `evaluation`
