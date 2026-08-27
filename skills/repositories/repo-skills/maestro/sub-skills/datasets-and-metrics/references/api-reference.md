# API reference

Use these import paths and signatures when wiring Maestro data and metric helpers into a model-specific workflow.

## Dataset loaders and adapters

| Import | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `maestro.trainer.common.datasets.jsonl.JSONLDataset` | `(annotations_path: str, images_directory_path: str) -> None` | Load a JSONL split as `(PIL.Image.Image, dict)` pairs | Keeps only valid rows; skips bad JSON, missing keys, and missing images with warnings. |
| `maestro.trainer.common.datasets.jsonl.is_jsonl_dataset` | `(dataset_location: str) -> bool` | Detect JSONL layout | Returns `True` if any split contains `annotations.jsonl`. |
| `maestro.trainer.common.datasets.coco.COCODataset` | `(annotations_path: str, images_directory_path: str) -> None` | Load a COCO split as `(PIL.Image.Image, supervision.Detections)` pairs | Delegates parsing to `supervision`. Missing images are skipped. |
| `maestro.trainer.common.datasets.coco.COCOVLMAdapter` | `(coco_dataset, prefix_formatter, suffix_formatter)` | Convert COCO detections into VLM prefix/suffix records | Formatter callbacks receive `(boxes, class_ids, class_names, image_size)`. |
| `maestro.trainer.common.datasets.coco.is_coco_dataset` | `(dataset_location: str) -> bool` | Detect COCO layout | Returns `True` if any split contains `_annotations.coco.json`. |
| `maestro.trainer.common.datasets.core.resolve_dataset_path` | `(dataset_id: str) -> Optional[str]` | Resolve a local path or download a Roboflow dataset | Uses `ROBOFLOW_API_KEY` for remote resolution. |
| `maestro.trainer.common.datasets.core.create_data_loaders` | `(dataset_location, train_batch_size, train_collect_fn, train_num_workers=0, test_batch_size=None, test_collect_fn=None, test_num_workers=None, detections_to_prefix_formatter=None, detections_to_suffix_formatter=None) -> tuple[DataLoader, Optional[DataLoader], Optional[DataLoader]]` | Build train/valid/test loaders | Requires all three splits. COCO input requires both formatter callbacks. |
| `maestro.trainer.common.datasets.roboflow.parse_roboflow_identifier` | `(identifier: str) -> Optional[tuple[str, str, Optional[int]]]` | Parse Roboflow workspace, project, and optional version | Accepts app/universe/roboflow domains, with or without `https://`. |

## Roboflow constants

| Name | Value | Notes |
| --- | --- | --- |
| `ROBOFLOW_PROJECT_TYPE_TO_DATASET_FORMAT` | `{"object-detection": "coco", "text-image-pairs": "jsonl"}` | Used by `resolve_dataset_path()`. |
| `ROBOFLOW_JSONL_FILENAME` | `annotations.jsonl` | Split annotation file expected by JSONL datasets. |
| `ROBOFLOW_COCO_FILENAME` | `_annotations.coco.json` | Split annotation file expected by COCO datasets. |

## Metrics

| Import | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `maestro.trainer.common.metrics.parse_metrics` | `(metrics: list[str]) -> list[BaseMetric]` | Build metric objects from names | Names are case-insensitive. Supported names: `edit_distance`, `bleu`, `mean_average_precision`. |
| `maestro.trainer.common.metrics.EditDistanceMetric` | `name = "edit_distance"` | Normalized string distance | Lower is better; returns `{"edit_distance": value}`. |
| `maestro.trainer.common.metrics.BLEUMetric` | `name = "bleu"` | BLEU score via `evaluate.load("bleu")` | Returns `{"bleu": value}`. |
| `maestro.trainer.common.metrics.MeanAveragePrecisionMetric` | `name = "mean_average_precision"` | Class-agnostic mAP via `supervision` | Returns `map50:95`, `map50`, and `map75`. |
| `maestro.trainer.common.metrics.MetricsTracker` | `init(metrics: list[str])`, `register(metric, epoch, step, value)`, `describe_metrics()`, `get_metric_values(metric, with_index=True)`, `as_json(output_dir=None, filename=None)` | Store per-step metric history | `as_json()` creates the output directory when needed. |
| `maestro.trainer.common.metrics.aggregate_by_epoch` | `(metric_values: list[tuple[int, int, float]]) -> dict[int, float]` | Average tracked values per epoch | Used by `save_metric_plots()`. |
| `maestro.trainer.common.metrics.save_metric_plots` | `(training_tracker, validation_tracker, output_dir) -> None` | Save one plot per metric | Writes `<metric>_plot.png`. |

## Utilities

| Import | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `maestro.trainer.common.utils.device.parse_device_spec` | `(device_spec: str | torch.device) -> torch.device` | Normalize device strings | Accepts `auto`, `cpu`, `cuda`, `cuda:N`, and `mps`. |
| `maestro.trainer.common.utils.device.device_is_available` | `(device: torch.device) -> bool` | Check whether a parsed device is actually available | `cpu` always returns `True`. |
| `maestro.trainer.common.utils.path.create_new_run_directory` | `(base_output_dir: str) -> str` | Create the next numeric run directory | Returns the absolute path to the new directory. |
| `maestro.trainer.common.utils.seed.ensure_reproducibility` | `(seed: Optional[int] = None, disable_cudnn_benchmark: bool = True, avoid_non_deterministic_algorithms: bool = True) -> None` | Seed RNGs and tighten deterministic settings | `seed=None` skips RNG seeding but still applies the deterministic flags unless you disable them. |

## Practical import pattern

```python
from maestro.trainer.common.datasets.core import create_data_loaders
from maestro.trainer.common.metrics import MetricsTracker, parse_metrics
from maestro.trainer.common.utils.device import parse_device_spec
from maestro.trainer.common.utils.path import create_new_run_directory
from maestro.trainer.common.utils.seed import ensure_reproducibility
```

For COCO workflows, keep the prefix/suffix formatter functions in the model-specific sub-skill and pass them into `create_data_loaders()` or `COCOVLMAdapter()` from here.
