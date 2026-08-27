# Preprocessing, runs, and save/load support

This reference covers Optimum support surfaces around task preprocessing, run/benchmark config validation, and base classes used by optimized model and quantizer implementations. These APIs are utility scaffolding; they are not the backend exporter, FX transform, or GPTQ workflow themselves.

## TaskProcessorsManager

`TaskProcessorsManager` exposes two selectors:

```python
from optimum.utils.preprocessing import TaskProcessorsManager

processor_cls = TaskProcessorsManager.get_task_processor_class_for_task("text-classification")
processor = TaskProcessorsManager.for_task("text-classification", config, tokenizer, preprocessor_kwargs={})
```

Supported tasks in the base manager:

| Task | Processor | Required preprocessor class | Default dataset/data keys |
| --- | --- | --- | --- |
| `text-classification` | `TextClassificationProcessing` | `PreTrainedTokenizerBase` | `glue`/`sst2`, `{"primary": "sentence"}`, ref `label` |
| `token-classification` | `TokenClassificationProcessing` | `PreTrainedTokenizerBase` | `conll2003`, `{"primary": "tokens"}`, refs `ner_tags`, `pos_tags`, `chunk_tags` |
| `question-answering` | `QuestionAnsweringProcessing` | `PreTrainedTokenizerBase` | `squad_v2`, `{"question": "question", "context": "context"}`, ref `answers` |
| `image-classification` | `ImageClassificationProcessing` | `BaseImageProcessor` | `uoft-cs/cifar10`, `{"image": "img"}`, label-like refs |

Constructor validation rejects the wrong preprocessor type with a `ValueError` beginning with `Preprocessor is incorrect`. The processors split provided `preprocessor_kwargs` into defaults and remaining kwargs without mutating the caller's dictionary.

## Dataset loading and processing

Each processor implements:

- `dataset_processing_func(example, data_keys, ref_keys=None)` for one example.
- `create_dataset_processing_func(data_keys, ref_keys=None)` for `datasets.Dataset.map`.
- `prepare_dataset(dataset, data_keys, ref_keys=None, split=None)` for an already loaded `Dataset` or `DatasetDict`.
- `load_dataset(path, data_keys=None, ref_keys=None, only_keep_necessary_columns=False, load_smallest_split=False, num_samples=None, shuffle=False, download_config=None, **load_dataset_kwargs)`.
- `load_default_dataset(...)` using the task's default dataset metadata.

Important caveats:

- `prepare_dataset`, `load_dataset`, and `load_default_dataset` require the optional `datasets` package.
- Default datasets are remote dataset identifiers. `load_default_dataset` can download unless the dataset is already cached or a local dataset path is passed to `load_dataset`.
- If `data_keys` is omitted, processors try to guess input columns from column names; ambiguous datasets should pass `data_keys` explicitly.
- If `ref_keys` is omitted, processors try to guess reference/label columns.
- `only_keep_necessary_columns=True` removes columns outside the preprocessor's `model_input_names` and reference keys.
- `load_smallest_split=True`, `num_samples=...`, and `shuffle=True` bound dataset work, but they do not make remote datasets safe if downloads are unavailable.
- Token-classification default data may require remote-code trust in some dataset versions; use explicit local/cached data when operating in a no-network context.

## Optional preprocessing imports

The public preprocessing package imports the image processor module, which imports `torchvision` transforms and normally also depends on Pillow for image workflows. As a result, importing `TaskProcessorsManager` can fail on `torchvision`/Pillow even if the immediate task is text-only.

When that happens:

1. Decide whether task preprocessing is actually needed. If you only need dummy inputs or normalized configs, import those modules directly instead of preprocessing.
2. Use `optimum.utils.import_utils` availability helpers such as `is_datasets_available`, `is_diffusers_available`, `is_timm_available`, and `is_sentence_transformers_available` to report missing optional packages without importing the heavy surface.
3. If Optimum's processor classes are required, install the missing optional packages in the task environment or ask for a smaller task that uses Transformers tokenizers/processors directly.

There is no guaranteed public text-only `TaskProcessorsManager` import path in this version because the preprocessing package initialization loads all processor classes.

## Run and benchmark config concepts

`optimum.utils.runs` defines dataclasses/enums used by run configurations:

- `RunConfig`: validates a run specification.
- `Run`: a dataclass base for validated run fields.
- `DatasetArgs`: dataset path/name, evaluation split, data keys, reference keys, and optional calibration split.
- `FrameworkArgs`: ONNX opset and optimization level validation.
- `TaskArgs`: task-specific fields such as `is_regression` for text classification.
- `BenchmarkTimeArgs`: benchmark duration and warmup runs.
- `Calibration`: static quantization calibration settings.
- Enums: `Frameworks.onnxruntime`, `QuantizationApproach.static/dynamic`, and calibration methods `minmax`, `percentile`, `entropy`.

Validation constraints to remember:

- Supported tasks for run config validation are `text-classification`, `token-classification`, `question-answering`, and `image-classification`.
- Text classification requires `task_args.is_regression` to be explicitly set.
- Static quantization requires `dataset.calibration_split` and `calibration` settings.
- Quantization-aware training is not supported (`aware_training` must remain false).
- `FrameworkArgs.opset` must be at most 15, and `optimization_level` must be one of `0`, `1`, `2`, or `99`.

`optimum.runs_base.Run` is an executable base class for comparing a Transformers baseline and an optimized model. It builds an Optuna grid over batch sizes and input lengths, records hardware/version metadata, loads task datasets through a task processor, and delegates timing/evaluation/finalization to backend subclasses. Do not call `Run.launch()` unless the backend subclass, datasets, model files, runtime budget, and download/cache policy are explicit.

`TimeBenchmark` creates simple dummy inputs for `input_ids`, `attention_mask`, `token_type_ids`, and `pixel_values`, runs warmups, tracks latency, and computes throughput/latency quantiles. It raises `NotImplementedError` if the model requires unsupported input names.

## BaseConfig

`BaseConfig` extends Transformers `PretrainedConfig` for Optimum configs with custom configuration file names.

Key behavior:

- Subclasses set `CONFIG_NAME` and `FULL_CONFIGURATION_FILE`; default is `config.json`.
- `save_pretrained(save_directory, push_to_hub=False, **kwargs)` requires a directory path, creates it if needed, and writes `CONFIG_NAME`.
- `to_dict()` adds `transformers_version` and `optimum_version` and removes internal auto/commit fields.
- `get_config_dict(pretrained_model_name_or_path, **kwargs)` loads local or Hub config dictionaries and honors versioned `configuration_files` by selecting the highest file version not newer than the installed Optimum version.
- `from_dict(..., return_unused_kwargs=True)` follows Transformers config semantics while preserving extra unused kwargs when requested.

Use local temp directories for smoke tests. Hub pushes require credentials and should be performed only when the user explicitly requests publication.

## OptimizedModel

`OptimizedModel` is a base wrapper for backend-specific optimized model classes.

Key methods and expectations:

- Constructor stores `model`, `config`, and optional `preprocessors`.
- `__call__` delegates to `forward`; subclasses must implement `forward`.
- `save_pretrained(save_directory, push_to_hub=False, **kwargs)` writes the config, each preprocessor, then calls subclass `_save_pretrained(save_directory)`.
- `from_pretrained(model_id, config=None, export=False, subfolder="", revision="main", local_files_only=False, trust_remote_code=False, cache_dir=..., token=None, **kwargs)` resolves config files, infers library routing, and delegates to subclass `_from_pretrained` or `_export`.
- If `export=True`, the subclass must implement `_export` or a legacy `_from_transformers` method.

This base class can call Hub/file discovery utilities. Use `local_files_only=True` and local directories when no downloads are allowed.

## OptimumQuantizer

`OptimumQuantizer` is an abstract base with two required surfaces:

- `from_pretrained(model_or_path, file_name=None)` loads a model/artifact for quantization in a subclass.
- `quantize(save_dir, file_prefix=None, **kwargs)` writes quantized output in a subclass.

The base class does not define a complete quantization workflow. Route GPTQ-specific configuration, save/load, and kernel troubleshooting to [`../../gptq-quantization/SKILL.md`](../../gptq-quantization/SKILL.md). Route ONNX Runtime/OpenVINO partner quantization to [`../../exporters-and-cli/SKILL.md`](../../exporters-and-cli/SKILL.md).
