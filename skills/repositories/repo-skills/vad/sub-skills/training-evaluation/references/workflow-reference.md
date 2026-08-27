# VAD Workflow Reference

This reference is a command-construction guide for a VAD checkout. Replace
angle-bracket placeholders; do not copy private host paths into a reusable run
record.

## 1. Setup-to-train sequence

1. **Confirm the input contract.** Use the data-preparation route to verify the
   nuScenes data root, temporal train/validation pickle files, map annotation
   file, camera assets, and optional CAN-bus inputs required by the selected
   config. The standard VAD configs use `VADCustomNuScenesDataset`,
   `data/nuscenes/`, `vad_nuscenes_infos_temporal_train.pkl`, and
   `vad_nuscenes_infos_temporal_val.pkl`. Do not repair a missing conversion in
   this route.
2. **Choose a config family.** Prefer `VAD_base_stage_1.py` followed by
   `VAD_base_stage_2.py` (or the matching tiny pair for a smaller experiment).
   The stage-2 configs carry `load_from` pointing at a stage-1 checkpoint. The
   `*_e2e.py` family trains the complete path as one run and is the documented
   alternative. Tiny/base changes capacity and resource demand; it does not
   change the parser contract.
3. **Check the config without building.** Run
   `scripts/check_training_contract.py <CONFIG>` and, when available, the
   architecture route's config checker. Confirm `plugin=True`, a usable
   `plugin_dir`, model/data/evaluation sections, normalization, and the stage
   checkpoint relationship. A config check does not prove imports, data, CUDA,
   or checkpoint compatibility.
4. **Check the entry-point imports.** From the project root, use
   `python tools/train.py --help` as a safe parser/import smoke check. If the
   legacy `mmcv`, `mmdet`, `mmdet3d`, `mmseg`, PyTorch, OpenCV, or custom CUDA
   extension stack cannot import, stop and use the environment/architecture
   routes rather than starting a partial run.
5. **Select a launch.** Start with one process for a smoke experiment. A
   documented multi-GPU training launch is shown below. Use a scheduler-specific
   command only when the site has already supplied its `slurm` or `mpi` setup.
6. **Preserve evidence.** Record the exact config, all overrides, launcher,
   visible GPU list, port or scheduler job, seed, deterministic choice,
   checkpoint identity, package versions, and work directory.

### Single-process training

```bash
cd <VAD_ROOT>
python tools/train.py <CONFIG.py> \
  --launcher none \
  --gpus 1 \
  --work-dir <WORK_DIR> \
  --seed 0 \
  --deterministic
```

`--gpu-ids 0` can be used instead of `--gpus 1`; the two options are mutually
exclusive. A non-distributed run uses the configured GPU id(s), but the VAD
model still requires a compatible CUDA-capable runtime for actual training.

### One-node distributed training

```bash
cd <VAD_ROOT>
CUDA_VISIBLE_DEVICES=<GPU_IDS> \
python -m torch.distributed.run \
  --nproc_per_node=<N> \
  --master_port=<PORT> \
  tools/train.py <CONFIG.py> \
  --launcher pytorch \
  --work-dir <WORK_DIR> \
  --seed 0 \
  --deterministic
```

`<N>` must equal the number of processes intentionally assigned to the
visible GPUs. Do not use the distributed command for evaluation merely because
it works for training. `slurm` and `mpi` are accepted values of the train
parser, but their environment/bootstrap arguments are site-specific; do not
invent a scheduler command. The repository also documents a shell wrapper for
distributed training; the direct `torch.distributed.run` form makes the
process count and port explicit.

## 2. Stage choices and checkpoint semantics

### Recommended two-stage path

Train stage 1 once for perception and prediction, then train stage 2 for
planning using that checkpoint as initialization:

```bash
python tools/train.py <VAD_BASE_OR_TINY_STAGE_1.py> \
  --launcher <none-or-pytorch> \
  --work-dir <STAGE_1_WORK_DIR> \
  --seed 0 --deterministic

python tools/train.py <VAD_BASE_OR_TINY_STAGE_2.py> \
  --launcher <none-or-pytorch> \
  --work-dir <STAGE_2_WORK_DIR> \
  --cfg-options load_from=<STAGE_1_CHECKPOINT> \
  --seed 0 --deterministic
```

The checked-in stage-2 configs already contain a `load_from` value. The command
line override is useful when the produced checkpoint is stored elsewhere. A
stage-2 config without a real stage-1 checkpoint is not a fresh independent
training recipe: stop and provide one, or intentionally switch to an e2e
config.

- `load_from` is an initialization checkpoint consumed by the runner. It is
  different from `--resume-from` and should not be described as optimizer/epoch
  continuation.
- `--resume-from <CHECKPOINT>` is for continuing a training run. In the
  checked-in train entry point, it is applied only when the path is an existing
  file; validate the path before launch because a missing path can leave
  `resume_from` unapplied.
- If both a config `load_from` and a valid `--resume-from` are present, the
  custom training API gives resume precedence (`runner.resume` before
  `runner.load_checkpoint`). Record this explicitly rather than assuming the
  stage initialization is used.
- A backbone `pretrained` field is model initialization, not a resumable run.

### End-to-end path

`VAD_base_e2e.py` and `VAD_tiny_e2e.py` are the one-run alternatives. They can
produce similar results according to the project documentation, but they do
not remove the need for the same data, plugin, checkpoint, native-extension,
and normalization preflight.

## 3. What training writes

The train entry point resolves `work_dir` with this priority:

1. `--work-dir`;
2. `work_dir` in the config;
3. `./work_dirs/<config-basename-without-extension>` when neither is set.

It creates the directory, dumps the effective config under the original config
basename, writes a timestamped log, records environment/config/seed metadata,
and delegates to the VAD custom training API. Checkpoint names and retention
follow `checkpoint_config` and the configured runner; VAD configs normally save
periodic epoch checkpoints. Validation during training is enabled unless
`--no-validate` is supplied and follows the config's `workflow`/evaluation
settings. Do not assume that a checkpoint exists until the log and filesystem
show it.

Treat the dumped config as the provenance record for the merged command. Keep
it beside the log/checkpoints when comparing runs. A work directory is not a
substitute for a source revision, data version, or checkpoint checksum.

## 4. Checkpoint-to-evaluation sequence

1. Confirm that the checkpoint is readable and paired with the intended config
   and image normalization. For released weights, use the legacy normalization
   below; the newer normalization in recent configs can produce wrong metrics
   and visualizations with those weights.
2. Confirm validation data, map annotations, and the evaluation dependencies.
   VAD evaluation formats predictions and invokes its custom nuScenes detection,
   map, motion, and planning calculations; it is not a checkpoint-only file
   inspection.
3. Run a **single non-distributed GPU** evaluation:

```bash
cd <VAD_ROOT>
CUDA_VISIBLE_DEVICES=<ONE_GPU> \
python tools/test.py <CONFIG.py> <CHECKPOINT.pth> \
  --launcher none \
  --out <RESULTS.pkl> \
  --eval bbox \
  --seed 0 \
  --deterministic
```

The project explicitly warns that distributed evaluation is inaccurate. Do not
replace `--launcher none` with `--launcher pytorch`, `slurm`, or `mpi` for a
benchmark result. `--show` or `--show-dir` may be added to the non-distributed
command, then qualitative rendering should be handed to `visualization`.

4. For format-only submission output, replace `--eval bbox` with
   `--format-only` and optionally pass `--eval-options` for dataset formatting
   kwargs. `--eval` and `--format-only` cannot be used together.
5. Preserve the printed metrics, output pickle path, generated formatted result
   path, config, checkpoint, and exact command. Do not treat an output file as
   a successful evaluation unless the process completed and metrics/output
   validation passed.

The active VAD dataset formatter writes a nuScenes-style submission containing
`results`, `map_results`, and `plan_results`. With the repository's
`use_pkl_result=True` settings, its formatted file is a pickle despite the
nuScenes-style JSON-shaped content. The test script's `--out` file is a pickle
of the collected bbox result list and is distinct from the formatter's
submission artifact. Keep those two artifacts named separately.

By default, the test script supplies a timestamped prefix under
`test/<config-stem>/` to formatting/evaluation kwargs. An explicit
`--eval-options jsonfile_prefix=<PREFIX>` can change that dataset-formatting
location; use a writable, unique prefix and avoid confusing it with `--out`.

## 5. Released-checkpoint normalization

For reproduction with released weights, set the config's `img_norm_cfg` to
exactly:

```python
img_norm_cfg = dict(
    mean=[103.530, 116.280, 123.675],
    std=[1.0, 1.0, 1.0],
    to_rgb=False)
```

The recent configs instead show mean `[123.675, 116.28, 103.53]`, standard
 deviation `[58.395, 57.12, 57.375]`, and `to_rgb=True`. The project documents
that using the newer setting with released weights gives wrong metric results
and visualizations. Verify the effective normalization in both train and test
pipelines; changing only a top-level variable after config expansion may not
rewrite already-expanded pipeline dictionaries.

## 6. Construction-time verification boundary

During construction, only safe static/config checks and parser help checks were
in scope. No full train, validation, single-GPU evaluation, distributed launch,
rendering, dataset conversion, checkpoint download, or benchmark claim was
made. Those actions require external data/checkpoints and compatible native
imports/CUDA. A future operator must satisfy the preflight gates above before
running them.
