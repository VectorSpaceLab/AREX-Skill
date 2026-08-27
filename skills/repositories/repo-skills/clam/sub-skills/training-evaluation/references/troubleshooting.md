# CLAM Training and Evaluation Troubleshooting

Use this reference to diagnose common CLAM dataset, split, training, evaluation, and checkpoint failures.

## Dataset CSV Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing-column error or downstream KeyError | CSV lacks `case_id`, `slide_id`, or selected label column | Add required columns; use `label_col` only after adding a matching custom task branch. |
| KeyError for a label string | `label_dict` does not cover every non-ignored label value | Update `label_dict`, normalize CSV label spelling, or add values to `ignore`. |
| Slide features not found | `slide_id` includes extension, has changed zero padding, or does not match `pt_files/<slide_id>.pt` | Store basenames only and preserve IDs as strings. |
| Unexpected class counts | `patient_voting` collapsed multi-slide patient labels differently than expected | Use `patient_voting='max'` for MIL-style maximum label or `'maj'` for majority vote, then regenerate splits. |
| Train/val/test leakage by patient | Splits were generated without patient stratification | Generate splits with `patient_strat=True` for the split dataset branch before training. |

## Split Directory Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `assert os.path.isdir(args.split_dir)` in training | Default split path does not exist | Generate `splits/<task>_<label_frac_percent>` or pass `--split_dir` as a directory name under `splits/`. |
| Training cannot find `splits_3.csv` | `--k`, `--k_start`, `--k_end`, or `--fold` requests folds not present | Align requested folds with available `splits_<fold>.csv` files. |
| Custom `--split_dir` unexpectedly becomes `splits/splits/...` | `main.py` prefixes custom split names with `splits/` | Pass a directory basename relative to `splits/`, not an already-prefixed path. |
| Evaluation uses model directory as splits | `--splits_dir` omitted in `eval.py` | Ensure the model directory contains copied `splits_<fold>.csv`, or pass the cohort split directory explicitly. |

## Training Flag Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Assertion during multiclass CLAM task | CLAM subtyping branch requires `--subtyping` | Add `--subtyping` when training multiclass CLAM tasks. |
| `ModuleNotFoundError` for `topk.svm` | `--bag_loss svm` or `--inst_loss svm` requires `smooth-topk` | Install the optional dependency from CLAM environment guidance or use `ce` loss. |
| Checkpoint shape mismatch after feature change | `--embed_dim` does not match feature tensors or checkpoint | Use 1024 for ResNet50/UNI and 512 for CONCH; retrain if checkpoint was built with another dimension. |
| MIL fails on multiclass or binary task | Wrong MIL class implied by `n_classes` | Binary uses `MIL_fc`; multiclass uses `MIL_fc_mc`; ensure custom task sets `n_classes` correctly. |
| Results overwrite or mix experiments | Reused `--exp_code` and `--seed` under same `--results_dir` | Use unique experiment codes and keep seed suffixes visible. |
| TensorBoard logs missing | `--log_data` omitted or `tensorboardX` unavailable | Add `--log_data` and ensure `tensorboardX` is installed in the runtime environment. |

## Evaluation Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Model directory assertion fails | `--models_exp_code` does not identify a folder under `--results_dir` | Point `--results_dir` to the parent and `--models_exp_code` to the experiment directory such as `EXP_s1`. |
| Checkpoint file missing | Requested fold has no `s_<fold>_checkpoint.pt` | Align `--k`, `--k_start`, `--k_end`, or `--fold` with saved checkpoints. |
| State dict missing/unexpected keys | `--model_type`, `--model_size`, `--drop_out`, `--embed_dim`, or class count differs from training | Reconstruct the exact training model options before evaluating. |
| Poor or invalid AUC | Evaluation split contains one class only | AUC is `-1` when all labels are one class; use a balanced split or report accuracy instead. |
| Independent cohort labels fail | Evaluation task branch still points to bundled dummy CSV or wrong label mapping | Add a cohort-specific branch with the correct CSV, feature folder, and `label_dict`. |

## Task Customization Problems

The split, training, and evaluation entrypoints each hard-code task choices and dataset branches. A new task must be added consistently in all relevant entrypoints. If only one script is edited, users commonly see parser choice failures, missing split directories, wrong `n_classes`, wrong feature folder names, or checkpoint classifier shape mismatches.

For a new 3-class subtype task, the minimum consistent changes are:

1. Add one task name to `choices` in split, training, and evaluation scripts.
2. Set `n_classes=3` and a complete three-label `label_dict` in each branch.
3. Point split generation to the metadata CSV and training/evaluation to the feature folder.
4. Generate splits with the same task name and label fraction.
5. Train CLAM with `--subtyping` and the correct `--embed_dim`.

## Heavy Runtime Caveats

Training and evaluation may require large feature tensors, GPU memory, checkpoint files, and optional native/system packages. For command review, use the bundled builders first; run the original CLAM commands only in a prepared CLAM environment with the required data and checkpoints.
