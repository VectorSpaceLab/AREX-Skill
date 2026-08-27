---
name: slam-runtime
description: "Run and troubleshoot the CUDA-only Gaussian-SLAM pipeline:
  validate the environment, construct safe run_slam.py invocations, understand
  tracking/mapping/submaps and outputs, control seeds and W&B, and prepare
  non-submitting SLURM plans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gaussian-SLAM runtime

Use this skill when a user wants to execute, configure, reproduce, or recover a
Gaussian-SLAM run from this repository. The entry point is `run_slam.py`; the
repository's execution path is **CUDA-only**. Do not offer a CPU fallback for
tracking, mapping, rendering, or evaluation. Dataset acquisition and dataset
file-layout instructions belong to `datasets-and-configuration`; evaluation
metric internals belong to `evaluation-and-mapping`.

## Input/output contract

### Required inputs

- A scene YAML path passed as the positional `config_path` argument.
- A config resolving to `dataset_name`, `data`, `cam`, `tracking`, `mapping`,
  `seed`, and `use_wandb`. A scene config normally inherits a dataset base
  config and supplies `data.scene_name`, `data.input_path`, and
  `data.output_path`.
- A prepared RGB-D scene and camera metadata accepted by the selected dataset
  adapter. The dataset's layout is intentionally not specified here; ask the
  dataset skill for that contract.
- A CUDA-capable PyTorch installation and both compiled extensions:
  `simple_knn._C` and `gaussian_rasterizer._C`.

Use explicit `--input_path` and `--output_path` values for portable runs. The
config loader resolves `inherit_from` using the path as written, relative to
the process working directory, so launch from the repository root (or use
paths that resolve from the chosen working directory).

### Produced artifacts

`run_slam.py` creates the output directory, saves the effective `config.yaml`,
then runs tracking/mapping followed by the repository evaluator. Common
artifacts are:

- `config.yaml`: effective merged configuration after CLI overrides;
- `estimated_c2w.ckpt`: estimated camera-to-world poses;
- `submaps/000000.ckpt`, etc.: checkpoints containing Gaussian parameters and
  the keyframe IDs belonging to the completed prior submap;
- `mapping_vis/*.jpg` and the created `tracking_vis/` directory;
- evaluator artifacts such as `rendering_metrics.json`,
  `reconstruction_metrics.json`, `ate_aligned.json`, PNG summaries, a Replica
  mesh, and a refined global-map PLY when the corresponding evaluation phase
  succeeds.

The evaluator catches failures per evaluation phase and prints a traceback, so
an `All done.✨` line is not sufficient evidence that every evaluation artifact
exists. Check the expected files and the log. The active final Gaussian model
is not explicitly finalized after the main loop; verify submap completeness
before consuming checkpoints as a final map.

## Required preflight

Run these checks before a full scene. They are safe and do not download data,
submit jobs, or contact W&B:

```bash
nvidia-smi
python - <<'PY'
import torch
print("torch", torch.__version__, "cuda", torch.version.cuda)
assert torch.cuda.is_available(), "Gaussian-SLAM requires CUDA"
print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
PY
python - <<'PY'
import simple_knn._C
import gaussian_rasterizer._C
print("CUDA extensions import")
PY
python run_slam.py --help
python skills/disco/gaussian-slam/sub-skills/slam-runtime/scripts/check_cli.py \
  configs/Replica/room0.yaml
```

The repository environment specifies Python 3.10, PyTorch 2.1.2 with CUDA
12.1, torchvision 0.16.2, FAISS-GPU, Open3D 0.18.0, and pinned builds of the
two CUDA extensions. Building extensions needs a compatible host compiler; the
README requires exported `CC` and `CXX`. A verified inspection environment
passed CUDA allocation and both extension imports on an NVIDIA A100-SXM4-40GB
with compute capability 8.0 (SM80). Treat that as evidence for A100/SM80
compatibility, not as a promise for arbitrary GPUs. Match the PyTorch/CUDA
runtime, host compiler, toolkit, and extension build target to the actual
machine.

`GaussianModel` imports `simple_knn._C.distCUDA2` at module import and uses it
when adding points. `src/utils/utils.py` imports the custom
`gaussian_rasterizer`; render settings, tensors, and camera optimization are
also hard-coded to CUDA. Missing either extension, a CPU-only Torch build, or a
visible device mismatch is a prerequisite failure—not something to work around
by changing the device to CPU.

## Standard run

From the repository root, start with a small bounded scene/config if one is
available, then use the full run:

```bash
python run_slam.py configs/<dataset>/<scene>.yaml \
  --input_path <scene-input> \
  --output_path <run-output>
```

The process is sequential: it loads and recursively merges YAML inheritance,
updates selected fields from CLI arguments, optionally initializes W&B, seeds
Python/NumPy/PyTorch/CUDA, runs `GaussianSLAM.run()`, and then constructs an
`Evaluator` from the saved output config. The first two frames use dataset poses;
subsequent frames go through the configured tracker. Mapping runs on the
configured keyframe cadence and always appends the last frame to the mapping
IDs. Do not infer that `--gt_camera` changes this flow: the flag is parsed but
is not applied by `update_config_with_args`; select
`tracking.odometry_type: gt` in YAML when ground-truth tracking is intended.

For a deterministic, non-W&B smoke invocation, make the output unique and
explicit:

```bash
DISABLE_WANDB=true python run_slam.py configs/<dataset>/<scene>.yaml \
  --input_path <scene-input> \
  --output_path <run-output> \
  --seed 0
```

This controls the software RNGs (`torch`, CUDA, NumPy, Python, and hash seed)
and disables cuDNN benchmarking, but the README explicitly warns that the
Differential Gaussian rasterizer is nondeterministic. Compare runs with a
small tolerance and record GPU, driver, extension build, config, and seed.

## CLI and configuration

Read [references/cli-reference.md](references/cli-reference.md) before changing
hyperparameters. It records every parser option, its target config field, and
source-level caveats (including parsed-but-ineffective options and truthiness
checks that ignore zero). Use the checker to catch missing inherited fields and
contradictory filter flags before starting a GPU job.

The highest-risk runtime changes are tracking iterations/loss weighting and
mapping cadence/iterations. Large new-submap point counts, high-resolution
frames, and long optimization schedules increase VRAM and wall time. Lower
cadence or iteration counts only for a smoke test; do not call a shortened run
paper reproduction.

## Tracking, mapping, and submaps

- **Tracking.** `Tracker.track` renders the current Gaussian model and optimizes
  camera rotation/translation using RGB and depth losses. `odometry_type` is
  `gt`, `const_speed`, or `odometer`; the latter uses the configured visual
  odometer for initialization. Alpha and depth-outlier filters affect the
  tracking mask. A high initial loss can double tracking iterations; with
  `help_camera_initialization`, the tracker may retry initialization with an
  odometer estimate.
- **Mapping.** At mapping frames, the mapper creates a keyframe, seeds 3D
  points from RGB-D and the estimated pose, adds non-duplicate points to the
  current Gaussian model using `distCUDA2`, optimizes the current submap, and
  writes a visualization. New submaps use edge/gradient seeding; an existing
  submap uses alpha/depth-error regions. Dataset-specific point-cloud filtering
  is an implementation detail; do not substitute a missing dataset contract.
- **Submap boundaries.** With `submap_using_motion_heuristic: true`, the source
  starts a new submap when motion from the last submap start exceeds a hard-coded
  50-degree rotation or 0.5 translation threshold. Otherwise it uses
  `new_submap_every` frame IDs and also includes the last frame. At a boundary,
  the prior model is written as a zero-padded checkpoint, keyframes are reset,
  and a new model starts at that frame. The loop saves poses at the end but does
  not perform a separate final active-model checkpoint; inspect the output
  rather than assuming the last active model is serialized.

## W&B and seed controls

Configs default to `use_wandb: False`. For an offline/local run, prefer that
setting or set `DISABLE_WANDB=true`; the entry point treats exactly the string
`true` as a forced disable. If W&B is enabled, `run_slam.py` calls `wandb.init`,
logs source code, and uploads tracking/mapping/evaluation records. Credentials
and network access are not required for the default disabled path. If a site
needs W&B, decide explicitly whether online or offline mode is appropriate and
ensure its run directory is writable: the source contains a site-specific
absolute W&B directory that may not exist on another machine, and it is not a
CLI setting. Patch it to a writable path or keep W&B disabled; do not expose
credentials in configs or SLURM scripts.

## SLURM

Use [references/cluster-reproduction.md](references/cluster-reproduction.md) or
run the safe planner:

```bash
python skills/disco/gaussian-slam/sub-skills/slam-runtime/scripts/render_sbatch_plan.py \
  --dataset Replica --scene room0 --scene room1 \
  --input-root <input-root> --output-root <output-root>
```

The planner only prints a reviewable batch script; it never runs `sbatch`,
starts Python SLAM, downloads data, or authenticates W&B. Review the generated
array bounds, config directory, scene names, input/output roots, partition,
GPU request, and environment activation before manually submitting it. The
repository example contains site placeholders, a dataset-directory case
mismatch for ScanNet++, a fixed array example that must be changed per dataset,
and a trailing continuation after `--group_name`; use the corrected recipe in
the reference instead of copying it verbatim.

## Failure recovery

1. Preserve the run log and output directory. Do not delete partial submaps or
   overwrite a prior run while diagnosing it.
2. Classify the first failure: environment/extension, config resolution,
   dataset contract, CUDA/VRAM, W&B, or post-SLAM evaluation.
3. Re-run the corresponding preflight or checker. For config failures, use an
   explicit scene config and absolute/working-directory-correct input/output
   overrides. For extension failures, rebuild both pinned extensions for the
   active Torch/CUDA ABI and GPU architecture; never install a CPU substitute.
4. For CUDA out-of-memory, reduce the smoke-test frame limit and mapping point
   sample/iterations, close competing GPU jobs, and use a fresh output path.
   Treat a successful reduced run as a diagnostic only.
5. For W&B errors, disable it with `DISABLE_WANDB=true` and rerun; separately
   repair writable run-directory/network/auth configuration if online logging
   is required.
6. If tracking diverges, inspect the initial-loss message and try the
   config-supported odometry initialization or a bounded iteration adjustment.
   Keep the change in the saved config and record it; do not silently switch to
   ground-truth poses.
7. If SLAM completes but evaluation reports a traceback, verify
   `estimated_c2w.ckpt` and `submaps/` first, then treat the affected evaluation
   artifact as missing. Evaluation failures do not prove tracking/mapping
   failed, and `All done.✨` does not prove evaluation succeeded.

See [references/troubleshooting.md](references/troubleshooting.md) for symptom,
likely cause, safe check, and recovery tables.

## Difficult synthetic cases for verification

- **Case A — ignored override and portable logging:** provide a valid scene
  config with `--track_w_color_loss 0.1 --gt_camera`, `DISABLE_WANDB=true`, and
  a writable output path. The checker/handoff must warn that those two options
  do not update the config, while the run plan preserves the YAML odometry and
  W&B-disabled state rather than claiming ground-truth tracking.
- **Case B — boundary plus GPU failure:** use a tiny synthetic RGB-D fixture and
  a config with `map_every: 1`, a boundary at the last frame, and a deliberately
  oversized `new_submap_points_num` for the available VRAM. The expected
  recovery is a preserved partial output, an OOM classification, a reduced
  diagnostic config in a new output directory, and an explicit check that only
  completed prior submaps are consumed—not a CPU rerun or an assumed final
  checkpoint.

## Scope and evidence limits

This skill is runtime-focused. It does not define dataset directory layouts,
download commands, metric formulas, mesh evaluation semantics, or global-map
quality thresholds. No full-scene execution, dataset download, SLURM submission,
or W&B network/login test was performed during construction. The environment
report proves package/CUDA allocation/extension-import readiness on an SM80 A100
inspection host, not end-to-end scene correctness on every supported dataset
or GPU.

Load the focused references progressively:

- [references/workflows.md](references/workflows.md) for execution stages and
  output validation;
- [references/cli-reference.md](references/cli-reference.md) for exact flags;
- [references/cluster-reproduction.md](references/cluster-reproduction.md) for
  a corrected, non-submitting cluster recipe;
- [references/troubleshooting.md](references/troubleshooting.md) for recovery.
