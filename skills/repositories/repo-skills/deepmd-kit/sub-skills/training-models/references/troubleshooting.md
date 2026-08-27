# DeePMD-kit Training Troubleshooting

Use this matrix for model/back-end-aware training failures. Route raw data repair to `data-config`, post-freeze inference/model testing to `inference-model-ops`, and deployment/build issues to `integrations-development`.

## Fast Triage

1. Identify backend flag, model family, and command actually used.
2. Check whether the failure occurs before data loading, during neighbor statistics, during the first training step, after several steps, during checkpoint/freeze, or only in distributed mode.
3. Inspect the input sections that match the failure: `model`, `loss`/`loss_dict`, `training`, `learning_rate`, `optimizer`, and fine-tune flags.
4. Confirm that tutorial water data is only being used for smoke testing.
5. Prefer a single-process, low-step reproduction before changing a distributed production job.

## Failure Matrix

| Symptom | Likely causes | Actions |
| --- | --- | --- |
| CLI rejects backend/model combination | Descriptor or fitting target not supported by selected backend; backend package missing; typo in backend alias. | Run `dp --<backend> -h`; choose supported backend from model-selection; use explicit flags `--tf`, `--pt`, `--jax`, or `--pd`. |
| Input parser rejects training file | Invalid JSON/YAML, wrong top-level schema for single vs multi-task, misspelled keys. | Validate JSON/YAML syntax; compare section shape against [training-workflows.md](training-workflows.md); do not start training until parser passes. |
| Missing label error or `nan` metric for a target | Loss prefactor is nonzero but data lacks matching label, e.g. force, virial, DOS, property, tensor, spin, or Hessian. | Set prefactor to zero only if the target should not be trained; otherwise route label/data creation to `data-config`. |
| NaN or exploding losses | Learning rate too high, bad labels/units, overlapping atoms, too-small `sel`, unstable fine-tune, mixed precision issue. | Stop long run; inspect early `lcurve.out`; lower `start_lr`, verify labels/units, rerun neighbor-stat, use bounded smoke steps, check data anomalies. |
| Validation flat or much worse than training | Validation split distribution differs, data leakage/imbalance, model too small/large, loss weights poor. | Compare train/validation system summaries; adjust splits/weights only after data validation; consider stronger model or regularization. |
| Neighbor-stat fails or auto `sel` disabled | Data paths wrong, type map mismatch, `--skip-neighbor-stat` used with `sel: auto`, cutoff/type list mismatch. | Fix systems/type map; run explicit `dp --<backend> neighbor-stat`; remove `--skip-neighbor-stat` when automatic `sel` is needed. |
| Training is extremely slow on CPU | Production training is GPU-oriented; DPA models are expensive; neighbor-stat/stat collection may dominate startup. | Treat CPU as smoke only; reduce `numb_steps` for validation; recommend GPU/distributed resources for production. |
| Checkpoint not found on restart | Passed frozen model instead of checkpoint prefix, wrong working directory, backend suffix mismatch. | Locate checkpoint files; use `--restart` only with checkpoint prefix; use frozen model path with `--finetune` only when supported. |
| Freeze fails after training | Wrong backend flag, wrong checkpoint folder/prefix, missing multi-task head, custom op/deployment constraint. | Freeze with same backend; pass `--checkpoint-folder` if needed; use `--head`/`--model-branch` for multi-task; route deployment-specific op issues. |
| `dp show ... model-branch` errors | Model is single-task. | Do not pass branch options; for multi-task, verify the checkpoint/frozen model is actually multi-task. |
| Multi-task branch/head not selected | `--model-branch` omitted for fine-tune, `--head` omitted for freeze, branch name typo. | Inspect available branches with `dp --pt show MODEL model-branch`; pass exact branch or explicitly choose `RANDOM`. |
| Type-map mismatch in fine-tuning | Downstream elements not subset/compatible with pretrained model, different order, missing observed types. | Compare `type_map`; use pretrained-compatible order; call out random initialization for new/missing types; route data type-map repair if uncertain. |
| `--use-pretrain-script` fails | Pretrained model lacks embedded model definition or backend cannot extract it. | Re-freeze/recreate model with compatible metadata if possible; otherwise match descriptor/fitting input exactly to pretrained model. |
| Built-in pretrained download fails | No network, unavailable model name in installed version, cache path not writable. | Use `dp pretrained download -h` for names; ask before network access; use existing cache path; avoid claiming download happened unless confirmed. |
| Distributed launch hangs/fails | Launcher mismatch, GPU/process mismatch, rendezvous/network issue, file locking/data loader contention. | Reproduce single-process; match launcher to backend; check `CUDA_VISIBLE_DEVICES`, `--nproc_per_node`, scheduler allocation, shared filesystem, and backend-specific env vars. |
| PyTorch ZeRO/FSDP error | `zero_stage` unsupported setting, not launched with `torchrun`, incompatible optimizer/model mode. | Use distributed launch; start with lower `zero_stage`; avoid unsupported optimizer/config combinations. |
| Paddle distributed data stalls | Too many workers, HDF5/file-locking issue, GPU list mismatch. | Try `NUM_WORKERS=0`, `HDF5_USE_FILE_LOCKING=0`, and explicit `--gpus`; verify data access on each node. |
| Hessian model cannot provide frozen Hessian outputs | PyTorch JIT/export limitation for Hessian-trained models. | Clarify that Hessian training and frozen-model Hessian output are different; route inference expectations to `inference-model-ops`. |

## Backend/Model Mismatch Notes

- DPA3 is documented for PyTorch, JAX, and DP-model style use; use PyTorch for ordinary training/fine-tuning unless the user explicitly selects another supported backend.
- DPA4 / SeZM is PyTorch-oriented in current docs; do not draft TensorFlow/JAX/Paddle DPA4 commands unless the installed version proves support.
- Multi-task training is primarily PyTorch. TensorFlow multi-task support is deprecated.
- DPLR is a TensorFlow-oriented long-range workflow and usually requires prerequisite dipole/Wannier-center modeling.
- Spin support changes `sel` and virtual-type behavior differently across TensorFlow and PyTorch/DP. Verify backend-specific assumptions.
- Tensor/DOS/property fitting require labels and fitting/loss types that match the target; do not reuse energy-only loss blindly.

## Loss And Label Diagnostics

| Loss setting | Required labels | If absent |
| --- | --- | --- |
| `start_pref_e` / `limit_pref_e` nonzero | Energy labels. | Energy training is invalid; route data. |
| `start_pref_f` / `limit_pref_f` nonzero | Force labels. | Set force prefactors to zero only for intentional energy-only training. |
| `start_pref_v` / `limit_pref_v` nonzero | Virial labels. | Set virial prefactors to zero or add virial data. |
| Hessian prefactors | Full Hessian arrays. | Do not use Hessian loss. |
| DOS loss | DOS/atomic DOS arrays matching `numb_dos`. | Route data; output dimension must match labels. |
| Property loss | `{property_name}.npy/raw` matching `task_dim`. | Route data; do not guess property name. |
| Tensor loss | Dipole/polar labels with configured selection/global mode. | Route data; match tensor shape and `sel_type`. |
| Spin loss | Spin-related labels/settings for selected backend. | Route data/model config; confirm virtual-type behavior. |

## Fine-Tuning Troubleshooting

Fine-tuning has extra compatibility checks:

1. **Model source:** Is the source a checkpoint, frozen file, or built-in pretrained name? Use the correct flag.
2. **Architecture:** Without `--use-pretrain-script`, the input model section must match the pretrained model. With it, the model must embed a usable definition.
3. **Type map:** Downstream data types should be contained in or compatible with the pretrained model type map. New types may get random parameters and should be reported.
4. **Branch:** Multi-task pretrained models need a branch/head selection unless random fitting is intentional.
5. **Learning rate:** Fine-tuning should usually start lower and run fewer steps than training from scratch.
6. **Cache/network:** Built-in pretrained names may require download; never assume network access.

## Multi-Task Troubleshooting

| Problem | Check |
| --- | --- |
| Task key error | Same keys in `model.model_dict`, `loss_dict`, and `training.data_dict`. |
| Shared descriptor not found | `model.shared_dict` key names and `descriptor` references match exactly. |
| Head freeze error | Use exact branch name from `dp --pt show MODEL model-branch`; pass `--head` or `--model-branch`. |
| Poor downstream fine-tune | Verify `finetune_head`, task sampling weights, retained pretrained data, and lower learning rate. |
| Random head unexpectedly used | Confirm `--model-branch` was not omitted or set to `RANDOM`. |

## Distributed Troubleshooting

Start from the single-process command generated by `draft_training_command.py`; then layer the launcher:

- PyTorch: `torchrun --nproc_per_node=N --no-python dp --pt train input.json`.
- TensorFlow: `horovodrun -np N dp --tf train input.json` or site MPI wrapper.
- Paddle: `python -m paddle.distributed.launch --gpus="0,1,..." dp --pd train input.json`.

If distributed execution fails:

1. Run one process on one GPU with the same input.
2. Verify every rank can read data and write checkpoints.
3. Confirm `nproc_per_node` equals intended visible GPUs.
4. Capture backend log mode where available, such as MPI worker logs or PyTorch distributed debug env vars.
5. Avoid modifying model architecture and launcher at the same time.

## Safe Recovery Pattern

When a training run fails, return a bounded recovery plan:

- Exact failing command and backend.
- First failing phase: parse, data load, neighbor-stat, first step, later training, checkpoint, freeze, distributed launch.
- Most likely root cause and one evidence point.
- Minimal config/command change to test next.
- Whether to route to data validation or post-freeze inference.
- Whether the next run is smoke-only or production-intended.
