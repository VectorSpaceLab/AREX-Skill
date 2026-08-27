# Analysis and utilities

## Purpose

This reference covers BEVFormer log analysis and utility workflows that do not change model training state. It helps future agents decide whether a request is safe to handle locally, checkpoint-bound, or data-bound.

## Read when

- the user wants to summarize JSON or JSONL logs
- the user asks about `analyze_logs`, `benchmark`, `visual`, `get_params`, `fuse_conv_bn`, or `visualize_results`
- the user wants to compare a run against public model zoo logs from the project README
- the user asks whether a utility can run without a dataset, checkpoint, or GPU

## Verified source behavior

| Source | Verified behavior | Skill consequence |
| --- | --- | --- |
| `tools/analysis_tools/analyze_logs.py` | Parses JSON logs and supports `plot_curve` and `cal_train_time`; the repo script expects `.json` files and `epoch`-grouped records. | Use the bundled helper for safe log summaries instead of re-running the source analyzer. |
| `tools/analysis_tools/get_params.py` | Loads a checkpoint with `torch.load` and counts parameters in `state_dict`. | Checkpoint-only, CPU-friendly utility; useful when a user wants a size check, not a training result. |
| `tools/analysis_tools/benchmark.py` | Builds dataset and detector objects, wraps them in CUDA data parallelism, and reports throughput. | Data- and GPU-bound; not a safe static-analysis substitute. |
| `tools/analysis_tools/visual.py` | Imports nuScenes and matplotlib, loads prediction results, and renders camera and BEV views. | Visualization-only workflow that needs the dataset and prediction artifacts. |
| `tools/misc/fuse_conv_bn.py` | Builds a model from config and checkpoint, fuses Conv+BN, and writes a new checkpoint. | Checkpoint-mutating utility; never suggest it for the only copy of a model file. |
| `tools/misc/visualize_results.py` | Builds a dataset from config, loads result pickles, and calls dataset display methods. | Data/result-bound visualization; requires the dataset and result artifacts. |

## Safe versus gated

### Safe on tiny fixtures
- `scripts/summarize_bevformer_log.py`

### Checkpoint-bound but CPU-friendly
- `get_params`
- `fuse_conv_bn`

### Data- or GPU-bound
- `benchmark`
- `visual`
- `visualize_results`

## Log summarization workflow

1. Point the bundled helper at one or more log files.
2. Choose `--metric` with a key that appears in the log, such as `NDS`, `mAP`, or `bbox_mAP`.
3. Compare the selected metric with `loss` and `lr` to spot divergence, plateaus, or unstable learning rate schedules.
4. If the file contains parse noise or interleaved record types, keep the input and inspect the keys before retrying.
5. Use the public model zoo logs from the README as comparison anchors when a summary needs context, but do not treat a single mismatch as proof of failure.

## Utility notes

- The bundled summarizer is intentionally smaller than the source analyzer and accepts JSON or JSONL logs without repo imports.
- `benchmark`, `visual`, and `visualize_results` are reference-only here because they need dataset or checkpoint artifacts that are not safe to assume.
- `fuse_conv_bn` changes the checkpoint output path; always write to a new file.

## Bundled helper

- [scripts/summarize_bevformer_log.py](../scripts/summarize_bevformer_log.py)
