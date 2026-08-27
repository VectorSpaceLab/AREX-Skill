# Repository map for AB3DMOT workflows

This map helps route user tasks without reopening the source checkout.

## Public evidence areas

| Area | Role in AB3DMOT workflows | Owning generated route |
| --- | --- | --- |
| `README.md` | Overview, paper context, citation, quick KITTI demo, benchmark links | root, tracking-pipeline, evaluation-visualization |
| `docs/INSTALL.md` | Python/dependency/toolbox setup and PYTHONPATH guidance | root install/troubleshooting |
| `docs/KITTI.md` | KITTI data layout, PointRCNN tracking commands, KITTI metrics and visualization | data-conversion, tracking-pipeline, evaluation-visualization |
| `docs/nuScenes.md` | nuScenes raw-data conversion, detector conversion, tracking, official/quick metrics, visualization | data-conversion, tracking-pipeline, evaluation-visualization |
| `configs/KITTI.yml` | KITTI defaults: split, detector, categories, output root, tracker flags | tracking-pipeline |
| `configs/nuScenes.yml` | nuScenes defaults: detector, split, categories, output root, tracker flags | tracking-pipeline |
| `main.py` | Primary tracking script and category loop | tracking-pipeline |
| `AB3DMOT_libs/model.py` | `AB3DMOT` tracker class and track/update/output behavior | tracking-pipeline API reference |
| `AB3DMOT_libs/box.py` | `Box3D` representation and array conversion helpers | tracking-pipeline API reference |
| `AB3DMOT_libs/io.py` | Detection loading, frame extraction, result/affinity writing, file combining | data-conversion, tracking-pipeline, evaluation-visualization |
| `AB3DMOT_libs/matching.py`, `dist_metrics.py`, `kalman_filter.py` | Association metrics, matching algorithms, Kalman filter state | tracking-pipeline API reference |
| `AB3DMOT_libs/kitti_*`, `nuScenes*` | Calibration, object/tracklet IO, OXTS, and nuScenes/KITTI conversion helpers | data-conversion, evaluation-visualization |
| `scripts/pre_processing/convert_det2input.py` | Converts KITTI object detections into AB3DMOT per-sequence inputs | data-conversion |
| `scripts/post_processing/trk_conf_threshold.py` | Confidence thresholding for 2D MOT/submission/visualization | evaluation-visualization |
| `scripts/post_processing/visualization.py` | Image and video rendering of tracked 3D boxes | evaluation-visualization |
| `scripts/post_processing/combine_trk_cat.py` | Combines category outputs into overall result folders | evaluation-visualization/result layout |
| `scripts/KITTI/evaluate.py` | Local KITTI validation metrics implementation | evaluation-visualization |
| `scripts/nuScenes/export_kitti.py` | nuScenes raw/result conversion and result export | data-conversion, evaluation-visualization |
| `scripts/nuScenes/evaluate.py`, `evaluate_quick.py` | Official and quick nuScenes metric workflows | evaluation-visualization |

## Output roots

KITTI default output root:

```text
results/KITTI/
  <det>_<category>_<split>_H<num>/
  <det>_<split>_H<num>/
```

nuScenes default output root:

```text
results/nuScenes/
  <det>_<category>_<split>_H<num>/
  <det>_<split>_H<num>/
```

Inside a result folder, common children include:

```text
data_0/               # MOT evaluation files
trk_withid_0/         # frame-wise 3D object rows with track ids
affi/                 # saved affinity matrices
affi_vis/             # text affinity visualization
log/ or vis_log.txt   # logs depending on workflow
trk_image_vis/        # visualization output images
trk_video_vis/        # visualization output videos
```

## Generated skill boundaries

- `data-conversion` owns input schemas and conversion/preflight.
- `tracking-pipeline` owns running `main.py` and direct tracker API usage.
- `evaluation-visualization` owns downstream result processing.
- Root owns install/import checks, repository map, cross-cutting troubleshooting, provenance, and router metadata.

## Source scripts not bundled wholesale

Large evaluator/converter scripts remain source evidence rather than bundled copies because they are dataset-bound, lengthy, and often write large external-data trees. The generated skill instead bundles safe helper scripts that validate inputs, construct commands, or run synthetic smoke checks without data side effects.
