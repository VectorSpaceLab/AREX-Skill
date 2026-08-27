# Scenic data formats, config fields, and external-data boundaries

Use this reference to explain what a Scenic dataset builder expects or returns without opening project files or downloading data.

## Common config fields

Most training configs expose these dataset-related keys:

| Config key | Used for |
| --- | --- |
| `config.dataset_name` | Registry key passed to `datasets.get_dataset`. |
| `config.dataset_configs` | Dataset-specific nested configuration passed unchanged to the builder. |
| `config.batch_size` | Global training batch size; must be divisible by `jax.device_count()`. |
| `config.eval_batch_size` | Optional global eval/test batch size; defaults to `batch_size`; must be divisible by `jax.device_count()`. |
| `config.data_dtype_str` | Image/input dtype string passed to builders, commonly `float32`. |
| `config.shuffle_seed` | Optional training shuffle seed. Must be `None` when using `tf.data` service. |

`train_utils.get_dataset` converts global batch sizes to per-host batch sizes before calling the builder. A builder's `batch_size` argument is therefore the local host batch size, not necessarily the global training batch.

## Common batch keys

| Key | Meaning | Notes |
| --- | --- | --- |
| `inputs` | Primary model input tensor/array. | Images usually use NHWC; video often uses time before spatial dimensions. |
| `label` | Class label, segmentation mask, one-hot vector, or task target. | `meta_data['target_is_onehot']` says whether classification labels are one-hot. |
| `batch_mask` | Float mask for true examples vs padding. | Added by `maybe_pad_batch`; partial eval/test batches are padded, partial train batches should be dropped before this point. |
| `file_name`, `key`, `tfds_id`, task-specific ids | Optional provenance/identity fields. | May be removed by TPU dtype filtering in BigTransfer unless explicitly preserved/supported. |

Shape progression:

1. TFDS/raw examples are mapped into per-example dictionaries.
2. A `tf.data.Dataset` batches examples into `[local_batch, ...]`.
3. After `tf_to_numpy` and `maybe_pad_batch`, `dataset_utils.shard` reshapes arrays to `[num_local_shards, local_batch / num_local_shards, ...]`.
4. Some JIT-oriented pipelines use `dataset_utils.shard_jit` with a global device mesh instead of the simple leading-axis reshape.

## `Dataset.meta_data` conventions

Common metadata fields:

| Field | Meaning |
| --- | --- |
| `input_shape` | Usually `(-1, ...)`; used for initialization/compile in older image builders. |
| `input_spec` | Nested shape/dtype spec, common in FlexIO and newer pipelines. |
| `num_train_examples`, `num_eval_examples`, `num_test_examples` | Split sizes used for training-step and eval-loop calculations. |
| `num_classes` | Classification/segmentation class count when applicable. |
| `input_dtype` | JAX dtype object for inputs. |
| `target_is_onehot` | Whether labels are one-hot encoded. |

Do not infer model head behavior from metadata alone. Route model-head and loss interpretation to `modeling-and-layers` after identifying the dataset output keys here.

## Built-in TFDS-backed dataset formats

| Dataset name | Main outputs | Config fields worth checking | External data requirement |
| --- | --- | --- | --- |
| `mnist`, `fashion_mnist` | `inputs` shape `28x28x1`, integer `label`, `batch_mask`. | Usually no dataset-specific fields. | TFDS prepared/downloadable data required to build. |
| `cifar10` | `inputs` shape `32x32x3`, `label`, optional one-hot/mixup, `batch_mask`. | `data_augmentations`; `cifar_default` is included; `mixup` requires one-hot labels. | TFDS data required. |
| `svhn` | `inputs` shape `32x32x3`, `label`, `batch_mask`. | `data_augmentations`, e.g. random crop/flip. | TFDS data required. |
| `imagenet` | `inputs` shape `224x224x3`, `label`, `batch_mask`. | `data_augmentations`, `onehot_labels`, `prefetch_buffer_size`. | ImageNet TFDS data must already be available or explicitly downloaded. |
| `cityscapes` | `inputs`, segmentation `label`, pixel-aware `batch_mask`. | `target_size`, `train_split`; label remapping excludes void/rare classes. | Cityscapes TFDS data and license-gated assets may be required. |
| `oxford_pets` | `inputs`, segmentation `label`, `batch_mask`. | Fixed resize to the configured image size. | TFDS data required. |
| `bair` | `inputs` video clips, no class labels. | `camera_name`, `num_frames`, `stride`, `zero_centering`, `num_eval_clips`, `shuffle_buffer_size`, `prefetch_to_device`. | TFDS data required. |
| `bit` | `inputs`, `label`, optional provenance fields, `batch_mask`; metadata from TFDS and config. | `dataset`, `train_split`, `val_split`, `pp_train`, `pp_eval`, `num_classes`, prefetch/cache/skip-decode fields. | TFDS data for the configured `dataset`. |
| `flexio` | Keys are defined by TFDS source features and CLU preprocessing specs; may use non-`inputs` names. | `pp_libs`, `train/eval/test.sources`, source `tfds_name`, `split`, preprocessing specs, `merge_sources`, `padded_batch`, `return_*`. | TFDS or Grain-accessible data and preprocessing libraries required. |

## COCO utilities and caveats

The bundled COCO utility surface is primarily label-map support and shared constants for COCO-like datasets.

`get_label_map(tfds_name)` behavior:

| `tfds_name` | Intended result | Caveat |
| --- | --- | --- |
| `coco/2017` | `{0: 'padding', 1: 'person', ..., 80: 'toothbrush'}` for COCO thing classes. | Self-contained in the utility. |
| `coco/2017_panoptic` | Padding plus COCO thing and stuff classes. | Self-contained in the utility. |
| `ref_coco` | Padding plus RefCOCO class labels. | Self-contained in the utility. |
| `lvis`, `objects365`, `scenic:objects365`, `open_images*` | Label maps backed by packaged label-map assets/helpers. | Treat as optional: verify the installed package has the helper functions and data files before relying on them. |
| Any other name | Raises `ValueError('Unsupported TFDS name: ...')`. | Fix the name or provide a separate label map. |

COCO/DETR-style input pipelines and evaluation often require external annotations, image directories, and optional packages such as `pycocotools`. A request to "convert COCO" or "use COCO TFRecords" without data present should be answered with a preflight checklist, not a conversion run.

Minimum preflight for COCO-like data:

- Dataset/task: detection, instance segmentation, panoptic segmentation, referring expressions, open-vocabulary, or evaluation-only.
- Annotation files: JSON path(s), split names, label-map source, and whether category ids are contiguous or COCO-original ids.
- Image roots or TFDS data directory.
- Optional dependencies: `pycocotools` for many COCO annotation/eval flows; TensorFlow/TFDS for TFDS-backed loading.
- Output intent: use an existing TFDS/Scenic pipeline, write TFRecords, or only inspect labels/metadata.
- Non-destructive policy: never overwrite annotations or generated records without an explicit output directory and user approval.

## FlexIO format expectations

FlexIO does not impose `inputs`/`label`; it preserves whatever feature names the preprocessing ops produce. A downstream model may expect `inputs`, task-specific names, or CLU/grand-vision modality constants. Check `meta_data['input_spec']` after a real data-approved build, or infer expected keys from the user's provided preprocessing specs.

TFDS source block checklist:

```python
{
  'source': 'tfds',
  'tfds_name': '...',
  'split': 'train' | 'validation' | 'test' | 'custom split expression',
  'shuffle_buffer_size': 1000,
  'cache': False,
  'preproc_spec': '...',
  'postproc_spec': '...',
  'skip_decoders': ['image'],
  'repeat_dataset': True,
  'weight': 1.0,  # only when merged with other sources
}
```

Grain source block checklist:

```python
{
  'source': 'grain',
  'tfds_name': '...',
  'split': 'train',
  'batch_size': None,
  'preproc_spec': '...',
  'postproc_spec': '...',
  'grain_configs': {},
  'drop_grain_meta_features': True,
}
```

Grain requires `start_step` at dataset construction time. Cache is unsupported for Grain-backed sources; per-source `shuffle_buffer_size` is also rejected because Grain uses global shuffle.

## TFRecord/project dataset caveats

Several project datasets use registry names such as `video_tfrecord_dataset`, `av_asr_tfrecord_dataset`, `coco_detr_detection`, or project-specific names. These typically require `dataset_configs` fields like:

- `base_dir`: root directory for records/assets.
- `tables`: mapping of split names to TFRecord/table patterns.
- `examples_per_subset`: split sizes used for loop scheduling.
- `num_frames`, `stride`, `test_stride`, `num_test_clips`, `num_train_val_clips` for video.
- `min_resize`, `crop_size`, augmentation settings, `zero_centering` for image/video preprocessing.
- `num_classes`, `class_splits`, `split_names`, or task-specific label maps.
- `modalities`, `return_as_dict`, text/tokenizer paths, caption fields, or feature dimensions for audiovisual/text projects.
- `test_batch_size`, `do_multicrop_test`, `do_three_spatial_crops`, `log_test_epochs` for eval variants.

If the user has no data present, you can still validate that these keys are named and shaped plausibly. Do not attempt to open records, enumerate examples, or convert formats until data paths are supplied and the user approves the run.

## When external data is required

External data is required for:

- Any call that produces real dataset iterators or split sizes from TFDS.
- Any call to `dataset_utils.get_num_examples` for TFDS data.
- Any TFRecord pipeline that enumerates examples or reads schemas from files.
- COCO conversion/evaluation against annotations or images.
- BigTransfer/FlexIO builds beyond preprocessing-string parsing and registry import.

Useful no-data alternatives:

- Registry lookup only.
- Config-key checklist.
- Preprocessing-string syntax review.
- Dependency import check.
- Shape/key expectations from the selected dataset family.
