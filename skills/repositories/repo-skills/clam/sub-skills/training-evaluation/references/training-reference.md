# CLAM Training Reference

Use this reference to assemble and explain `main.py` training commands. CLAM training reads existing feature `.pt` bags and split CSVs; it does not segment slides or extract features.

## Command Shape

A typical CLAM training command is:

```bash
CUDA_VISIBLE_DEVICES=0 python main.py \
  --data_root_dir DATA_ROOT_DIR \
  --task task_1_tumor_vs_normal \
  --model_type clam_sb \
  --exp_code task_1_tumor_vs_normal_CLAM_50 \
  --k 10 \
  --drop_out 0.25 \
  --early_stopping \
  --lr 2e-4 \
  --weighted_sample \
  --bag_loss ce \
  --inst_loss svm \
  --log_data \
  --embed_dim 1024
```

For multiclass CLAM subtyping, add `--subtyping`. For CONCH features, set `--embed_dim 512`; for ResNet50 or UNI features, set `--embed_dim 1024`.

## Key Flags

| Flag | Purpose | Evidence-backed behavior |
| --- | --- | --- |
| `--data_root_dir` | Root containing feature dataset subfolders | Built-in task branches append task-specific feature folder names. |
| `--task` | Selects dataset branch and class count | Bundled choices are `task_1_tumor_vs_normal` and `task_2_tumor_subtyping`; custom tasks require parser and branch edits. |
| `--model_type` | Chooses `clam_sb`, `clam_mb`, or `mil` | CLAM models use attention and optional instance clustering; MIL uses top-instance baselines. |
| `--model_size` | `small` or `big` for CLAM | MIL ignores model size. |
| `--embed_dim` | Input feature width | Must match upstream encoder output: 1024 for ResNet50/UNI, 512 for CONCH. |
| `--exp_code` | Experiment name | Output directory becomes `<results_dir>/<exp_code>_s<seed>`. |
| `--results_dir` | Root output directory | Defaults to `./results`; created if missing. |
| `--k`, `--k_start`, `--k_end` | Fold count and fold range | Reads `splits_<fold>.csv` for each selected fold. |
| `--split_dir` | Custom split directory name under `splits/` | If omitted, training uses `splits/<task>_<label_frac_percent>`. |
| `--label_frac` | Training label fraction | Also influences default split directory name. |
| `--max_epochs` | Epoch cap | Defaults to 200. |
| `--lr`, `--reg`, `--opt` | Optimizer controls | `--opt` choices are `adam` and `sgd`. |
| `--drop_out` | Dropout probability passed to models | Defaults to 0.25 in CLI; verified constructors default to 0.0. |
| `--weighted_sample` | Use weighted sampling in loaders | Useful for class imbalance. |
| `--early_stopping` | Stop on validation loss plateau | Patience is 20, with stopping only after epoch 50. |
| `--log_data` | Enable TensorBoard logging | Uses `tensorboardX.SummaryWriter` under the fold output directory. |
| `--testing` | Debug loader mode | Reduces loader work for debugging. |
| `--bag_loss` | Slide-level loss | Choices are `ce` or `svm`; `svm` imports `SmoothTop1SVM` from `smooth-topk`. |
| `--inst_loss` | CLAM instance clustering loss | Choices are `ce`, `svm`, or `None`; `svm` also requires `smooth-topk`. |
| `--no_inst_cluster` | Disable CLAM instance clustering | Uses standard training loop instead of CLAM instance loop. |
| `--bag_weight` | CLAM bag-vs-instance loss weight | Default is 0.7. |
| `--B` | Positive/negative patches sampled for CLAM instance loss | Passed as `k_sample` when greater than 0. |
| `--subtyping` | Mark CLAM as a subtyping problem | Required by the bundled multiclass CLAM training branch. |

## Outputs

For `--results_dir results --exp_code EXP --seed 1`, training writes to:

```text
results/EXP_s1/
  experiment_EXP.txt
  splits_0.csv
  s_0_checkpoint.pt
  split_0_results.pkl
  summary.csv
  0/                 # TensorBoard events when --log_data is set
```

For partial fold ranges, the aggregate file is named `summary_partial_<start>_<end>.csv`. `summary.csv` includes `folds`, `test_auc`, `val_auc`, `test_acc`, and `val_acc`.

## Loss and Metric Behavior

- Binary AUC uses class-1 probability.
- Multiclass AUC uses one-vs-rest ROC AUC during training summaries.
- `summary()` reports per-class accuracy counts after validation and test evaluation.
- Early stopping saves the best validation-loss checkpoint as `s_<fold>_checkpoint.pt`; without early stopping, the final epoch state is saved to the same path.

## Custom Task Training Notes

The bundled `main.py` is not data-driven from a config file. To train a custom task, edit the working script or maintain a local fork so `--task` selects the correct CSV, feature subfolder, `label_dict`, and `n_classes`. Keep the same task name across split generation, training, evaluation, and output bookkeeping.
