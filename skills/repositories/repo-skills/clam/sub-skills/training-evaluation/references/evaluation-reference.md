# CLAM Evaluation Reference

Use this reference when running `eval.py` on trained CLAM or MIL checkpoints, including evaluation on independent cohorts.

## Command Shape

A typical evaluation command is:

```bash
CUDA_VISIBLE_DEVICES=0 python eval.py \
  --data_root_dir DATA_ROOT_DIR \
  --results_dir results \
  --models_exp_code task_1_tumor_vs_normal_CLAM_50_s1 \
  --save_exp_code task_1_tumor_vs_normal_CLAM_50_s1_cv \
  --task task_1_tumor_vs_normal \
  --model_type clam_sb \
  --k 10 \
  --embed_dim 1024
```

Evaluation loads checkpoints from `<results_dir>/<models_exp_code>/s_<fold>_checkpoint.pt` and writes outputs under `eval_results/EVAL_<save_exp_code>/`.

## Key Flags

| Flag | Purpose | Evidence-backed behavior |
| --- | --- | --- |
| `--data_root_dir` | Root containing feature dataset subfolders | Must point to the feature bags for the evaluation cohort. |
| `--results_dir` | Directory containing model experiment folders | Defaults to `./results`. |
| `--models_exp_code` | Model experiment directory name | Joined with `--results_dir` to form `models_dir`. |
| `--save_exp_code` | Evaluation output label | Output directory becomes `eval_results/EVAL_<save_exp_code>`. |
| `--splits_dir` | Split directory for evaluation | If omitted, defaults to `models_dir`; otherwise must contain `splits_<fold>.csv`. |
| `--task` | Selects evaluation dataset branch and class count | Must match the intended cohort labels and feature subfolder branch. |
| `--model_type` | `clam_sb`, `clam_mb`, or `mil` | Must match the checkpoint architecture. |
| `--model_size` | CLAM size, `small` or `big` | Must match training for CLAM checkpoints. |
| `--drop_out` | Dropout passed to model construction | Must match checkpoint architecture. |
| `--embed_dim` | Input feature width | Must match the checkpoint and feature tensors. |
| `--k`, `--k_start`, `--k_end`, `--fold` | Fold selection | `--fold` evaluates one fold; otherwise the selected range is evaluated. |
| `--split` | Cohort subset | Choices are `train`, `val`, `test`, and `all`; default is `test`. |
| `--micro_average` | Multiclass AUC mode | Uses micro-average instead of macro-style mean of one-vs-rest AUCs. |

## Outputs

Evaluation writes:

```text
eval_results/EVAL_SAVE_EXP_CODE/
  eval_experiment_SAVE_EXP_CODE.txt
  fold_0.csv
  summary.csv
```

Each `fold_<fold>.csv` includes `slide_id`, true label `Y`, predicted label `Y_hat`, and probability columns `p_0`, `p_1`, ... for each class. The summary file includes `folds`, `test_auc`, and `test_acc`; partial ranges use `summary_partial_<first>_<last>.csv`.

## Checkpoint Expectations

`eval.py` constructs checkpoint paths as:

```text
<results_dir>/<models_exp_code>/s_<fold>_checkpoint.pt
```

The model is rebuilt from CLI flags, then `load_state_dict(..., strict=True)` is used after removing `instance_loss_fn` keys. Architecture mismatches surface as missing keys, unexpected keys, or tensor-size errors. Confirm these fields before evaluation:

- `--model_type` matches training (`clam_sb`, `clam_mb`, or `mil`).
- `--model_size`, `--drop_out`, and `--embed_dim` match training.
- `--task` implies the same `n_classes` as the checkpoint classifier head.
- For MIL, binary checkpoints use `MIL_fc`; multiclass checkpoints use `MIL_fc_mc` indirectly when `n_classes > 2`.

## Independent Cohort Evaluation

To evaluate an external cohort:

1. Prepare the cohort CSV with the same label semantics and a feature folder with `pt_files/<slide_id>.pt`.
2. Add or select an evaluation task branch that points to the cohort CSV and feature subfolder.
3. Provide split files for the cohort, or use `--split all` if evaluating every slide without fold split filtering.
4. Keep `--models_exp_code` pointed at the original checkpoint directory and `--save_exp_code` unique for the cohort run.
5. Keep `--embed_dim` aligned to the features used by the checkpoint, not just the external cohort preference.

For public handoffs, record that evaluation can be heavy because it loads every selected feature bag and model checkpoint.
