# KITTI evaluation and submission workflows

Use this reference after AB3DMOT has produced a KITTI tracking result folder under `results/KITTI/<result_sha>/`. For the provided PointRCNN validation run, the combined result folder is usually `results/KITTI/pointrcnn_val_H1/`.

## Preconditions

- Run commands from the AB3DMOT repository root.
- Confirm `results/KITTI/<result_sha>/data_0/` exists before metric evaluation. It contains one KITTI tracking-format text file per sequence.
- Confirm `results/KITTI/<result_sha>/trk_withid_0/` exists before visualization or confidence thresholding. It contains per-frame KITTI object-format files with track IDs in the final column.
- Local KITTI metric commands are for the validation split, where validation labels and `evaluate_tracking.seqmap.val` are available in the repository.
- KITTI test split labels are not available locally. Test-set evaluation is an external server/manual gate.

## KITTI 3D MOT validation metrics

The KITTI evaluator takes positional arguments:

```bash
python3 scripts/KITTI/evaluate.py <result_sha> <num_hypothesis> 3D <iou_threshold>
```

Common validation commands from the AB3DMOT docs are:

```bash
python3 scripts/KITTI/evaluate.py pointrcnn_val_H1 1 3D 0.25
python3 scripts/KITTI/evaluate.py pointrcnn_val_H1 1 3D 0.5
python3 scripts/KITTI/evaluate.py pointrcnn_Car_val_H1 1 3D 0.7
```

Interpretation:

- `0.25` 3D IoU is the main AB3DMOT validation setting used for all categories in the README-style tables.
- `0.5` 3D IoU is a stricter all-category validation setting.
- `0.7` 3D IoU is normally reported for the Car category result folder, so use a category-specific result SHA such as `pointrcnn_Car_val_H1` when reproducing that line.
- The evaluator prints class summaries to stdout and writes per-class summary text files and recall-curve PDFs into `results/KITTI/<result_sha>/`.

Expected metric artifacts include names such as:

```text
results/KITTI/<result_sha>/summary_car_average_eval3D.txt
results/KITTI/<result_sha>/summary_pedestrian_average_eval3D.txt
results/KITTI/<result_sha>/summary_cyclist_average_eval3D.txt
results/KITTI/<result_sha>/MOTA_recall_curve_car_eval3D.pdf
```

The exact category files depend on which categories are present in the result folder.

## KITTI 2D MOT validation metrics

Use the same evaluator with `2D 0.5`:

```bash
python3 scripts/KITTI/evaluate.py pointrcnn_val_H1 1 2D 0.5
```

For a custom validation result folder:

```bash
python3 scripts/KITTI/evaluate.py <result_sha> 1 2D 0.5
```

Interpretation:

- `0.5` is the 2D bounding-box IoU threshold used for KITTI 2D MOT validation in the AB3DMOT docs.
- Do not substitute a 3D IoU threshold into this command. The third argument controls whether the evaluator uses projected 2D boxes or 3D boxes.
- Expected artifacts are analogous to the 3D case but use the `eval2D` suffix, for example `summary_car_average_eval2D.txt`.

## Confidence thresholding for KITTI 2D MOT submission

For KITTI test results, AB3DMOT applies a per-track confidence threshold before packaging the server submission:

```bash
python3 scripts/post_processing/trk_conf_threshold.py --dataset KITTI --result_sha pointrcnn_test_H1
```

This creates:

```text
results/KITTI/pointrcnn_test_H1_thres/data_0/
results/KITTI/pointrcnn_test_H1_thres/trk_withid_0/
```

For the provided KITTI PointRCNN detector, AB3DMOT's threshold table is:

| Category | Track confidence threshold |
| --- | ---: |
| Car | 3.240738 |
| Pedestrian | 2.683133 |
| Cyclist | 3.645319 |

Thresholding computes each track's average score and removes entire track IDs whose average falls below the category threshold. The script infers the detector name from the first underscore-delimited part of `result_sha`, so `pointrcnn_test_H1` maps to the PointRCNN thresholds. A custom detector name will need a supported threshold entry in the running repository code.

## KITTI test server submission

KITTI test labels are not available locally. For a 2D MOT test submission:

1. Produce test tracking results, normally `results/KITTI/pointrcnn_test_H1/`.
2. Run confidence thresholding to create `results/KITTI/pointrcnn_test_H1_thres/`.
3. Compress only the thresholded `data_0/` folder contents in the format expected by the KITTI tracking submission server.
4. Upload through the official KITTI tracking evaluation server.

Do not report local test metrics for KITTI test unless an authorized external label source or server result is provided. Treat upload, account access, and leaderboard result retrieval as manual external gates.

## Command-builder shortcut

The bundled command builder can print the same sequence without importing AB3DMOT:

```bash
python3 sub-skills/evaluation-visualization/scripts/build_postprocess_commands.py \
  --dataset KITTI --split val --result-sha pointrcnn_val_H1 --steps kitti-3d kitti-2d threshold visualize
```

For a KITTI test submission sequence:

```bash
python3 sub-skills/evaluation-visualization/scripts/build_postprocess_commands.py \
  --dataset KITTI --split test --result-sha pointrcnn_test_H1 --steps threshold kitti-submission visualize
```
