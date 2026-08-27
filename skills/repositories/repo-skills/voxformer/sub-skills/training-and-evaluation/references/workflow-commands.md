# Workflow commands

These templates are repository-grounded command shapes. Replace angle-bracket
placeholders with paths in the operator's checkout; do not copy private paths
into a reusable plan. Run from the repository root after the environment and
SemanticKITTI layout are independently prepared. Commands below are plans only;
they are not a substitute for preflight.

## Stage order and config roles

1. **Stage 1 QPN:** `projects/configs/voxformer/qpn.py` uses
   `SemanticKittiDatasetStage1`, `./kitti/` by default, and writes checkpoints
   at the configured interval (one epoch in this config). Its output is the
   class-agnostic query proposal/checkpoint workflow.
2. **Stage 2 VoxFormer:** `projects/configs/voxformer/voxformer-S.py` is the
   single-camera variant and `voxformer-T.py` is the temporal five-camera
   variant. Both use `SemanticKittiDatasetStage2`, the configured query tag
   (`query_iou5203_pre7712_rec6153` in the inspected presets), labels, and
   stage-2 data. The T preset uses temporal offsets `[-12, -9, -6, -3]`.
3. A stage-2 run must use query artifacts matching its config's `query_tag`,
   labels tag, camera count and temporal setup. Selecting a stage-2 config does
   not generate those files and does not automatically consume a stage-1
   checkpoint. Confirm the data contract with `dataset-preparation` first.

The standard `*-deform3D.py` variants are a separate CUDA/custom-extension
choice. Use them only after `environment-and-installation` proves the extension
is ready; otherwise choose the corresponding standard S/T config.

## Train: documented four-GPU shape

The getting-started document gives these commands:

```bash
./tools/dist_train.sh <repo-config>/projects/configs/voxformer/qpn.py 4
./tools/dist_train.sh <repo-config>/projects/configs/voxformer/voxformer-T.py 4
```

Use a repository-relative config in practice, for example:

```bash
./tools/dist_train.sh projects/configs/voxformer/qpn.py <GPU_COUNT> \
  --work-dir <stage1-work-dir>
./tools/dist_train.sh projects/configs/voxformer/voxformer-T.py <GPU_COUNT> \
  --work-dir <stage2-work-dir>
```

`tools/dist_train.sh` sets `PYTHONPATH` to the repository, invokes
`python -m torch.distributed.launch --nproc_per_node=<GPU_COUNT>`, selects
`--launcher pytorch`, and appends `--deterministic`. It uses `PORT` when set
(default `28509`):

```bash
PORT=<free-port> ./tools/dist_train.sh <config> <GPU_COUNT> \
  --work-dir <work-dir>
```

The underlying `tools/train.py` also supports a non-distributed diagnostic:

```bash
python tools/train.py <config> --gpus 1 --work-dir <work-dir> --deterministic
```

`--gpus` and `--gpu-ids` are mutually exclusive and are for non-distributed
training. For a non-distributed run, the code defaults to GPU 0 unless IDs are
specified; it is not a CPU training path. The distributed wrapper's GPU count
must be a positive number of visible, compatible CUDA devices.

Useful training flags (all belong after the config; wrapper extra arguments are
forwarded):

- `--work-dir <dir>`: override the config work directory. The code creates it
  and dumps a copy of the config there, so confirm it is new or intentionally
  reusable before launch.
- `--resume-from <checkpoint>`: the code only assigns this value when the path
  is an existing file. In the custom train API, `resume_from` resumes runner
  state (including optimizer/epoch state where supported).
- `--no-validate`: disables validation during training. Default is validation;
  the custom training API registers an evaluation hook when validation is on.
- `--seed <int>`, `--deterministic`: reproducibility controls. The distributed
  wrapper always adds deterministic.
- `--autoscale-lr`: scales the configured learning rate by the selected GPU
  count relative to eight. This changes optimization; do not add it silently.
- `--cfg-options key=value ...`: merge config overrides. The deprecated
  `--options` spelling is accepted, but do not pass both. Quote list/tuple
  values as required by MMCV's `DictAction`.
- `--launcher none|pytorch|slurm|mpi`: the wrapper uses `pytorch`; direct
  `none` is non-distributed. Slurm/MPI require an externally prepared launcher.

The shared runtime defaults to `workflow=[('train', 1)]`, NCCL distributed
backend, and no `load_from`/`resume_from`. The standard stage-2 presets set
`max_epochs=20`; QPN sets 24. These are configuration facts, not a promise that
an execution will finish or reproduce a reported score.

## Load versus resume

There are two distinct mechanisms:

- `--resume-from` is a CLI convenience for an existing file and is wired to
  `cfg.resume_from`; use it to continue a compatible interrupted run in the
  same work directory/config family. Verify config, optimizer, epoch, world
  size assumptions, and output ownership first.
- `load_from` is a config field from the MMDetection/MMCV runtime and is applied
  by the custom training API when `resume_from` is absent. It loads model
  weights without the same resume semantics. If a config needs a starting
  weight, set it deliberately through a controlled config override or a copied
  config; do not confuse it with the stage-1-to-stage-2 data dependency.

The inspected `train.py` checks `osp.isfile(args.resume_from)` before assigning
it. A missing resume path therefore does not become a valid resume request and
should be treated as a preflight error, not ignored.

## Test/evaluation: single GPU

`tools/test.py` requires a checkpoint and at least one operation. A safe shape
is:

```bash
python tools/test.py <config> <checkpoint>.pth \
  --eval <metric> --show-dir <visualization-dir>
```

The repository dataset's `evaluate()` returns SemanticKITTI SSC metrics, even
though the generic parser help mentions bbox/segm/proposal. The distributed
wrapper hard-codes `--eval bbox`; for this repository's SSC path, prefer the
explicit direct command above or verify the wrapper behavior with the installed
stack before using it.

Other test operations:

```bash
# Save/format a result artifact (the current implementation's --out write is
# intentionally disabled by an assertion; do not treat --out as verified).
python tools/test.py <config> <checkpoint>.pth --out <results>.pkl

python tools/test.py <config> <checkpoint>.pth --format-only \
  --eval-options <key>=<value>
python tools/test.py <config> <checkpoint>.pth --show-dir <result-dir>
python tools/test.py <config> <checkpoint>.pth --show
```

Parser constraints from `tools/test.py`:

- At least one of `--out`, `--eval`, `--format-only`, `--show`, or `--show-dir`
  is mandatory.
- `--eval` and `--format-only` cannot be combined.
- `--out` must end in `.pkl` or `.pickle`. However, the inspected code prints a
  write message and then hits `assert False`; use `--eval`, `--show-dir`, or
  `--format-only` for a verified operation unless the implementation is fixed
  and separately tested.
- `--cfg-options` changes the loaded config; `--eval-options` passes evaluation
  kwargs. Deprecated `--options` must not be combined with `--eval-options`.
- `--gpu-collect` requests GPU result collection. Without it, distributed test
  uses `--tmpdir` or an automatically created `.dist_test` temporary directory;
  ensure shared filesystem and free space when using multiple ranks.
- `--fuse-conv-bn` is an inference optimization, not a correctness or memory
  fix. `--seed` and `--deterministic` affect reproducibility.

## Test: documented distributed shape

The getting-started document gives:

```bash
./tools/dist_test.sh <config> <checkpoint>.pth 4
```

The wrapper's actual contract is `CONFIG CHECKPOINT GPUS`, default `PORT=29503`,
then `torch.distributed.launch ... tools/test.py CONFIG CHECKPOINT
--launcher pytorch ... --eval bbox`. Extra arguments begin at wrapper argument
4. Override the port without modifying files:

```bash
PORT=<free-port> ./tools/dist_test.sh <config> <checkpoint>.pth <GPU_COUNT> \
  --show-dir <result-dir>
```

Because the wrapper always adds `--eval bbox`, do not append `--format-only` or
assume the wrapper is an SSC-metric command without checking the resulting
parser/config behavior. For an exact distributed operation, construct the
underlying shape explicitly:

```bash
PYTHONPATH=. python -m torch.distributed.launch \
  --nproc_per_node=<GPU_COUNT> --master_port=<free-port> \
  tools/test.py <config> <checkpoint>.pth --launcher pytorch \
  --eval <metric> --tmpdir <shared-temp-dir>
```

This still requires CUDA/NCCL, a matching checkpoint, all test data and a
shared writable temporary location. It is a launch template, not a request to
run it during skill creation.

## Outputs and preflight ownership

Training writes logs, a dumped config, checkpoints according to
`checkpoint_config`, and validation artifacts under `work_dir`. QPN has
`checkpoint_config=dict(interval=1)`; the inspected standard S/T presets set
`checkpoint_config=None` explicitly, so do not promise periodic stage-2
checkpoints without an intentional config change. Evaluation may create
validation/test prefixes and distributed temporary files; `show-dir` and
`--tmpdir` are operator-owned paths.

Before launch, check:

- config exists and is the intended stage/variant;
- checkpoint exists, is readable, and was made for that config/model family;
- stage-appropriate labels, query files, images, calibration, poses and
  preprocess artifacts exist;
- GPU count, `CUDA_VISIBLE_DEVICES`, NCCL, and free port are consistent;
- work/result/temp directories are fresh or explicitly approved for reuse;
- no stale checkpoint is being mistaken for the newest run.

Use `scripts/preflight_train_test.py`; it reports existing output paths but does
not delete, create, truncate, or launch anything.
