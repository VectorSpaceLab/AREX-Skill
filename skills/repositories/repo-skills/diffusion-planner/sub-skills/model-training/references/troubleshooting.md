# Training troubleshooting matrix

Start with the first failing contract, not the last stack frame. Capture the
command, active environment, `CUDA_VISIBLE_DEVICES`, world size, local batch,
normalization path, one manifest entry, and checkpoint key names.

| Symptom | Likely contract | Recovery |
|---|---|---|
| `FileNotFoundError` for a list item | `train_set_list` contains a name not found under `train_set` | Print the resolved `data_dir/item`; fix the manifest/data root. Do not add a second root or silently duplicate data. |
| JSON decode/type error | List is not valid JSON or top-level value is not a list | Make the file a JSON array of `.npz` filenames. Validate with the bundled checker. |
| `KeyError` from a worker | `.npz` lacks one of the 11 required keys | Re-run the model-ready data producer or route to data-preparation. Do not invent fields in this skill. |
| `RuntimeError` in a linear layer/attention | Feature axis or model flags disagree | Compare all axes with `args.json`/CLI: time 21, lane points 20, route lanes 25, hidden 192, heads 6 by default. |
| `batch_size` local shape or empty loader | Global batch is not divisible by world size | Choose `batch_size % WORLD_SIZE == 0`; remember the script uses integer floor division and `drop_last=True`. |
| `invalid device ordinal` | More ranks than visible GPUs or wrong CUDA remapping | Match `--nproc-per-node` to visible devices. With `CUDA_VISIBLE_DEVICES=4,5`, ranks still address local devices 0 and 1. |
| NCCL initialization/hang | CUDA/NCCL process or stale rank/port state | First run one GPU with `--ddp false`; ensure no stale `RANK`, `WORLD_SIZE`, or worker group; choose a free `--port`; retry with matching visible GPUs. |
| `Address already in use` | `MASTER_PORT`/`--port` is occupied | Stop the failed job's workers or choose another port consistently. The helper sets `MASTER_ADDR=localhost` for torchrun. |
| `torch.cuda.synchronize` or CUDA OOM | Full training was attempted without enough GPU memory or with bad device state | Confirm CUDA and GPU visibility, reduce local batch/model dimensions only for a new run, and use `--num_workers 0` to separate loader failures. CPU checks do not validate NCCL training. |
| `nuplan` import from augmentation | `StatePerturbation` uses Pacifica vehicle parameters | Use `--use_data_augment false` for a limited parser/API smoke, or repair the full training environment. This is not a normalization failure. |
| `NaN` loss assertion | Non-finite/mis-normalized data, wrong heading conversion, or invalid std | Validate finite `.npz` values and positive normalization stds; check zero masks and cos/sin conversion before changing optimizer settings. |
| model loads but EMA is absent | Checkpoint lacks `ema_state_dict` or resume was run with EMA disabled | Continue only if non-EMA behavior is intended; record that EMA evaluation cannot be reproduced. |
| `latest.pth` not found on resume | `--resume_model_path` points to the file, not its directory | Pass the directory; `resume_model` appends `latest.pth`. |
| missing/unexpected keys at resume | Architecture/parameterization mismatch or DDP prefix conversion | Compare checkpoint sibling `args.json` with current flags. Use an explicit, reviewed key conversion; do not use broad `strict=False` as a repair. |
| optimizer/schedule starts fresh | Optional checkpoint keys are absent/incompatible | The loader intentionally continues; report a warm-start rather than a true resume and decide whether to reset the run name. |
| `args.json` serialization failure | A non-serializable runtime object was added to argparse args | Keep config fields JSON-compatible; normalizers are converted by the training script, but custom objects are not. |
| logger fails after setup | Rank-0 save path is not writable or W&B/TensorBoard setup is broken | Test a writable temporary `--save_dir`, keep `--use_wandb false`, and verify `tb/` creation. |
| `UnboundLocalError` for `model_ema` or `ema.update` after `--use_ema false` | Current entrypoint assigns EMA only in the true branch but `train_epoch` updates it unconditionally | Keep EMA enabled, or make an explicit reviewed code patch that initializes/guards EMA and checkpoint saving before retrying. |
| model output has wrong trajectory count | `predicted_neighbor_num` changes state/normalizer/decoder shapes | Match this value across data slicing, normalization, model config, and checkpoint; ego is always index 0. |
| generated trajectory is unnormalized or physically odd | State normalizer/checkpoint args mismatch | Load the matching `args.json`; inverse normalization is done by the decoder only in eval mode. |

## DDP recovery order

1. Stop the failed job's child processes and remove no checkpoints unless the
   user explicitly asks. Do not resume from a partially written file while a
   writer is still alive.
2. Run the native help and bundled checker.
3. Run a one-GPU `--ddp false`, `--num_workers 0` contract/API check with a tiny
   local fixture and no augmentation if necessary.
4. Check `torch.cuda.is_available()`, device count, and visible-device mapping.
5. Relaunch with a free port, explicit matching process count, divisible global
   batch, and the same args/paths on every rank.
6. Only then investigate model memory or checkpoint compatibility.

## Checkpoint key triage

The standard checkpoint keys are `epoch`, `model`, `ema_state_dict`,
`optimizer`, `schedule`, `loss`, and `wandb_id`. The loader accepts either a
wrapper containing `model` or a bare state dict. It separately attempts the
optional keys, so a successful `Model load done` is not proof that optimizer,
scheduler, epoch, and EMA state were restored. Verify the printed load messages
and retain the exact `args.json` used to construct the model.

## Non-goals

- nuPlan scenario/map preprocessing and data acquisition: use
  `../data-preparation/SKILL.md`;
- planner/closed-loop simulation and NuBoard: use
  `../closed-loop-planning/SKILL.md`;
- custom classifier/collision guidance: use `../guidance/SKILL.md`.
