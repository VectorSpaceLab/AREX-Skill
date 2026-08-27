# nuScenes evaluation, export, and submission workflows

Use this reference after AB3DMOT has produced a nuScenes tracking result folder under `results/nuScenes/<result_sha>/`, for example `results/nuScenes/megvii_val_H1/`.

## Preconditions and optional dependencies

- Run commands from the AB3DMOT repository root.
- Official nuScenes evaluation and KITTI-to-nuScenes export require the nuScenes development kit stack plus AB3DMOT's helper dependencies. The repo documents `nuscenes-devkit==1.1.9`, `motmetrics<=1.1.3`, and `pandas>=0.24`; the export script also uses Fire and pyquaternion.
- Official local validation requires the full nuScenes metadata/data root for the target version and split. By default, AB3DMOT expects `data/nuScenes/data/` and converted KITTI-style tracking metadata under `data/nuScenes/nuKITTI/tracking/`.
- `results/nuScenes/<result_sha>/data_0/` must exist before converting AB3DMOT's KITTI-format tracking output to nuScenes tracking JSON.
- Test-set labels are not available locally. nuScenes test metrics are an external server/manual gate.

## Convert AB3DMOT tracking results to nuScenes JSON

AB3DMOT stores tracker outputs in KITTI tracking format. Convert them before running official nuScenes tracking evaluation:

```bash
python3 scripts/nuScenes/export_kitti.py kitti_trk_result2nuscenes --result_name megvii_val_H1 --split val
```

Expected artifact:

```text
results/nuScenes/megvii_val_H1/results_val.json
```

For another result folder or split:

```bash
python3 scripts/nuScenes/export_kitti.py kitti_trk_result2nuscenes --result_name <result_sha> --split <train|val|test>
```

The export step requires correspondence files under the converted nuScenes KITTI-style tracking tree. If those files are missing, route back to data-conversion before evaluating.

## Official local nuScenes validation evaluation

After conversion, run the local copy of the official nuScenes tracking evaluator:

```bash
python3 scripts/nuScenes/evaluate.py --result_path ./results/nuScenes/megvii_val_H1/results_val.json
```

A fully explicit validation command is:

```bash
python3 scripts/nuScenes/evaluate.py \
  --result_path ./results/nuScenes/megvii_val_H1/results_val.json \
  --eval_set val \
  --dataroot ./data/nuScenes/data \
  --version v1.0-trainval \
  --render_curves 1 \
  --verbose 1
```

The script's parser exposes `--result_path`, `--output_dir`, `--eval_set`, `--dataroot`, `--version`, `--config_path`, `--render_curves`, `--verbose`, and `--render_classes`. In the repo implementation, metrics are written next to the result JSON path even though `--output_dir` is parsed.

Expected artifacts include:

```text
results/nuScenes/<result_sha>/results_val.json
results/nuScenes/<result_sha>/metrics_summary.json
results/nuScenes/<result_sha>/metrics_details.json
results/nuScenes/<result_sha>/plots/summary.pdf
```

`metrics_summary.json` is the most useful machine-readable local validation output. Treat exact FPS or runtime values as machine-dependent.

## Quick validation evaluation

AB3DMOT also provides a quick validation evaluator adapted from the KITTI evaluation style:

```bash
python3 scripts/nuScenes/evaluate_quick.py megvii_val_H1 1 val
```

Use it when you need a faster local trend check after producing `data_0/`, not as a replacement for the official metric. It uses converted KITTI-style nuScenes validation labels and writes per-class summaries and recall-curve PDFs into `results/nuScenes/<result_sha>/`.

Expected quick-eval artifacts include names such as:

```text
results/nuScenes/<result_sha>/summary_car_average_eval3D.txt
results/nuScenes/<result_sha>/summary_pedestrian_average_eval3D.txt
results/nuScenes/<result_sha>/MOTA_recall_curve_car_eval3D.pdf
```

The quick evaluator is not expected to match official nuScenes numbers exactly. Use it to compare method variants under the same local setup.

## nuScenes test server submission

For the nuScenes test split:

```bash
python3 main.py --dataset nuScenes --det_name megvii --split test
python3 scripts/nuScenes/export_kitti.py kitti_trk_result2nuscenes --result_name megvii_test_H1 --split test
```

Expected submission artifact:

```text
results/nuScenes/megvii_test_H1/results_test.json
```

Compress `results_test.json` as required by the official nuScenes tracking evaluation server and submit externally. Do not claim local test metrics unless an official server result is supplied.

## Confidence thresholding and visualization

nuScenes official sAMOTA-style evaluation uses the raw track scores, so do not threshold before official validation or test JSON export unless you explicitly intend to evaluate a thresholded operating point.

For qualitative visualization, AB3DMOT filters low-score tracklets first:

```bash
python3 scripts/post_processing/trk_conf_threshold.py --dataset nuScenes --result_sha megvii_val_H1
python3 scripts/post_processing/visualization.py --dataset nuScenes --result_sha megvii_val_H1_thres --split val
```

For the provided nuScenes detectors, AB3DMOT's threshold table is:

| Detector | Car | Pedestrian | Truck | Trailer | Bus | Motorcycle | Bicycle |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| megvii | 0.262545 | 0.217600 | 0.294967 | 0.292775 | 0.440060 | 0.314693 | 0.284720 |
| centerpoint | 0.269231 | 0.410000 | 0.300000 | 0.372632 | 0.430000 | 0.368667 | 0.394146 |

The documentation's intended thresholding syntax is `--dataset nuScenes --result_sha <result_sha>` with a space before `--result_sha`.

## Choosing official vs quick evaluation

For `megvii_val_H1` or another validation result:

1. If the question is reportable nuScenes tracking performance, convert to JSON and run official evaluation.
2. If the question is rapid local comparison and full official evaluation is too slow, run quick evaluation after confirming `data_0/` and converted labels exist.
3. If the result is for the test split, export JSON and submit externally; quick/local official test metrics are not available without hidden labels.
4. If the question is qualitative track quality, threshold first and then visualize; keep this separate from official scoring.
