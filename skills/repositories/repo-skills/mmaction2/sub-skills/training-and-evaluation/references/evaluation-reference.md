# Evaluation Reference

MMAction2 evaluation is config-driven: train validation and test metrics come from `val_evaluator` and `test_evaluator`; offline analysis utilities consume result dumps or checkpoint outputs. Keep dataset schemas and config inheritance details in the data/config sub-skill, but use this reference to choose metrics, dumps, and reporting workflows.

## Evaluation flow

1. During training, validation runs when `train_cfg.val_interval` permits it unless `--no-validate` disables validation.
2. Testing assigns `cfg.load_from` to the checkpoint argument and runs the configured test loop/evaluator.
3. `--dump predictions.pkl` adds a dump evaluator so predictions can be evaluated offline or fused with other streams.
4. Offline analysis utilities must use the same compatible config/evaluator semantics as the dumped predictions.

For this version, prediction dumping is the `--dump` flag. If a stale command snippet uses `--out` for test prediction dumps, update it to `--dump`.

Use the bundled command builder to preview the testing portion:

```bash
python scripts/mmaction2_train_test_command_builder.py test --config CONFIG.py --checkpoint CHECKPOINT.pth --work-dir work_dirs/eval_run --dump work_dirs/eval_run/predictions.pkl
```

## Metric families

| Metric/config type | Best fit | Key inputs and outputs | Common pitfalls |
| --- | --- | --- | --- |
| `AccMetric` | Action classification, skeleton classification, audio classification, many recognition configs. | `metric_list` supports `top_k_accuracy`, `mean_class_accuracy`, `mean_average_precision`, and `mmit_mean_average_precision`; default prefix is `acc`; common outputs include `acc/top1`, `acc/top5`, `acc/mean1`. | Multi-label tasks need mAP-style metrics and labels shaped as multi-hot arrays; class count and head output shape must match labels. |
| `ConfusionMatrix` | Single-label classification diagnostics. | Computes `confusion_matrix/result`; can use scores or labels, but label-only predictions require `num_classes`. | Not suitable for multi-label tasks; plotting needs matplotlib and a display or output path. |
| `RetrievalMetric` | Text-video/video retrieval configs. | Accepts paired `video_feature` and `text_feature`; outputs `R1`, `R5`, `R10`, `MdR`, `MnR` under prefix `retrieval`. | Invalid metric names raise errors; features are normalized before similarity. |
| `RetrievalRecall` | Multi-label retrieval-style recall in multimodal tasks. | Outputs `retrieval/Recall@k` for configured `topk`. | `topk` must be positive and no larger than the class dimension for score inputs. |
| `AVAMetric` | AVA spatio-temporal action detection. | Needs annotation CSV, exclude file, label map, action score threshold, class count, and optional custom classes; reports mAP-style outputs. | Annotation/proposal formats and person boxes must match AVA conventions; missing optional detection data is not fixed by evaluator flags. |
| `MultiSportsMetric` | MultiSports frame/video action detection. | Needs annotation pickle; reports `frameAP`, `v_map@<thr>`, and aggregate video mAP entries. | Requires expected annotation structure and normalized boxes in predictions. |
| `ANetMetric` | ActivityNet temporal localization/proposal workflows. | `metric_type='TEM'` dumps intermediate results; `metric_type='AR@AN'` computes AUC and `AR@1`, `AR@5`, `AR@10`, `AR@100`; `dump_config` controls CSV/JSON output. | Localization result paths can be generated artifacts; ensure output directories are intentional. |
| `ActivityNetLocalization` reporting | ActivityNet detection mAP from proposal/detection JSON. | Used by the mAP reporting utility with ground truth and detection output; reports mAP per temporal IoU and average mAP. | Some helper modes attempt to create/download auxiliary classification labels if missing; avoid unapproved network access. |

## Result dump and offline evaluation

Dump predictions during a test run by adding `--dump` to the previewed test command. The dumped file should normally end in `.pkl` or `.pickle` and live under an intentional work directory.

Offline metric evaluation utilities consume the same config plus the dumped predictions. Treat these as user-runtime utilities: run them only in a workspace that provides the corresponding MMAction2 analysis entrypoints and user-approved output paths.

Examples of the logical operations to preview or translate into the user's runtime:

```bash
# test + dump preview through this skill's safe builder
python scripts/mmaction2_train_test_command_builder.py test --config CONFIG.py --checkpoint CHECKPOINT.pth --work-dir work_dirs/eval_run --dump work_dirs/eval_run/predictions.pkl

# offline evaluator shape in a user MMAction2 runtime
python <MMAction2_ANALYSIS_ENTRYPOINT>/eval_metric.py CONFIG.py work_dirs/eval_run/predictions.pkl

# evaluator override shape
python <MMAction2_ANALYSIS_ENTRYPOINT>/eval_metric.py CONFIG.py work_dirs/eval_run/predictions.pkl --cfg-options test_evaluator.metric_list="('top_k_accuracy','mean_class_accuracy')"
```

Offline evaluation fails when the dump does not contain compatible data samples, when the evaluator needs dataset metadata unavailable from the config, or when task-specific annotation files are absent.

## Multi-stream score fusion

Use score fusion when separate streams, such as RGB/pose or joint/bone skeleton streams, each produced dumped predictions with compatible sample order and labels.

Logical utility shape:

```bash
python <MMAction2_ANALYSIS_ENTRYPOINT>/report_accuracy.py --preds stream_a.pkl stream_b.pkl --coefficients 1.0 1.0 --apply-softmax
```

For multi-label classification, add `--multi-label`.

Requirements:

- number of prediction dumps must equal number of coefficients;
- dumps must contain `pred_score` and `gt_label` for each sample;
- sample ordering and label space must match across streams;
- use `--apply-softmax` when dumps contain logits instead of probabilities.

## Confusion matrix reporting

From a checkpoint, the confusion-matrix utility temporarily sets the test evaluator to a confusion matrix and runs test. From an existing prediction dump, it reads predictions directly.

Logical command shapes:

```bash
python <MMAction2_ANALYSIS_ENTRYPOINT>/confusion_matrix.py CONFIG.py CHECKPOINT.pth --out work_dirs/eval_run/confusion_matrix.pkl --show-path work_dirs/eval_run/confusion_matrix.png --include-values

python <MMAction2_ANALYSIS_ENTRYPOINT>/confusion_matrix.py CONFIG.py work_dirs/eval_run/predictions.pkl --label-file labels.txt --target-classes 0 1 2 --show-path work_dirs/eval_run/confusion_subset.png
```

Useful flags:

| Flag | Meaning |
| --- | --- |
| `--out` | Save the raw confusion matrix. |
| `--show` | Display a matplotlib window; avoid on headless machines. |
| `--show-path` | Save a plotted image. |
| `--include-values` | Draw values in the cells. |
| `--label-file` | Provide class names when the dataset cannot. |
| `--target-classes` | Restrict to selected class indices; requires more than one class. |
| `--cmap` | Matplotlib color map, default `viridis`. |
| `--cfg-options` | Override config values before evaluation. |

## ActivityNet mAP reporting

ActivityNet proposal/detection reporting logical shape:

```bash
python <MMAction2_ANALYSIS_ENTRYPOINT>/report_map.py --proposal proposals.json --gt anet_anno_val.json --det-output work_dirs/localization/det_result.json --cls cuhk17_top1
```

Safety caveat: the `cuhk17_top1` helper expects an auxiliary classification prediction JSON in the current working directory and may try to fetch it if absent. Do not run this utility on offline or no-network systems unless that file is already provided and the user approves any output writes.

## Choosing metrics in config overrides

Examples:

Classification top-k and mean-class accuracy:

```bash
--cfg-options test_evaluator.type=AccMetric test_evaluator.metric_list="('top_k_accuracy','mean_class_accuracy')"
```

Multi-label mAP-style classification:

```bash
--cfg-options test_evaluator.type=AccMetric test_evaluator.metric_list="('mean_average_precision','mmit_mean_average_precision')"
```

Confusion matrix evaluator:

```bash
--cfg-options test_evaluator.type=ConfusionMatrix test_evaluator.num_classes=NUM_CLASSES
```

Retrieval evaluator:

```bash
--cfg-options test_evaluator.type=RetrievalMetric test_evaluator.metric_list="('R1','R5','R10','MdR','MnR')"
```

Do not use these overrides to paper over mismatched datasets or heads. If annotation format, `data_prefix`, class names, or pipeline fields are wrong, route to the data/config sub-skill first.
