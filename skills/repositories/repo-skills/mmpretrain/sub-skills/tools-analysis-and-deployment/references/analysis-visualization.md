# Analysis and Visualization

This reference covers post-run analysis, plots, and offline metrics that operate on saved logs, result files, or checkpoints.

## Dependency gates

| Workflow family | Core dependencies | Optional dependencies | Headless-safe path |
| --- | --- | --- | --- |
| Log summaries, result metrics, confusion matrices, FLOPs | `torch`, `mmcv`, `mmengine`, `matplotlib` | `seaborn` for styling | Save to file instead of opening a window |
| Dataset browser and scheduler plots | `torch`, `mmengine`, `matplotlib` | `seaborn` | Use `--output-dir` / `--save-path` and `--not-show` |
| CAM visualization | core stack plus model and image loading | `grad-cam>=1.3.6` | Use `--save-path` |
| t-SNE visualization | core stack plus model and image loading | `scikit-learn` | Use `--work-dir` and save plots |

## Command contracts

| Tool | Input contract | Output contract | Notes |
| --- | --- | --- | --- |
| `analyze_logs` | One or more JSON log files. `plot_curve` accepts curve keys, legend labels, title, style, output path, and window size. `cal_train_time` reads `time` and `epoch` fields from the train stream. | Printed timing summary or a curve image saved to disk. | Use the bundled `scripts/analyze_json_log.py` when you want a safe summary helper with file output by default. |
| `analyze_results` | A config plus a saved prediction result file. The result file must contain per-sample labels and scores, and the dataset in the config must be able to resolve the sample images. | A `success/` and `fail/` image gallery plus a JSON manifest. | Best for inspecting the most confident correct and incorrect predictions. |
| `eval_metric` | A saved prediction file plus one or more metric configs such as `type=Accuracy topk=1,5`. | A metric dictionary printed to stdout. | The result file must contain prediction samples in the expected offline-evaluation format. |
| `confusion_matrix` | A config plus either a checkpoint or a prediction file. Supports `--show`, `--show-path`, `--out`, `--include-values`, `--cmap`, and config overrides. | A saved confusion matrix tensor and optional plot image. | If a checkpoint is provided, the command runs the test loop; if a result file is provided, it evaluates offline. |
| `get_flops` | A config or model reference plus an optional input shape. | FLOPs, parameters, activations, and a layer table printed to stdout. | Treat the result as an approximation; unsupported ops are not counted. |
| `browse_dataset` | A model config with a dataset definition and the target phase. Supports `original`, `transformed`, `concat`, and `pipeline` modes. | A browser window or a saved image set. | Use `--output-dir` and `--not-show` for headless browsing. |
| `vis_scheduler` | A config plus optional dataset size, GPU count, title, style, and save path. | A learning-rate, momentum, or weight-decay curve plot. | Set `--dataset-size` to skip dataset construction when you only need the schedule shape. |
| `vis_cam` | An image, a config, and a checkpoint. Optional target layers, target category, ViT reshaping flags, and CAM method. | A CAM overlay saved to disk or shown on screen. | Requires the optional CAM package; use `--preview-model` when you need layer names. |
| `vis_tsne` | A config, optional checkpoint, optional test config, class filters, feature-stage choice, and t-SNE settings. | Saved feature arrays, plots, and a log under a work directory. | Requires `scikit-learn`; use `--test-cfg` if the base config has no test dataloader. |

## Inputs and outputs by workflow

### Log analysis
- **Input:** JSON log lines with train and validation records.
- **Useful fields:** `time`, `step`, `epoch`, and any scalar metric key such as `loss` or `accuracy/top1`.
- **Outputs:** timing summary to stdout or a saved curve image.
- **Safe choice:** use the helper script when you need a quick summary or a file-only plot in a headless environment.

### Offline metrics
- **Input:** a saved prediction file from testing or inference export.
- **Typical metrics:** accuracy, precision, recall, F1-score, average precision, recall-at-k, and retrieval metrics.
- **Outputs:** a printed metric dictionary.
- **Caution:** the prediction file must contain the prediction fields expected by the metric you choose.

### Confusion matrix
- **Input:** config plus result file or checkpoint.
- **Outputs:** a tensor-like matrix and, optionally, a rendered heatmap.
- **Caution:** if the dataset does not provide class names, the plot will fall back to numeric labels.

### FLOPs / params
- **Input:** config or model reference, plus image shape.
- **Outputs:** total FLOPs, parameters, activations, and the layer breakdown.
- **Caution:** only supported operators are counted, and the result is meant for comparison rather than strict reporting.

### Dataset and schedule visualization
- **Input:** model config with dataset and scheduler sections.
- **Outputs:** browser figures or schedule curves.
- **Caution:** for browser-style commands, use save paths in non-GUI environments.

### CAM and t-SNE
- **Input:** a real image for CAM; a config, checkpoint, and dataset for t-SNE.
- **Outputs:** overlays, feature arrays, scatter plots, and logs.
- **Caution:** CAM target layers for ViT-like backbones often need explicit layer names and `--vit-like`.

## When to prefer the bundled helper scripts

- Use `scripts/analyze_json_log.py` when you want a short, file-safe summary of a JSON log and an optional saved curve plot.
- Use `scripts/estimate_flops.py` when you want a CPU-only complexity estimate from a config or model reference without invoking the full source tool.
- Use `scripts/publish_checkpoint.py` when you want a publish-ready checkpoint artifact while preserving the input file.

## Verification-friendly cases

- A tiny JSON log with training and validation records should produce a timing summary and a saved accuracy curve.
- A small published checkpoint should keep the source file unchanged while dropping training-only fields and optional EMA containers.
