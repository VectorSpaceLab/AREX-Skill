# Results and Logs

## Purpose

Read this when you need to summarize a completed run or locate the files that
`system/main.py` produces.

## Saved outputs

The server base class writes the main experiment artifacts using paths relative
to `system/`:

- `models/<dataset>/<algorithm>_server.pt`
- `../results/<dataset>_<algorithm>_<goal>_<run>.h5`

The h5 result file stores:

- `rs_test_acc`
- `rs_test_auc`
- `rs_train_loss`

## Text-log summary helper

The legacy `system/get_mean_std.py` script reads a `.out` file, finds repeated
`Best accuracy` blocks, and prints the accuracy list plus mean and standard
deviation.

The bundled `scripts/summarize_results.py` helper accepts either h5 results or
text logs and prints a safer summary without requiring a manual re-parsing of
output text.

## `result_utils.py`

`system/utils/result_utils.py` computes the same kind of summary for h5 files
across repeated runs.

Use it when you want the best accuracy statistics for a batch of runs.

## Checklist for a completed run

- `main.py` printed the best accuracy and average round time.
- The h5 result file exists in the expected results directory.
- Any optional model checkpoint exists under `models/<dataset>/`.
- The summary helper can read the run output without parsing errors.
