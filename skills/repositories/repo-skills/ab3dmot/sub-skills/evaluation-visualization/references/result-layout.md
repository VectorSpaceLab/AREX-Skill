# AB3DMOT result layout for evaluation, thresholding, combination, and visualization

AB3DMOT writes all post-tracking artifacts below `results/<dataset>/`. Evaluation and visualization commands use the result folder basename as `result_sha`.

## Combined and category-specific result names

For each category, `main.py` writes category result folders:

```text
results/KITTI/pointrcnn_Car_val_H1/
results/KITTI/pointrcnn_Pedestrian_val_H1/
results/KITTI/pointrcnn_Cyclist_val_H1/

results/nuScenes/megvii_Car_val_H1/
results/nuScenes/megvii_Pedestrian_val_H1/
results/nuScenes/megvii_Truck_val_H1/
```

After all categories finish, `combine_trk_cat.py` creates a combined folder without the category segment:

```text
results/KITTI/pointrcnn_val_H1/
results/nuScenes/megvii_val_H1/
```

Use the combined folder for all-category evaluation and visualization. Use a category-specific folder only when reproducing a category-specific result, debugging one class, or running a stricter one-class threshold such as KITTI Car 3D IoU `0.7`.

Folder naming pattern:

```text
<det_name>_<split>_H<num_hypothesis>              # combined
<det_name>_<Category>_<split>_H<num_hypothesis>   # per category
<result_sha>_thres                                # confidence-thresholded copy
```

## Main tracking result folder

A typical combined folder contains:

```text
results/<dataset>/<result_sha>/
  data_0/
    <sequence>.txt
  trk_withid_0/
    <sequence>/
      <frame>.txt
  affi/
    <sequence>/
      <frame>.npy
  affi_vis/
    <sequence>/
      <frame>.txt
  combine_log.txt
```

Important subdirectories:

- `data_0/`: one text file per sequence in KITTI tracking-result format. This is the primary input for KITTI evaluation, nuScenes quick evaluation, KITTI-to-nuScenes export, and server submissions.
- `trk_withid_0/`: one text file per frame in KITTI object-detection style, with score and track ID appended. This is used by confidence thresholding and visualization.
- `affi/`: NumPy affinity matrices saved by the tracker, keyed by sequence and frame. These are useful for debugging association but are not required for metric scripts.
- `affi_vis/`: text-formatted affinity matrices for easier inspection when both adjacent frames contain tracklets.
- `combine_log.txt`: log from combining category folders into the all-category folder.

If `num_hypo > 1`, the index changes by hypothesis:

```text
data_0/ trk_withid_0/
data_1/ trk_withid_1/
...
```

Most AB3DMOT examples use one hypothesis and pass `1` to evaluator commands. The evaluator's `num_hypothesis` argument is a count, while `data_0` and `trk_withid_0` are zero-indexed folders.

## Thresholded result folder

Confidence thresholding creates a sibling folder:

```text
results/<dataset>/<result_sha>_thres/
  data_0/
  trk_withid_0/
```

The thresholded folder keeps only tracks whose average score meets the detector/category threshold. Use this folder for:

- KITTI 2D MOT test-server packaging.
- Qualitative visualization, where low-score tracklets are likely false positives.

Do not threshold before official nuScenes validation/test JSON export unless the experiment intentionally evaluates a thresholded operating point.

## Visualization output folder

Visualization reads `trk_withid_<hypothesis_index>/` and writes images and videos into the same result folder:

```text
results/<dataset>/<result_sha>/
  trk_image_vis/
    <sequence>/
      <frame>.jpg
  trk_video_vis/
    <sequence>.mp4
  vis_log.txt
```

For a thresholded visualization, these live under `<result_sha>_thres/`.

Visualization requires image and calibration data for the requested dataset/split. The script has a KITTI mini-data fallback for quick demos when the full KITTI tracking image root is absent. That fallback still requires matching tracking results. nuScenes visualization expects converted nuScenes KITTI-style images/calibration for the target split.

## Metric and export artifacts

KITTI local evaluation writes into `results/KITTI/<result_sha>/`:

```text
summary_<category>_average_eval3D.txt
summary_<category>_average_eval2D.txt
MOTA_recall_curve_<category>_eval3D.pdf
sMOTA_recall_curve_<category>_eval3D.pdf
```

nuScenes official export/evaluation writes into `results/nuScenes/<result_sha>/`:

```text
results_<split>.json
metrics_summary.json
metrics_details.json
plots/
```

nuScenes quick evaluation writes per-category summary files and recall-curve PDFs into the same result folder.

## Submission artifacts

KITTI 2D MOT test submission uses:

```text
results/KITTI/<result_sha>_thres/data_0/
```

nuScenes 3D MOT test submission uses:

```text
results/nuScenes/<result_sha>/results_test.json
```

Both are external/manual gates. Packaging commands should not invent local test metrics.
