# Inference workflows

Use this file to decide how to construct inference runs. The bundled helper renders commands only; it never imports MMDetection3D, loads a checkpoint, downloads weights, opens a display, or touches a GPU.

## Safe command rendering

From this sub-skill directory, render commands with the bundled helper:

```bash
python scripts/build_inference_command.py --help
```

Task-specific help:

```bash
python scripts/build_inference_command.py lidar-det --help
python scripts/build_inference_command.py mono-det --help
python scripts/build_inference_command.py multi-modality-det --help
python scripts/build_inference_command.py lidar-seg --help
```

Rendered examples:

```bash
python scripts/build_inference_command.py \
  lidar-det \
  --pcd demo/data/kitti/000008.bin \
  --config configs/pointpillars/pointpillars_hv_secfpn_8xb6-160e_kitti-3d-car.py \
  --checkpoint CHECKPOINT.pth \
  --device cuda:0 \
  --pred-score-thr 0.3 \
  --out-dir outputs
```

```bash
python scripts/build_inference_command.py \
  mono-det \
  --img demo/data/kitti/000008.png \
  --ann-file demo/data/kitti/000008.pkl \
  --config configs/pgd/pgd_r101-caffe_fpn_head-gn_4xb3-4x_kitti-mono3d.py \
  --checkpoint CHECKPOINT.pth \
  --cam-type CAM2 \
  --pred-score-thr 8 \
  --out-dir outputs
```

```bash
python scripts/build_inference_command.py \
  multi-modality-det \
  --pcd demo/data/kitti/000008.bin \
  --img demo/data/kitti/000008.png \
  --ann-file demo/data/kitti/000008.pkl \
  --config configs/mvxnet/mvxnet_fpn_dv_second_secfpn_8xb2-80e_kitti-3d-3class.py \
  --checkpoint CHECKPOINT.pth \
  --cam-type CAM2 \
  --pred-score-thr 0.3 \
  --out-dir outputs
```

```bash
python scripts/build_inference_command.py \
  lidar-seg \
  --pcd demo/data/scannet/scene0000_00.bin \
  --config configs/pointnet2/pointnet2_ssg_2xb16-cosine-200e_scannet-seg.py \
  --checkpoint CHECKPOINT.pth \
  --device cuda:0 \
  --out-dir outputs
```

After rendering, inspect the printed command before execution. The rendered command follows the v1.4.x demo CLI shape:

- LiDAR detection: `python demo/pcd_demo.py PCD CONFIG CHECKPOINT ...`
- Monocular detection: `python demo/mono_det_demo.py IMG ANN_FILE CONFIG CHECKPOINT ...`
- Multi-modality detection: `python demo/multi_modality_demo.py PCD IMG ANN_FILE CONFIG CHECKPOINT ...`
- LiDAR segmentation: `python demo/pcd_seg_demo.py PCD CONFIG CHECKPOINT ...`

## Remote or no-display workflow

For remote servers, CI jobs, SSH sessions, and containers without a display:

1. Omit `--show`.
2. Keep `--out-dir outputs` or another explicit output directory.
3. Keep prediction saving enabled; do not combine `--no-save-pred` with a need to inspect results later.
4. Expect JSON predictions under `OUT_DIR/preds/`.
5. Do not depend on LiDAR Open3D image output when `--show` is false. LiDAR visualization paths are display-sensitive.
6. For image-based workflows, camera visualizations can be saved under `OUT_DIR/vis_camera/<cam_type>/` when the config visualizer is available.

The demo entry points defensively force online display off when `DISPLAY` is missing. That protects remote execution, but it also means a command that asks for `--show` may not show anything on a headless host.

## Config/checkpoint acquisition

Before actual execution, obtain a config/checkpoint pair that matches:

- Task type: detection vs segmentation, and LiDAR vs monocular vs multi-modality.
- Dataset conventions: classes, camera keys, box coordinate mode, point dimensions, and expected info-file schema.
- Model family: checkpoint weights must correspond to the selected config architecture.

Common safe acquisition pattern:

```bash
mim download mmdet3d --config MODEL_CONFIG_ALIAS --dest checkpoints
```

Caveats:

- Actual `mim download`, model aliases, checkpoint URLs, and inferencer aliases may trigger network access.
- Large checkpoints can fail in restricted networks or quota-limited environments. Prefer pre-downloaded local checkpoint files for reproducible runs.
- Some model families require CUDA ops or sparse-convolution backends; command rendering cannot prove those are installed.

## Point-cloud detection workflow

Command-style path:

```bash
python demo/pcd_demo.py PCD_FILE CONFIG_FILE CHECKPOINT_FILE \
  --device cuda:0 \
  --pred-score-thr 0.3 \
  --out-dir outputs
```

Python-style path:

```python
from mmdet3d.apis import LidarDet3DInferencer

inferencer = LidarDet3DInferencer(
    model='CONFIG.py',
    weights='CHECKPOINT.pth',
    device='cuda:0',
)
results = inferencer(
    dict(points='sample.bin'),
    out_dir='outputs',
    show=False,
    pred_score_thr=0.3,
)
```

Use the lower-level API when you need the transformed input data along with the prediction:

```python
from mmdet3d.apis import init_model, inference_detector

model = init_model('CONFIG.py', 'CHECKPOINT.pth', device='cuda:0')
pred, data = inference_detector(model, 'sample.bin')
```

Array guidance:

- `inference_detector` supports a single `numpy.ndarray` or a sequence of arrays when dimensions match the config pipeline.
- `LidarDet3DInferencer` also supports arrays and lists of per-sample dictionaries.
- The demo command is file-path only.

## Monocular detection workflow

Command-style path:

```bash
python demo/mono_det_demo.py IMG_FILE ANN_FILE CONFIG_FILE CHECKPOINT_FILE \
  --device cuda:0 \
  --cam-type CAM2 \
  --pred-score-thr 0.3 \
  --out-dir outputs
```

Python-style path:

```python
from mmdet3d.apis import MonoDet3DInferencer

inferencer = MonoDet3DInferencer(
    model='CONFIG.py',
    weights='CHECKPOINT.pth',
    device='cuda:0',
)
results = inferencer(
    dict(img='image.png', infos='sample_infos.pkl'),
    cam_type='CAM2',
    out_dir='outputs',
    show=False,
    pred_score_thr=0.3,
)
```

Annotation/info file requirements:

- The file must load to a mapping with `data_list`.
- Each sample needs an `images` mapping containing the exact `cam_type` key.
- The selected image basename must match the info record's image basename.
- Calibration matrices must be present for the model pipeline. Typical fields include `cam2img`, `lidar2cam`, and sometimes `lidar2img`.

Camera-key examples are dataset-specific; do not hard-code one spelling across datasets. Inspect the info file keys or ask the user for the intended camera.

Score threshold note: some monocular models use scores outside the usual `[0, 1]` interval. For those models, a value such as `8` may be meaningful while `0.3` may be too permissive.

## Multi-modality detection workflow

Command-style path:

```bash
python demo/multi_modality_demo.py PCD_FILE IMG_FILE ANN_FILE CONFIG_FILE CHECKPOINT_FILE \
  --device cuda:0 \
  --cam-type CAM2 \
  --pred-score-thr 0.3 \
  --out-dir outputs
```

Python-style path:

```python
from mmdet3d.apis import MultiModalityDet3DInferencer

inferencer = MultiModalityDet3DInferencer(
    model='CONFIG.py',
    weights='CHECKPOINT.pth',
    device='cuda:0',
)
results = inferencer(
    dict(points='sample.bin', img='image.png', infos='sample_infos.pkl'),
    cam_type='CAM2',
    out_dir='outputs',
    show=False,
    pred_score_thr=0.3,
)
```

Multi-view caveats:

- Single-view KITTI/SUN RGB-D-like workflows are the most robust.
- `cam_type='all'` can represent multi-view directory-style input in some code paths, but support depends on the selected pipeline.
- The inferencer warns that `LoadMultiViewImageFromFiles` is not supported; validate multi-view configs before promising end-to-end execution.
- Project models may require project-specific imports, CUDA ops, or checkpoint sources beyond the core package.

## LiDAR segmentation workflow

Command-style path:

```bash
python demo/pcd_seg_demo.py PCD_FILE CONFIG_FILE CHECKPOINT_FILE \
  --device cuda:0 \
  --out-dir outputs
```

Python-style path:

```python
from mmdet3d.apis import LidarSeg3DInferencer

inferencer = LidarSeg3DInferencer(
    model='CONFIG.py',
    weights='CHECKPOINT.pth',
    device='cuda:0',
)
results = inferencer(
    dict(points='sample.bin'),
    out_dir='outputs',
    show=False,
)
```

Low-level path:

```python
from mmdet3d.apis import init_model, inference_segmentor

model = init_model('CONFIG.py', 'CHECKPOINT.pth', device='cuda:0')
pred, data = inference_segmentor(model, 'sample.bin')
```

Segmentation notes:

- The low-level segmentor is file-path oriented.
- The inferencer supports point arrays when they match the config's point layout.
- Segmentation visualization is display-sensitive like LiDAR detection.

## Output directory checklist

Use this checklist before execution:

- `--out-dir` / `out_dir` is set to a writable directory.
- `--no-save-pred` is not set if JSON output is needed.
- `--no-save-vis` is not set if visualization output is needed.
- On remote servers, do not rely on `--show`; copy JSON or saved camera visualizations for local inspection.
- For LiDAR Open3D output, decide whether a display or virtual display is available before promising saved rendered point-cloud views.
