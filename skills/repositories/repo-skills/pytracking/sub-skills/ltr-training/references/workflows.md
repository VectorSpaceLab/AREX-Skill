# LTR training workflows

This reference describes safe operating workflows for the LTR training stack. It assumes you are working in a PyTracking checkout with importable `pytracking` and `ltr` packages and that the user has approved any long-running training execution.

## 1. Preflight the checkout and local training config

Before constructing a training command:

1. Confirm the checkout contains `ltr/run_training.py` and `ltr/train_settings/`.
2. Confirm the environment can import `ltr` and has a CUDA-capable PyTorch build if the selected setting expects GPU execution.
3. Ensure the local training config module exists. If it is missing, generate the template from the repository root:

   ```bash
   python - <<'PY'
   from ltr.admin.environment import create_default_local_file
   create_default_local_file()
   PY
   ```

4. Edit `ltr/admin/local.py` and set at least:
   - `workspace_dir`: base directory for checkpoints.
   - `tensorboard_dir`: usually inside `workspace_dir`.
   - `pretrained_networks`: directory containing downloaded or previously trained weights.
   - Dataset roots required by the selected training setting.
   - `pregenerated_masks` for RTS.
   - `lasot_candidate_matching_dataset_path` for KeepTrack.

The generated template contains common fields such as `lasot_dir`, `got10k_dir`, `trackingnet_dir`, `coco_dir`, `lvis_dir`, `sbd_dir`, `imagenet_dir`, `ecssd_dir`, `hkuis_dir`, `msra10k_dir`, `davis_dir`, and `youtubevos_dir`. Some settings use extra fields not present in the default template, notably `imagenet_vid_gmot_dir` and `tao_burst_dir` for TaMOs. Add missing attributes to `EnvironmentSettings.__init__` when a setting references them.

## 2. Choose and validate a train setting

A training run is identified by two strings:

- `train_module`: a subdirectory under `ltr/train_settings` such as `bbreg`, `dimp`, `kys`, `lwl`, `rts`, `tamos`, or `tomp`.
- `train_name`: a file stem inside that subdirectory such as `atom`, `prdimp50`, or `tomp50`.

Validate against the checkout before running:

```bash
python skills/disco/pytracking/sub-skills/ltr-training/scripts/build_training_command.py --list
python skills/disco/pytracking/sub-skills/ltr-training/scripts/build_training_command.py dimp prdimp50
```

The helper prints a command only; it never imports the setting or starts training.

## 3. Construct a launch command without starting training

Default source-style command from the repository root:

```bash
python ltr/run_training.py <train_module> <train_name>
```

Examples:

```bash
python ltr/run_training.py bbreg atom
python ltr/run_training.py dimp prdimp50
python ltr/run_training.py tomp tomp50
```

To disable cuDNN benchmark mode, use the bundled helper:

```bash
python skills/disco/pytracking/sub-skills/ltr-training/scripts/build_training_command.py tomp tomp50 --no-cudnn-benchmark
```

The source command-line parser declares `--cudnn_benchmark` as `type=bool`; passing text like `False` can still evaluate truthy. The helper therefore emits a Python API one-liner for the no-benchmark case.

## 4. Launch only after an explicit execution decision

Before launching a full run, confirm:

- Dataset roots exist and match the split names used by the selected setting.
- Required pretrained weights are in `pretrained_networks` or required stage checkpoints exist under `workspace_dir`.
- CUDA device selection and memory budget are acceptable.
- `num_workers` is safe for the host; reduce to `0` when debugging loader or multiprocessing failures.
- The user accepts the run length. Many settings are configured for tens to hundreds of epochs and large per-epoch sample counts.

A controlled single-GPU launch pattern is:

```bash
CUDA_VISIBLE_DEVICES=0 python ltr/run_training.py <train_module> <train_name>
```

Do not use this sub-skill to run trained trackers after training. Hand off tracker execution to `tracking-evaluation`.

## 5. Resume, checkpoints, and TensorBoard

The trainer saves checkpoints under:

```text
<workspace_dir>/checkpoints/ltr/<train_module>/<train_name>/
```

Each checkpoint stores epoch, actor type, network type, network state, optimizer state, stats, and settings. Most included settings call `trainer.train(..., load_latest=True, fail_safe=True)`, so they resume from the latest matching checkpoint in the project path and attempt repeated restart after a crash. If you change the model class, actor class, or checkpoint path, be explicit about whether resuming is still safe.

TensorBoard logs are written under:

```text
<tensorboard_dir>/ltr/<train_module>/<train_name>/
```

with one writer per loader name plus an `info` writer for module name, script name, and description. To inspect logs after a run starts:

```bash
tensorboard --logdir <tensorboard_dir>
```

## 6. Modify an existing train setting safely

Prefer copying an existing setting to a new file stem or new module instead of editing a canonical setting in place. A setting file must define:

```python
def run(settings):
    ...
```

Inside `run(settings)`, the normal sequence is:

1. Set metadata and hyperparameters on `settings`.
2. Instantiate dataset objects from `ltr.dataset` using `settings.env.<field>` paths.
3. Compose transforms and a processing object from `ltr.data.processing`.
4. Build a sampler from `ltr.data.sampler`.
5. Wrap the sampler in `LTRLoader` or `MultiEpochLTRLoader`.
6. Construct a model from `ltr.models`.
7. Define objectives and loss weights.
8. Construct an actor from `ltr.actors`.
9. Create optimizer and learning-rate scheduler.
10. Create `LTRTrainer` and call `trainer.train(...)`.

For a quick edit sanity check without training, use static checks: verify the file exists, the `run(settings)` function is defined, imports are available, and the selected dataset/checkpoint fields are configured. Do not import a setting if its top-level code has side effects; included settings generally keep construction inside `run(settings)`.

## 7. Family-specific launch notes

- ATOM and DiMP/PrDiMP depend on standard SOT datasets and PreciseRoIPooling-backed components. The selected setting chooses whether GOT-10k is included.
- KeepTrack requires a base SuperDiMP-style checkpoint and a LaSOT candidate-matching JSON. Generating that JSON is a tracker-execution workflow; validate the tracker and dataset through `tracking-evaluation`, then point `lasot_candidate_matching_dataset_path` at the resulting JSON.
- KYS requires a DiMP checkpoint and the `spatial-correlation-sampler` package for its cost-volume model.
- LWL stage 1 requires converted Mask R-CNN backbone weights. LWL stage 2 resumes from the stage-1 workspace checkpoint. LWL box initialization resumes from the stage-2 workspace checkpoint.
- RTS requires pregenerated masks and an LWL stage-2 checkpoint in `pretrained_networks`.
- TaMOs uses additional MOT/VOS-style datasets and, for the Swin setting, Swin-Base backbone weights. Its batch size and worker count depend on `torch.cuda.device_count()`.
- ToMP uses dense regression processing with standard SOT datasets and long 300-epoch defaults.
