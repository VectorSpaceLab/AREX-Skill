# Troubleshooting and recovery

Use the first traceback and the stage's artifact contract to classify the
problem. Prefer a copied checkpoint and external logs. The repository runner
has no stage selector, so after a repair it normally reruns all stages.

## Constructor and input failures

### `config.yaml` missing or config merge fails

- Symptom: failure before `Starting evaluation...` or while loading config.
- Check: pass an explicit `--config_path`; verify inherited paths in the config
  are resolvable from the repository's current working directory.
- Recovery: use the exact config that produced the checkpoint, without editing
  the checkpoint's source files in place. Re-run read-only schema checks.
- Do not: fabricate dataset or camera fields from a different scene.

### Dataset cannot be constructed / input path missing

- Check `dataset_name`, `data.input_path`, `data.scene_name`, and `cam` values.
  A config may inherit from a repository-relative path.
- Ensure dataset files are mounted and readable. This sub-skill does not
  download them.
- If the checkpoint and dataset come from different frame subsets, stop and
  label metrics unverified rather than silently reindexing poses.

### `estimated_c2w.ckpt` or `submaps/` missing

- The SLAM run may be incomplete. `estimated_c2w.ckpt` is saved during map
  transitions and again at the end; a missing file is not repairable by this
  evaluator.
- A missing or malformed submap prevents rendering and usually global-map
  construction. Preserve the run and ask for a completed checkpoint.

## CUDA and extension failures

### CUDA unavailable, model `.cuda()` failure, or rasterizer kernel error

Rendering, `GaussianModel`, `RenderFrames`, FAISS GPU merge, and map refinement
are CUDA paths. Confirm:

```bash
python -c 'import torch; print(torch.cuda.is_available()); print(torch.version.cuda)'
```

Then check the compiled rasterizer/simple-knn against the active PyTorch/CUDA
combination and GPU memory. Use a compatible environment from
`environment.yml` or the project's prepared environment; do not report a CPU
fallback as a full evaluation. A CPU-only trajectory helper can remain a
support check.

### Out-of-memory during rendering or global-map refinement

- Stop other GPU jobs and inspect the checkpoint's submap/point counts.
- Retry on a GPU with enough memory or use a copied checkpoint only if an
  explicitly approved code/config change reduces workload.
- Do not silently change the 10,000 global-map iterations, point merge policy,
  or metric sampling and compare the result to an unmodified run.

### FAISS index/training or empty-point failure

`merge_submaps` trains a FAISS index per submap and expects usable XYZ points.
Empty submaps, too few points for the configured IVF index, incompatible
FAISS-GPU builds, or no merged points can fail the global-map stage. Check
submap tensor schemas and counts with a project-aware CUDA environment; the
safe checkpoint script intentionally does not deserialize tensors. Keep
trajectory/render outputs if they succeeded and label global-map output
unverified.

## Trajectory failures

### Shape, NaN, or alignment errors

Confirm estimated and GT poses are `(N, 4, 4)` and correspond to the same
frame order. The helper only removes frames where GT contains NaN/Inf and
applies that mask to estimates. It does not robustly handle a shorter GT, an
empty valid sequence, or arbitrary frame-id gaps.

For a CPU support test, call `evaluate_trajectory` with a temporary output
folder and small finite arrays, then verify `ate.json`, `ate_aligned.json`,
and `eval_trajectory.png`. This does not validate the full Evaluator.

## Rendering failures

### No metrics or `num_renders` is zero

Check that `submaps/*.ckpt` exists, each checkpoint has a non-empty
`submap_keyframes` list, ids are valid for the constructed dataset, and
`estimated_c2w` covers those ids. Because all submap loads are repeated in one
stage, one malformed submap can abort the stage. Do not infer metrics from an
old JSON file.

### LPIPS/SSIM import or shape errors

The environment requires `torchmetrics`, `pytorch_msssim`, torchvision, and a
working LPIPS backend. Confirm rendered and GT colors are the same shape and
range. Keep the repository's metric implementations and normalization when
comparing runs.

### `depth_l1_train_view` is suspicious

It is an unmasked mean absolute difference between rendered and dataset depth
for training/keyframe views. It is not the Replica sampled unseen-view mesh
metric. Check depth units and dataset preprocessing before comparing scenes.

## Replica reconstruction failures

### Stage says dataset is not supported

This is an intentional skip for all dataset names other than the literal
`replica`, not a dependency failure. Do not create a mesh or report a
reconstruction score for ScanNet, TUM, or ScanNet++ from this stage.

### Missing `data/Replica-SLAM/cull_replica` assets

Provide the exact `<scene>.ply` and `<scene>_pc_unseen.npy` assets matching
`config.data.scene_name` in the repository's expected data location. Do not
substitute a training mesh or invent the unseen point cloud.

### Open3D window/context failure on a cluster

`calc_2d_metric` requests an invisible Open3D visualizer, but the build still
needs a headless-compatible rendering context. Install/use the repository's
headless Open3D setup and cluster display configuration. This can make only
`depth l1` become `null`; a 3-D result may still be present. If mesh
integration itself fails, the whole reconstruction stage is partial/failed.
Do not open GUI windows in safe validation scripts.

### `evaluate_3d_reconstruction` import or evaluation failure

Install the pinned package from `environment.yml` in the active environment
and check its API. The dependency controls the 3-D metric schema. If only the
local 2-D metric fails, the code writes `depth l1: null`; if the external
3-D call fails first, no reconstruction JSON may be written.

### Mesh appears empty or overly sparse

Inspect submap coverage, rendered depth, depth filtering, and TSDF integration
inputs. The cleaner discards connected components below 200 vertices. Keep
`final_mesh.ply` and `cleaned_mesh.ply` separate; do not overwrite the input
mesh while diagnosing.

## Global-map and ScanNet++ NVS failures

### Global PLY is absent

The merge/refinement stage failed. Check CUDA/FAISS, submap XYZ tensors,
point-cloud filtering, and GPU memory. The stage is not a harmless optional
extra for a complete evaluation report.

### NVS directory is absent

If the global PLY exists but NVS is absent, check `dataset_name` spelling and
whether it is exactly `scannetpp`. For ScanNet++ also verify that the test
split can be constructed and that test colors/poses are present. Non-ScanNet++
absence is intentional.

### NVS images exist but no JSON metric

This is the current contract: NVS PSNR is printed only. Preserve stdout/logs,
including `PSNR List` and `Avg. NVS PSNR`; do not invent `nvs_metrics.json`.

## Recovery reporting template

```text
checkpoint: <path or stable label>
config/dataset/scene: <...>
stages:
  trajectory: complete|partial|failed|unverified
  rendering: complete|partial|failed|unverified
  reconstruction: complete|skipped-by-dataset|partial|failed
  global_map: complete|partial|failed|unverified
  scannetpp_nvs: complete|skipped-by-dataset|partial|failed
artifacts inspected: <list>
first traceback: <stage and concise exception>
repair/retry: <external prerequisite and rerun>
remaining uncertainty: <...>
```
