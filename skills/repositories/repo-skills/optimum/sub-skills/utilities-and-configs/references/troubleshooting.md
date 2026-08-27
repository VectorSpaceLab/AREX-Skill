# Utilities and configs troubleshooting

Use this checklist when Optimum support utilities fail before a backend-specific workflow begins.

## `ImportError` importing preprocessing or task processors

Symptoms:

- Importing `TaskProcessorsManager` or `optimum.utils.preprocessing` fails before you instantiate a processor.
- Error mentions `torchvision`, Pillow/PIL, image transforms, or image processing.

Cause and response:

- In this Optimum version, the preprocessing package imports the image-classification processor at package import time. That module imports `torchvision.transforms`; image workflows also depend on Pillow.
- If you only need normalized configs or dummy inputs, avoid preprocessing imports entirely and import `optimum.utils.normalized_config` or `optimum.utils.input_generators` directly.
- If you need availability checks, use lightweight helpers from `optimum.utils.import_utils` such as `is_datasets_available`, `is_diffusers_available`, `is_timm_available`, and `is_sentence_transformers_available`.
- If you need Optimum task processors, install the missing optional packages in the active environment or ask for a text-only preprocessing path implemented with Transformers directly.

## Missing `datasets`

Symptoms:

- `prepare_dataset`, `load_dataset`, or `load_default_dataset` raises an `ImportError` requiring `datasets`.
- Dataset loading attempts a network request or fails in offline mode.

Response:

- Install `datasets` only if dataset preprocessing is in scope.
- Prefer an already available local dataset path and explicit `data_keys`/`ref_keys`.
- Avoid `load_default_dataset` in no-network runs because default datasets are remote identifiers.
- Bound work with `load_smallest_split=True`, `num_samples=...`, and `only_keep_necessary_columns=True`, but remember these options do not prevent an initial download.
- Some dataset versions can require remote-code trust; do not enable trust without explicit user approval.

## Missing `diffusers`, `timm`, or `sentence_transformers`

Symptoms:

- An exporter, pipeline, or task/library inference path fails while probing model libraries.
- Availability helpers report these packages as absent.

Response:

- For utility-only tasks, do not install these packages just to generate normalized configs or dummy inputs.
- For backend exporter registration, model library detection, or accelerated pipelines, route to [`../../exporters-and-cli/SKILL.md`](../../exporters-and-cli/SKILL.md).
- If a user asks for Diffusers/TIMM/Sentence-Transformers model support, make the optional dependency and model cache/download budget explicit before running backend workflows.

## Invalid task names

Surfaces:

- `TaskProcessorsManager.get_task_processor_class_for_task(task)` supports only `text-classification`, `token-classification`, `question-answering`, and `image-classification`; unsupported values raise `KeyError` with the supported list.
- `RunConfig` uses the same limited run-config task set.
- Accelerated pipeline invalid task or accelerator errors belong to the exporter/pipeline routing surface, not this sub-skill.

Response:

- Normalize common task aliases before calling the API.
- If the task is a pipeline/export task outside the four preprocessing processors, route to the exporter/pipeline sub-skill.
- If the task is truly new, do not patch `TaskProcessorsManager` in place; implement a local processor or extend the skill after verifying source support.

## Dummy input dtype mismatches

Symptoms:

- Assertions fail because `torch.int64` is not equal to `numpy.int64`.
- NumPy generation fails for `bf16`.
- Unknown dtype string raises a mapping error.

Response:

- Compare dtype through framework-specific expectations: `DTYPE_MAPPER.pt(...)` for PyTorch and `DTYPE_MAPPER.np(...)` for NumPy.
- Use `float_dtype="fp32"` or `"fp16"` for NumPy. `bf16` is supported only on the PyTorch mapping.
- Use `int_dtype="int64"`, `"int32"`, or `"int8"` unless the downstream API explicitly supports another type.
- Re-run the local smoke script with the desired framework: `python scripts/utils_smoke.py --framework pt` or `--framework np`.

## Dummy input shape mismatches

Common causes:

- Vision generator constructor dimensions are overridden by `normalized_config.image_size`, `input_size`, or `num_channels`.
- `task="multiple-choice"` changes text shapes from `(batch, sequence)` to `(batch, num_choices, sequence)`.
- Cache generators require `hidden_size // num_attention_heads` to be an integer and may need family-specific cache layouts.
- `DummyLabelsGenerator` needs `num_labels` for classification; otherwise integer generation can be invalid.

Response:

- Print the normalized config fields before generating.
- Use `supports_input(input_name)` to choose the generator.
- For nonstandard config names, fix the normalized wrapper with `with_args` rather than changing generator internals.
- For architecture-specific key/value caches, select the specialized PKV generator instead of the generic one.

## Config serialization file choices

Symptoms:

- `save_pretrained` refuses a path.
- `from_pretrained` cannot find the config file.
- Loading picks an unexpected versioned JSON file.

Response:

- `BaseConfig.save_pretrained(save_directory)` requires a directory path, not a file path.
- Subclasses control file names through `CONFIG_NAME` and `FULL_CONFIGURATION_FILE`. Confirm the saved directory contains the subclass `CONFIG_NAME`.
- If a config dictionary contains `configuration_files`, `BaseConfig.get_configuration_file(...)` selects the highest versioned config file not newer than the installed Optimum version.
- Invalid JSON raises an environment-style load error; validate JSON before retrying.

## BaseConfig local vs Hub path errors

Symptoms:

- Error says it cannot load configuration for a path or model id.
- A local directory has the same name as a Hub model id.
- A config is stored in a subfolder and top-level fallback is surprising.

Response:

- For local loading, pass a directory containing the expected config file or pass explicit subclass config paths when supported.
- Use `subfolder=...` only when the config file is actually inside that subfolder.
- In no-network environments, pass `local_files_only=True` through higher-level loading APIs and make sure the files are already present.
- `trust_remote_code=True` has no useful effect on `BaseConfig` itself; remote custom code decisions belong to Transformers/Auto classes and must be explicitly approved.
- Avoid `push_to_hub=True` unless the user requested publication and provided credentials/token policy.

## Run/benchmark surprises

Symptoms:

- `RunConfig` validation fails for text classification, static quantization, opset, optimization level, or aware training.
- `TimeBenchmark` raises `NotImplementedError` for an input name.

Response:

- Set `task_args={"is_regression": ...}` for text-classification run configs.
- For static quantization, include both `dataset.calibration_split` and a `calibration` config.
- Keep `aware_training=False`.
- Keep ONNX `opset <= 15` and `optimization_level` in `0`, `1`, `2`, or `99`.
- `TimeBenchmark` only knows `input_ids`, `attention_mask`, `token_type_ids`, and `pixel_values`; use a task-specific dummy input generator for anything else.
