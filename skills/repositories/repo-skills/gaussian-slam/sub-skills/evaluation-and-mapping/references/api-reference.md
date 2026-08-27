# API reference

This reference mirrors the repository implementation rather than inventing a
new evaluator API. Paths below are repository-relative source anchors.

## CLI entry point

`run_evaluation.py` exposes:

```text
python run_evaluation.py [--checkpoint_path PATH] [--config_path PATH]
```

- `--checkpoint_path`: default `output/slam/full_experiment/`.
- `--config_path`: default empty. An empty value is replaced with
  `<checkpoint_path>/config.yaml`.
- The wrapper constructs `Evaluator(Path(checkpoint_path),
  Path(config_path))` and calls `.run()`.
- There are no stage selectors, no dry-run mode, and no output-directory
  argument in this wrapper.

The command is intended for a project environment such as `gslam` from
`environment.yml` (Python 3.10, PyTorch 2.1.2/CUDA 12.1, Open3D 0.18,
FAISS-GPU, the Gaussian rasterizer, simple-knn, and
`evaluate_3d_reconstruction`). Exact availability must be checked in the
active environment; package names alone are not proof of a working CUDA
extension.

## `Evaluator`

Source: `src/evaluation/evaluator.py`.

```python
Evaluator(checkpoint_path, config_path, config=None, save_render=False)
```

Constructor behavior:

1. Loads `config_path` with `load_config`, unless a `config` dictionary is
   supplied.
2. Calls `setup_seed(config["seed"])`.
3. Sets `self.device = "cuda"` and constructs the dataset from
   `dataset_name`, `data`, and `cam`.
4. Reads `estimated_c2w.ckpt` with `torch.load(..., map_location="cuda")`.
5. Discovers `checkpoint_path/submaps/*`; rendering and reconstruction later
   narrow this to `*.ckpt`.
6. Stores camera intrinsics and image dimensions from the dataset.
7. If `save_render=True`, creates `rendered_imgs/`; the CLI leaves it false.

The constructor can fail before stage-level exception handling if config,
dataset, checkpoint, CUDA, or imports are invalid.

### `run_trajectory_eval()`

Calls `evaluate_trajectory(self.estimated_c2w, self.gt_poses,
self.checkpoint_path)`. The helper:

- truncates ground truth only when it has more frames than the estimate;
- removes entries where ground-truth pose elements are NaN or infinite, using
  the same mask on estimates;
- extracts translation from `[:, :3, 3]`;
- computes raw translational ATE and a Horn closed-form rigidly aligned ATE;
- writes `ate.json`, `ate_aligned.json`, and `eval_trajectory.png`.

Alignment is applied to translation trajectories, not to the reported full
pose matrices. Equal, finite frame counts and `(N, 4, 4)` pose arrays should be
confirmed before running.

### `run_rendering_eval()`

For each sorted `submaps/*.ckpt` and each listed `submap_keyframes`, it:

1. Loads `gaussian_params` to CUDA.
2. Creates `GaussianModel()`, runs `training_setup`, and restores parameters.
3. Reads color/depth from the configured dataset and renders at the estimated
   camera pose.
4. Computes PSNR, LPIPS (Alex), multi-scale SSIM, and absolute depth L1.

It averages all rendered keyframe values and writes:

- `rendering_metrics.json` with `psnr`, `lpips`, `ssim`,
  `depth_l1_train_view`, and `num_renders`;
- `rendering_metrics.png` with PSNR, SSIM, and rendered depth-L1 curves;
- `rendered_imgs/<frame>.png` only when `Evaluator(..., save_render=True)` is
  used by custom Python code.

The default CLI does not request rendered image files. A zero render count
causes an averaging failure, which is caught by the outer evaluator and leaves
this stage incomplete.

### `run_reconstruction_eval()`

If `config["dataset_name"] != "replica"`, prints a skip message and returns
without reconstructing a mesh. For Replica it:

- creates `mesh/`;
- uses Open3D `ScalableTSDFVolume`, with voxel length `5/512`, truncation
  `0.04`, RGB8 colors, and the configured camera intrinsics;
- renders each submap keyframe, median-filters depth outliers with kernel 20
  and threshold 0.1, and integrates RGB-D using depth scale 1 and truncation
  30;
- writes `mesh/final_mesh.ply`;
- calls `evaluate_reconstruction` against
  `data/Replica-SLAM/cull_replica/<scene>.ply` and
  `data/Replica-SLAM/cull_replica/<scene>_pc_unseen.npy`.

The reconstruction helper cleans connected components by retaining components
with at least 200 vertices, writes `mesh/cleaned_mesh.ply`, runs
`evaluate_3d_reconstruction.run_evaluation` with distance threshold `0.01`
and ICP alignment, then attempts its 2-D depth evaluation. If the 2-D attempt
fails it records `{"depth l1": None}`, but a 3-D or mesh-construction failure
escapes to the outer stage catch.

### `run_global_map_eval()`

It constructs `RenderFrames`, which uses CUDA tensors and samples every frame
unless a dataset has more than 1,000 frames; then it uses a deterministic
stride of `len(dataset)//1000`. It then:

1. merges submaps with `merge_submaps` (FAISS, duplicate radius `0.0001`);
2. downsamples only when the point cloud exceeds 1,000,000 points, using voxel
   size `0.02`;
3. removes statistical outliers (`nb_neighbors=40`, `std_ratio=3.0`);
4. refines a degree-3 `GaussianModel` for `10_000` iterations using the
   cycling training frames and color/depth/regularization losses;
5. writes `<scene_name>_global_map.ply` in the checkpoint directory.

For `dataset_name == "scannetpp"` only, it creates `nvs_eval/`, switches a
copied config to `use_train_split=False`, renders every test frame, writes
`nvs_eval/<index:04d>.jpg`, and prints the per-frame and average PSNR. The
current implementation does not write NVS PSNR to JSON.

## Supporting serialization APIs

Source: `src/utils/io_utils.py`.

- `save_dict_to_ckpt(dictionary, file_name, directory=...)` creates the
  directory and uses `torch.save` (legacy zip serialization disabled).
- `save_dict_to_yaml` and `save_dict_to_json` create parent directories before
  writing.
- `load_config` supports recursive `inherit_from` merging.

Source: `src/entities/gaussian_slam.py` establishes the checkpoint layout:

```text
<output_path>/
  config.yaml
  estimated_c2w.ckpt
  submaps/
    000000.ckpt
    000001.ckpt
    ...
```

Each saved submap dictionary has:

```text
{
  "gaussian_params": <GaussianModel.capture_dict() dictionary>,
  "submap_keyframes": [frame_id, ...]
}
```

`GaussianModel.capture_dict()` contains active SH degree, Gaussian tensors,
optimizer bookkeeping, and the spatial learning scale. `GaussianModel` and
its PLY loading/restoring paths are CUDA-bound in this repository; do not
assume a CPU `torch.load` probe validates the model.
