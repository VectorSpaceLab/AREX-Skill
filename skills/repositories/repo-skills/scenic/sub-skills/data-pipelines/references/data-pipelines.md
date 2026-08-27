# Scenic dataset registry and input-pipeline construction

This reference is for reasoning about Scenic inputs without reading source files or downloading data. Treat it as the local operating guide for registry lookup, dataset-builder calling conventions, TFDS/tf.data service assumptions, BigTransfer preprocessing, and FlexIO.

## Safety model: what is safe without data?

Safe by default:

- Import `scenic.dataset_lib.datasets`.
- Inspect `DatasetRegistry.list()` and the lazy import table.
- Import a known dataset registration module if the user accepts optional dependency imports.
- Call `datasets.get_dataset(name)` or `DatasetRegistry.get(name)` to retrieve a builder function.

Not safe without explicit user consent and data/runtime budget:

- Calling a dataset builder function returned by the registry.
- Calling `train_utils.get_dataset(...)`.
- Calling TFDS-backed helpers that run `download_and_prepare()` or read prepared TFDS data.
- Running COCO/TFRecord conversion or evaluation utilities against user data.

Use the bundled `scripts/check_dataset_registry.py` helper for safe inspection.

## Dataset registry contract

Scenic's central registry is `scenic.dataset_lib.datasets.DatasetRegistry`.

| API | Purpose | Failure mode |
| --- | --- | --- |
| `DatasetRegistry.add(name, builder_fn)` | Register a dataset builder under a unique string name. | Raises `KeyError` if the name is already registered. |
| `@datasets.add_dataset(name)` | Decorator that registers the decorated builder when its module is imported. | Registration happens only after module import. |
| `DatasetRegistry.get(name)` / `datasets.get_dataset(name)` | Return the registered builder function. If `name` is in the lazy table, import that module first. | Raises `KeyError` for unknown names or for a lazy module that imported but did not register the requested name. |
| `DatasetRegistry.list()` | List names that are already registered in this Python process. | Only includes modules imported so far; it is not the full lazy table. |

Practical implication: if `dataset_name` is unknown, do not immediately edit code. First decide whether the name should be one of the built-in lazy names, or whether it belongs to a project module that must be imported before lookup.

## Built-in lazy import names

The repository-level lazy table maps these names to registration modules. Importing the module registers the builder; it does not by itself build a dataset.

| `dataset_name` | Registered by module | Notes |
| --- | --- | --- |
| `cifar10` | `scenic.dataset_lib.cifar10_dataset` | TFDS image classification. |
| `cityscapes` | `scenic.dataset_lib.cityscapes_dataset` | TFDS semantic segmentation. |
| `imagenet` | `scenic.dataset_lib.imagenet_dataset` | TFDS ImageNet 2012; requires prepared/downloadable data for actual loading. |
| `fashion_mnist` | `scenic.dataset_lib.fashion_mnist_dataset` | TFDS image classification. |
| `mnist` | `scenic.dataset_lib.mnist_dataset` | TFDS image classification. |
| `bair` | `scenic.dataset_lib.bair_dataset` | TFDS video prediction-style batches. |
| `oxford_pets` | `scenic.dataset_lib.oxford_pets_dataset` | TFDS segmentation. |
| `svhn` | `scenic.dataset_lib.svhn_dataset` | TFDS image classification. |
| `video_tfrecord_dataset` | `scenic.projects.vivit.data.video_tfrecord_dataset` | Project TFRecord video pipeline; external TFRecord tables required to build. |
| `av_asr_tfrecord_dataset` | `scenic.projects.avatar.datasets.av_asr_tfrecord_dataset` | Project audiovisual/ASR TFRecord pipeline; external data required. |
| `bit` | `scenic.dataset_lib.big_transfer.bit` | BigTransfer/VTAB-style TFDS pipeline with preprocessing strings. |
| `bert_wikibooks` | `scenic.projects.baselines.bert.datasets.bert_wikibooks_dataset` | Baseline BERT dataset; project dependencies/data apply. |
| `bert_glue` | `scenic.projects.baselines.bert.datasets.bert_glue_dataset` | Baseline GLUE dataset; project dependencies/data apply. |
| `coco_detr_detection` | `scenic.projects.baselines.detr.input_pipeline_detection` | COCO/DETR-style detection input; annotation/data dependencies apply. |
| `cityscapes_variants` | `scenic.projects.robust_segvit.datasets.cityscapes_variants` | Robust SegViT variant registration. |
| `robust_segvit_segmentation` | `scenic.projects.robust_segvit.datasets.segmentation_datasets` | Robust SegViT segmentation. |
| `robust_segvit_variants` | `scenic.projects.robust_segvit.datasets.segmentation_variants` | Robust SegViT variants. |
| `flexio` | `scenic.dataset_lib.flexio.flexio` | Flexible TFDS/Grain input pipeline. |

Custom project names may exist outside this table. They are not visible until their project dataset module is imported.

## Safe registry commands

From an environment where Scenic is importable:

```bash
python skills/disco/scenic/sub-skills/data-pipelines/scripts/check_dataset_registry.py --list
python skills/disco/scenic/sub-skills/data-pipelines/scripts/check_dataset_registry.py --dataset-name cifar10
python skills/disco/scenic/sub-skills/data-pipelines/scripts/check_dataset_registry.py \
  --import-module scenic.projects.example_project.input_pipeline \
  --dataset-name custom_name
```

The helper only imports modules and performs registry lookup. It intentionally does not call the returned dataset builder.

## `train_utils.get_dataset` contract

Scenic's training utilities build datasets through:

```python
train_utils.get_dataset(
    config,
    data_rng,
    num_local_shards=None,
    dataset_service_address=None,
    dataset_name=None,
    dataset_configs=None,
    **kwargs,
)
```

Key behavior:

1. `dataset_name = dataset_name or config.dataset_name`.
2. `dataset_builder = datasets.get_dataset(dataset_name)` uses the registry/lazy import behavior above.
3. `config.batch_size` and `config.get('eval_batch_size', config.batch_size)` must each be divisible by `jax.device_count()`.
4. The builder receives per-host batch sizes: `batch_size // jax.process_count()` and `eval_batch_size // jax.process_count()`.
5. `num_shards` defaults to `jax.local_device_count()` unless `num_local_shards` is passed.
6. The builder receives `dtype_str=config.data_dtype_str`, `rng=data_rng`, `shuffle_seed=config.get('shuffle_seed', None)`, `dataset_configs=dataset_configs or config.get('dataset_configs', {})`, `dataset_service_address=...`, and any extra `**kwargs`.
7. If `dataset_service_address` is set and `shuffle_seed` is not `None`, Scenic raises a `ValueError`; set `config.shuffle_seed = None` for data-service runs.

Do not call this helper as a diagnostic unless the user has supplied/approved real data and runtime budget.

## Dataset object and batch pipeline conventions

Scenic builders return a `dataset_utils.Dataset` dataclass with these common fields:

- `train_iter`, `valid_iter`, `test_iter`: iterators or iterator providers yielding nested dictionaries of NumPy/JAX-compatible arrays.
- `meta_data`: model/trainer metadata such as `input_shape`, `input_spec`, `num_train_examples`, `num_eval_examples`, `num_test_examples`, `num_classes`, `input_dtype`, and `target_is_onehot`.
- Optional raw `train_ds`, `valid_ds`, `test_ds` fields for builders that return underlying `tf.data.Dataset` objects.
- Optional multi-dataset lists for builders that expose multiple train/eval/test streams.

Common transformations:

1. TFDS examples are mapped to Scenic keys such as `inputs` and `label`.
2. `dataset_utils.tf_to_numpy` converts TensorFlow tensors to NumPy arrays.
3. `dataset_utils.maybe_pad_batch` adds or updates `batch_mask`; partial training batches are treated as errors because train pipelines should use `drop_remainder=True`.
4. `dataset_utils.shard` reshapes leading batch dimension from `[local_batch, ...]` to `[num_local_shards, local_batch / num_local_shards, ...]` for `pmap`-style training.
5. Some builders call `flax.jax_utils.prefetch_to_device` when `dataset_configs.prefetch_to_device` or a builder-specific prefetch size is set.

## TFDS helpers and data service assumptions

`dataset_utils.load_split_from_tfds(...)` and `load_split_from_tfds_builder(...)` are convenience helpers for TFDS-backed datasets. Important details:

- They call `builder.download_and_prepare()` before creating the split, so they are not no-data diagnostics.
- Each host reads `tfds.even_splits(split, jax.process_count())[jax.process_index()]`.
- Preprocessing runs before cache; training splits repeat, augment, shuffle, and batch with `drop_remainder=True`; non-training splits batch with `drop_remainder=False` and repeat.
- They set a private TensorFlow threadpool and prefetch with AUTOTUNE.

`dataset_utils.get_data(...)` / `make_pipeline(...)` are the newer compatibility helpers used by BigTransfer:

- `get_dataset_tfds(...)` uses `tfds.builder(..., try_gcs=True)`, host-even splits with `drop_remainder=True`, optional skip decoders, and `tfds.ReadConfig(skip_prefetch=True, try_autocache=False, add_tfds_id=True)`.
- `make_pipeline(...)` supports `cache='loaded'`, `cache='batched'`, `cache=False/None`, `repeat_after_batching`, `ignore_errors`, explicit `prefetch`, and optional `dataset_service_address`.
- For eval/non-train splits, `get_data(...)` disables data service.

`tf.data` service:

- Built-in image/video builders apply data service only to the training dataset.
- A random `shuffle_seed` with data service is rejected because every worker would produce identical shuffled data.
- The registered service job name is `scenic_data_pipeline`.

## BigTransfer (`dataset_name='bit'`)

The `bit` builder wraps BigTransfer/VTAB-style TFDS input pipelines and uses preprocessing strings.

Required/typical `dataset_configs` keys:

| Key | Meaning |
| --- | --- |
| `dataset` | TFDS dataset name, for example `imagenet2012` or a controlled-noisy-label dataset. |
| `train_split` | Training split string. |
| `val_split` | Evaluation split string or a list of eval specs. Four-item eval specs are `(name, dataset, split, pp_eval)`; five-item specs add `dataset_dir`. |
| `pp_train`, `pp_eval` | BigTransfer preprocessing strings. |
| `num_classes` | Recommended for classification metadata. If missing, the builder logs a warning. |
| `shuffle_buffer_size` | Used for training unless a single shard shortcut applies. |
| `dataset_dir` | Optional TFDS data directory. |
| `prefetch_to_host` | `tf.data` prefetch count before host iteration, default usually `2`. |
| `prefetch_to_device` | Optional device prefetch count. |
| `cache` | `None`/`False`, `loaded`, or `batched` depending on the pipeline stage. |
| `skip_decode` | Feature names or nested structure to decode lazily, usually image-related. |
| `remove_tpu_dtypes` | Drop non-TPU-compatible fields after preprocessing, default `True`. |
| `extra_meta_data` | Extra metadata copied into `Dataset.meta_data`. |

Preprocessing minilanguage:

```text
op|op(arg1, arg2)|op(key=value)|...
```

Each token is looked up in the BigTransfer preprocessing registry under `preprocess_ops.<token>`. Examples include:

```text
inception_crop|resize(256)|random_crop(240)|flip_lr|-1_to_1
```

Common registered operation names include `decode`, `decode_jpeg_and_center_crop`, `decode_jpeg_and_inception_crop`, `inception_crop`, `resize`, `resize_small`, `central_crop`, `random_crop`, `flip_lr`, `flip_ud`, `value_range`, `standardize`, `onehot`, `keep`, `drop`, `copy`, `delete_field`, `pad`, `patchify`, `extract_patches`, `randaug`, `random_brightness`, `random_contrast`, `random_hue`, `random_saturation`, `random_rotate`, `random_rotate90`, and `rotate`.

Failure interpretation:

- Unknown operation name: misspelled preprocessing string or missing preprocessing library import.
- `tensorflow_addons` import/runtime errors: BigTransfer rotate/randaugment-related ops depend on TensorFlow Addons image functions.
- Removed field after preprocessing: non-TPU dtype filtering is active; either keep only supported fields or set `remove_tpu_dtypes=False` if the downstream can handle those fields.

## FlexIO (`dataset_name='flexio'`)

FlexIO is a lightweight, configurable input pipeline for TFDS and Grain-backed sources.

Builder requirements:

- `rng` is required.
- `shuffle_seed` must be falsey; use the JAX RNG instead.
- `dataset_service_address` is unsupported and must be `None`.
- `dtype_str` must be `float32`.
- Grain-backed datasets require `start_step` so the loader can compute a deterministic start index.

Top-level `dataset_configs` fields:

| Field | Meaning |
| --- | --- |
| `pp_libs` | Python modules from which CLU `preprocess_spec` ops are collected. Empty by default. |
| `train`, `eval`, `test` | Per-mode config blocks. Missing modes produce `None` iterators/metadata. |
| `return_iterators` | If false, return dataset metadata/specs without iterator objects. |
| `return_datasets` | If true, include raw `tf.data.Dataset` objects in the returned `Dataset`. |
| `extra_meta_data` | Extra metadata merged into `Dataset.meta_data`. |
| `padded_batch` | Use padded batching for variable shapes. |

Each mode config contains `sources` and optional mode-level preprocessing:

```python
config.dataset_configs.train = {
  'sources': [{
    'source': 'tfds',
    'tfds_name': 'coco',
    'split': 'train',
    'shuffle_buffer_size': 1000,
    'cache': False,
    'preproc_spec': 'decode_example|resize(224)',
    'postproc_spec': '',
    'skip_decoders': ['image'],
    'repeat_dataset': True,
  }],
  'merge_sources': True,
  'preproc_spec': '',
  'postproc_spec': '',
}
```

Source rules:

- `source='tfds'`: creates a deterministic host split, optionally skips decoders, caches/repeats/shuffles, applies per-example preprocessing, batches, then applies postprocessing.
- `source='grain'`: uses `grain.tensorflow.load_from_tfds`, global shuffling, JAX-process sharding, optional Grain config updates, and optional metadata-field dropping.
- Multiple sources can be merged by weighted `tf.data.Dataset.sample_from_datasets`; if not merged, FlexIO returns a dictionary of source datasets and requires compatible input specs.
- Mixing multiple Grain-backed sources through the simple merged path is not implemented.

FlexIO metadata:

- `meta_data['input_spec']`, `eval_input_spec`, and `test_input_spec` are derived from `tf.data.Dataset.element_spec` with the host dimension removed.
- `num_*_examples` comes from `num_examples` in a source config or from TFDS split metadata.
