# AutoML bridge

This sub-skill covers the small glue layer that translates between PocketFlow and the AutoML job format used by the source repo. It does not explain the learner search space itself; see `../../compression-learners/SKILL.md` for the meaning of the `ws_*` knobs.

## Files in the source tree

| File | Role |
| --- | --- |
| `automl/automl.yaml` | AutoML job metadata, search-space bounds, and result keys |
| `automl/automl_hparam.conf` | Placeholder template for generated hyper-parameters |
| `run.sh` | Source Seven-based job wrapper that connects the template, job run, and result parsing |

## Bundled helpers

- `scripts/cvt_automl_hparams.py` converts a generated hparam file into PocketFlow CLI flags.
- `scripts/parse_automl_results.py` extracts `object_value`, `prune_ratio`, and `loss` from TensorFlow log output.

## Supported parameter names

| Name | Meaning |
| --- | --- |
| `ws_prune_ratio_exp` | pruning ratio exponent used by weight sparsification |
| `ws_iter_ratio_beg` | beginning fraction of the sparsification schedule |
| `ws_iter_ratio_end` | ending fraction of the sparsification schedule before normalization |
| `ws_update_mask_step` | mask update interval |

The conversion helper normalizes `ws_iter_ratio_end` so the end of the schedule is measured from the remaining iterations, matching the source script.

## Expected workflow

1. Let AutoML fill `automl_hparam.conf` or a generated hparam file.
2. Run `python scripts/cvt_automl_hparams.py <file>` to obtain the PocketFlow flag fragment.
3. Run the PocketFlow job with those flags.
4. Feed the resulting TensorFlow log to `python scripts/parse_automl_results.py <log>`.

## Limitations

- Missing placeholders are reported as errors instead of being silently defaulted.
- The result parser expects the TensorFlow log tags used by the source project.
- The wrapper is reference-only for Seven-specific execution; the bundled helpers are the safe operating path here.
