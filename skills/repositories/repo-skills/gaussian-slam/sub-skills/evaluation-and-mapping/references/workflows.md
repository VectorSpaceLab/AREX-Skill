# Workflows

## 1. Read-only preflight

Run from the Gaussian-SLAM repository root. Replace the placeholder with a
checkpoint copied or staged for evaluation when the source output must be
preserved.

```bash
CKPT=/path/to/checkpoint
python skills/disco/gaussian-slam/sub-skills/evaluation-and-mapping/scripts/check_cli.py \
  --checkpoint "$CKPT" --json
python skills/disco/gaussian-slam/sub-skills/evaluation-and-mapping/scripts/validate_checkpoint.py \
  --checkpoint "$CKPT" --json
```

Check manually that:

- `config.yaml` resolves to a config containing `dataset_name`,
  `data.scene_name`, and usable `data`/`cam` values;
- `estimated_c2w.ckpt` is present;
- `submaps/` contains the expected numbered `.ckpt` files;
- the dataset input path is mounted and readable;
- Replica has both cull ground truth files when reconstruction is desired;
- ScanNet++ has a usable test split when NVS is desired;
- the active environment has a working CUDA device and compiled rasterizer,
  FAISS-GPU, and simple-knn extensions.

The helper scripts intentionally stop at file-level checks. They do not load
Torch checkpoints, import Open3D, access a dataset, or test a GPU kernel.

## 2. Environment gate

The repository `environment.yml` describes a `gslam` environment with Python
3.10, PyTorch 2.1.2, CUDA toolkit/PyTorch CUDA 12.1, FAISS-GPU, Open3D 0.18,
`evaluate_3d_reconstruction`, Gaussian rasterizer, simple-knn, image and
metric packages, and dataset utilities. In the actual target environment,
perform lightweight, explicit probes before the expensive command:

```bash
python - <<'PY'
import torch
print('cuda_available=', torch.cuda.is_available())
if torch.cuda.is_available():
    print('device=', torch.cuda.get_device_name(0))
import open3d
import faiss
import evaluate_3d_reconstruction
print('imports=ok')
PY
```

This probe imports dependencies but does not evaluate a checkpoint, open a
window, or download data. If a package import triggers a first-run model
weight download in a particular installation, stop and satisfy that cache
explicitly rather than hiding the network access inside evaluation.

Do not use a CPU-only trajectory helper result as the environment gate. The
full `Evaluator` constructor and rendering/global-map code construct CUDA
objects.

## 3. Standard full evaluation

```bash
python run_evaluation.py \
  --checkpoint_path "$CKPT" \
  --config_path "$CKPT/config.yaml" 2>&1 | tee evaluation.log
```

Run one evaluator per checkpoint. The command writes into `$CKPT`; `tee`
only adds an external log. After it exits, classify each stage from the log
and artifacts rather than relying on exit status:

| Stage | Success evidence | Dataset/resource gate |
|---|---|---|
| Trajectory | `ate.json`, `ate_aligned.json`, `eval_trajectory.png` | finite, shape-compatible poses and dataset GT |
| Rendering | `rendering_metrics.json`, `rendering_metrics.png` | CUDA rasterizer, valid submaps/keyframes, metric dependencies |
| Reconstruction | `mesh/final_mesh.ply`, `mesh/cleaned_mesh.ply`, `reconstruction_metrics.json` | Replica only; headless Open3D, Replica cull assets, 3-D evaluator |
| Global map | `<scene>_global_map.ply` | CUDA FAISS, valid submaps, enough points, refinement memory |
| ScanNet++ NVS | `nvs_eval/*.jpg` plus PSNR lines in log | `dataset_name: scannetpp`, test split, global map success |

A stage may be absent even when a later stage exists. Preserve the log and
list absent files explicitly.

## 4. Targeted support validation

For a malformed or synthetic pose fixture, it is reasonable to call the
trajectory helper in a separate CPU-only test process with NumPy arrays and a
temporary output directory. This validates alignment/math and output schema
only. It does not validate `Evaluator`, rendering, Open3D, FAISS, Gaussian
restore, or the configured dataset.

Likewise, the safe bundled scripts can validate a deliberately incomplete
checkpoint fixture without CUDA. Do not make fake `.ckpt` files look like a
successful full evaluation.

## 5. Recovery workflow

1. Copy the checkpoint to a new working directory if any output may be
   overwritten or if a rerun must be comparable.
2. Run read-only preflight and environment probes again after changing the
   environment or config.
3. Identify the first failing stage. Repair only its external prerequisite:
   config/path, dataset asset, dependency/cache, or available GPU memory.
4. Re-run the complete evaluator because the CLI has no stage selector and
   outputs are shared. Do not delete successful metrics merely to make a
   report look complete.
5. Compare timestamps and contents; label rerun outputs and partial metrics.
6. If the same stage still fails, stop with the traceback and an explicit
   unverified/blocked stage. Do not report skipped reconstruction or missing
   NVS as a numerical failure.

## Dataset-specific flows

### Replica mesh and depth L1

Use a config whose `dataset_name` is exactly `replica`. Confirm the scene name
matches both cull assets:

```text
data/Replica-SLAM/cull_replica/<scene>.ply
data/Replica-SLAM/cull_replica/<scene>_pc_unseen.npy
```

Install Open3D for headless rendering and the
`evaluate_3d_reconstruction` package in the same environment. The evaluator
uses an Open3D invisible visualizer for the 2-D depth metric; a desktop GUI is
not required, but a headless-compatible build/display setup is required.

### ScanNet++ global map and NVS

Use `dataset_name: scannetpp` and a config with a valid train split for the
map refinement. The evaluator then makes a separate test dataset with
`use_train_split=False`. NVS images are saved only after global-map refinement
succeeds. No NVS JSON summary is currently emitted; retain stdout if the PSNR
is needed.

### Non-Replica / non-ScanNet++

Trajectory, rendering, and global map remain meaningful when their inputs and
CUDA dependencies are valid. Reconstruction is intentionally skipped for
non-Replica. Global-map NVS is intentionally skipped for datasets other than
ScanNet++.
