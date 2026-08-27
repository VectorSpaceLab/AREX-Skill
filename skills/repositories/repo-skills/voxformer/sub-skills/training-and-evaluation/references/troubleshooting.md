# Troubleshooting

Use the symptom and the command contract first. Do not retry a full run until
preflight explains the failure and the operator has approved any new output
path or resource request.

## CLI/API misuse

- **Test exits with “Please specify at least one operation”:** add exactly one
  of `--eval`, `--format-only`, `--show`, `--show-dir`, or `--out`. For this
  repository, prefer `--eval` or `--show-dir`; `--out` currently reaches an
  assertion after printing its write message.
- **`--eval` and `--format-only` conflict:** these are explicitly rejected by
  `tools/test.py`; choose evaluation or formatting.
- **Output suffix error:** `--out` must end in `.pkl` or `.pickle`, but the
  current write path is not verified. Use a distinct `--show-dir`/`--tmpdir`
  and keep a log of the command.
- **Both `--options` and `--cfg-options` or both `--options` and
  `--eval-options`:** use the non-deprecated spelling only once. Quote MMCV
  list/tuple values without embedded whitespace.
- **Unexpected `bbox` evaluation:** `dist_test.sh` appends `--eval bbox` for
  historical generic MMDetection behavior. Use direct `tools/test.py` with the
  intended SSC metric or update the wrapper only as an explicitly reviewed
  repository change.
- **Help/import failure:** run `python tools/train.py --help` and
  `python tools/test.py --help` only after environment preparation. A parser
  check is safe; it does not prove model, dataset, CUDA op, or evaluator
  execution.

## Config and data mismatch

- **Stage-2 dataset cannot find queries:** inspect the config's
  `query_tag` (standard presets use `query_iou5203_pre7712_rec6153`) and the
  corresponding stage-2 `queries/*.query...` files. A differently suffixed
  query file is missing for this config even if a query file with another tag
  exists.
- **Wrong stage:** QPN uses `SemanticKittiDatasetStage1`; S/T uses
  `SemanticKittiDatasetStage2`. Do not pass a stage-1 config to a stage-2
  checkpoint or treat generated stage-1 model weights as stage-2 query files.
- **Temporal/camera mismatch:** T uses five cameras and temporal offsets
  `[-12,-9,-6,-3]`; S uses one camera and no temporal offsets. Images and
  sequence frames must support the selected setup. Route model changes to
  `model-configuration`, not ad-hoc CLI guesses.
- **Missing labels or preprocess artifacts:** stop before launch and route to
  `dataset-preparation`. The training tool builds datasets immediately and will
  fail after allocating resources if the layout is incomplete.
- **Config silently changes work directory:** CLI `--work-dir` wins over the
  config. If neither is set, `train.py` derives a `./result/voxformer/...`
  directory. Preflight and confirm ownership before relying on defaults.
- **Validation unexpectedly runs:** validation is enabled by default. Use
  `--no-validate` only when intentionally postponing it; this is not a way to
  bypass missing validation data in a claimed evaluation.

## Checkpoint and resume problems

- **Checkpoint not found:** `test.py` requires an existing checkpoint path;
  `train.py --resume-from` is only assigned when `osp.isfile()` is true. Use
  an absolute or correctly rooted path and re-run preflight.
- **Wrong checkpoint/config:** compare stage, model family, camera/temporal
  variant, custom-op variant, input dimensions, and saved config metadata. A
  readable `.pth` is not evidence of compatibility.
- **Resume versus load confusion:** resume continues runner state; `load_from`
  loads weights when no `resume_from` is active. Do not use a QPN checkpoint as
  an implicit stage-2 initialization unless the model explicitly supports and
  the experiment owner has approved that design.
- **Stale or partial checkpoint:** inspect modification time, size, log ending,
  and whether the checkpoint was written by the intended config. Never pick the
  lexicographically first `.pth`; name it explicitly.
- **Overwrite risk:** checkpoints/logs/config dumps share `work_dir`. Use a new
  directory for a changed config or incompatible world size. The preflight
  helper warns about existing paths but never deletes them.

## OOM and device issues

- **CUDA out of memory:** first stop and record GPU count, visible devices,
  config variant, batch/sample settings, and whether temporal T or deform3D is
  selected. Reduce scope only through reviewed config changes; do not claim
  equivalence after changing resolution, cameras, temporal frames, or batch
  size. A single-GPU diagnostic may still be infeasible.
- **`cuda`/device ordinal errors:** compare `--nproc_per_node`,
  `CUDA_VISIBLE_DEVICES`, and the actual visible GPU count. For non-distributed
  `--gpu-ids`, use valid visible indices. Do not mix host-global IDs with
  remapped `CUDA_VISIBLE_DEVICES` IDs.
- **NCCL initialization or hang:** choose a free `PORT`, ensure all ranks see
  the same filesystem/config/data, use NCCL-compatible CUDA/driver packages,
  and avoid concurrent jobs reusing the same port or work directory. A
  distributed test may need a shared `--tmpdir` or sufficient `.dist_test`
  space.
- **No-GPU/CPU request:** this code's custom training API calls `.cuda()` and
  the distributed config uses NCCL. Route to environment preparation; do not
  promise CPU full training/evaluation.

## Distributed launch

- **Port occupied:** set `PORT=<free-port>` for `dist_train.sh` (default
  28509) or `dist_test.sh` (default 29503), or use `--master_port` in a direct
  launch. Confirm the port is free for every rank before starting.
- **Wrapper argument shifted:** train wrapper arguments are `CONFIG GPUS
  [extra...]`; test wrapper arguments are `CONFIG CHECKPOINT GPUS [extra...]`.
  A missing checkpoint or GPU count changes every later positional argument.
- **Test wrapper gives a confusing metric error:** it hard-codes `--eval bbox`.
  Construct a direct distributed `tools/test.py` command when an explicit SSC
  evaluation operation is needed.
- **Rank-local files never collect:** check shared storage, `--tmpdir`, rank
  count and that all ranks use the same dataset length. If a job was killed,
  remove or quarantine stale temporary files only after confirming no live job
  uses that directory.
- **Slurm/MPI request:** the tool accepts these launcher names, but the
  repository wrapper selects PyTorch launch. Use an external scheduler-aware
  command only with an environment-specific plan; it was not verified here.

## Native extension/import failures

- **Plugin import fails:** environment preparation must align legacy
  `torch`/`mmcv-full`/`mmdet`/`mmseg`/`mmdet3d` versions. Run the environment
  sub-skill's safe import checks before training; do not patch imports inside a
  run directory.
- **Deformable attention symbol or ABI error:** distinguish standard S/T from
  `*-deform3D`. The deform3D family requires its CUDA extension/toolchain;
  missing `nvcc`, incompatible compiler, or torch/CUDA ABI blocks that family.
  Use the standard counterpart only if its own backend checks pass.
- **Import passes but operation fails:** an import smoke is not an op/runtime
  smoke. Record the exact exception, torch/CUDA/MMCV versions and selected
  config, then route to environment-and-installation.

## Stale outputs and result interpretation

- **Existing result directory:** do not merge a new run into it by default.
  Pick a unique work/show/tmp directory or obtain explicit reuse approval.
- **Metrics look implausible or empty:** verify result count, `y_pred`/`y_true`
  shapes, ignored label 255 handling, class mapping, split, query tag and
  checkpoint/config pairing. `mIoU` excludes class index 0 in `SSCMetrics`;
  it is not a generic mean over every class.
- **No final metric claim:** imports, help, config parsing and command printing
  are safe evidence only. Without real SemanticKITTI artifacts and an approved
  run, report metrics as unverified.
- **Repository has no small native tests:** do not invent a passing test suite.
  Use the bundled preflight plus safe parser/help and static/config checks, and
  clearly label full train/test as skipped.
