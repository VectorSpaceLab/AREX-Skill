# Modular and Legacy Model Workflow

Use this reference to choose between modular, legacy/manual, pipeline, and custom-model paths when extending Transformers.

## Decide Modular vs Legacy

Prefer the modular path when:

- the new model is architecturally close to an existing model
- differences are localized to config fields, norms, attention, MLPs, task heads, or processor variants
- inheritance from existing classes keeps the source concise and readable
- generated standalone files can be produced deterministically by the modular converter

Prefer the legacy/manual path when:

- no existing model is a good parent
- inheritance would be awkward or misleading
- the modular converter cannot express the needed structure
- handwritten standalone files are clearer for maintainers

Do not modify an existing parent model just to make inheritance convenient for a new model. If the parent shape is wrong, copy or write the relevant code explicitly.

## Modular Path

Create a modular source file at:

```text
src/transformers/models/<model>/modular_<model>.py
```

The `<model>` directory and filename should use the snake_case model name. The config `model_type` is the serialized public key used by `AutoConfig.from_pretrained`; it is often the same as the directory name but must be checked explicitly.

Typical modular tasks:

- import the closest parent model classes
- subclass unchanged classes with `pass`
- override only behavior that differs
- define config changes as class-level annotations when possible
- add `@auto_docstring` and `@strict` to config classes when following current modular patterns
- use `__post_init__` for derived config fields or backward compatibility logic
- define `base_model_tp_plan` and `base_model_pp_plan` when tensor or pipeline parallel support is needed
- include module-level `logger` and `__all__`

Generate standalone files:

```bash
python utils/modular_model_converter.py <model>
python utils/check_modular_conversion.py --files src/transformers/models/<model>/modular_<model>.py
```

Expected signal: the generated `modeling_<model>.py`, `configuration_<model>.py`, or processor files match converter output after formatting. If they drift, edit the modular file or converter inputs, not the generated file.

## Generated Files Not To Edit

When `src/transformers/models/<model>/modular_<model>.py` exists, generated files can be overwritten by `make fix-repo` or modular conversion. Treat these as generated outputs unless the maintainer explicitly directs otherwise:

- `modeling_<model>.py`
- generated `configuration_<model>.py` sections
- generated image/video/processing files derived from modular sources
- generated copied classes pulled from parent dependencies

It is acceptable to inspect generated files for debugging converter output, but make durable source changes in `modular_<model>.py` or in the true copied-from source.

## Legacy or Manual Model Path

For a new architecture, write self-contained files under `src/transformers/models/<model>/`.

Core conventions:

- configs inherit from `PreTrainedConfig`
- models inherit from `PreTrainedModel`
- config classes set unique `model_type`
- model classes set `config_class`
- task heads call the base model in `forward` instead of relying on deep inheritance
- model files stay readable and explicit, with no unnecessary abstraction layers
- public forward signatures use descriptive argument names and support expected Transformers conventions
- optional backend imports are guarded

Common files:

```text
configuration_<model>.py
modeling_<model>.py
tokenization_<model>.py
tokenization_<model>_fast.py
image_processing_<model>.py
video_processing_<model>.py
processing_<model>.py
feature_extraction_<model>.py
__init__.py
```

Only create modality files that the model actually needs.

## `transformers add-new-model-like`

The installed console script is:

```text
transformers -> transformers.cli.transformers:main
```

For similar-model scaffolding, use:

```bash
transformers add-new-model-like
```

The command asks for an existing model type and the new model name, then creates a modular file, auto mapping changes, tests, docs, and generated files. It relies on existing `CONFIG_MAPPING_NAMES` and related auto mappings to discover the source model.

Use the scaffold as a starting point, not a finished port. Review every generated file, then adapt config, model internals, tokenizers/processors, docs, and tests.

## Registration and Auto Mappings

Public loading depends on consistent registration.

### Config

`AutoConfig.from_pretrained(pretrained_model_name_or_path, **kwargs)` resolves from serialized config fields. Ensure:

- config class has unique `model_type`
- `CONFIG_MAPPING_NAMES` includes the new `model_type` and config class
- `utils/check_auto.py` agrees with generated mappings

Repair command when mappings are stale:

```bash
python utils/check_auto.py --fix_and_overwrite
```

`make fix-repo` can also repair auto mappings as part of repository consistency fixes.

### Model Classes

For built-in model classes, update the relevant auto modeling mapping for each task head, such as base model, causal LM, sequence classification, image classification, conditional generation, or multimodal generation.

For custom out-of-tree code, the public registration pattern is:

```python
AutoConfig.register("resnet", ResnetConfig)
AutoModel.register(ResnetConfig, ResnetModel)
AutoModelForImageClassification.register(ResnetConfig, ResnetModelForImageClassification)
```

The first `AutoConfig.register` argument must match `config.model_type`. The first model registration argument must be the config class.

### Tokenizers and Processors

Check all relevant mappings:

- tokenizer mapping for slow and fast tokenizers
- image processor mapping, including PIL/NumPy or torchvision variants when present
- video processor mapping
- feature extractor mapping
- processor mapping for multimodal wrappers

`AutoTokenizer.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)` may choose a fast tokenizer by default when available. Validate both `use_fast=True` and `use_fast=False` paths when both classes exist.

Registration gaps usually appear as `AutoTokenizer`, `AutoProcessor`, or `AutoImageProcessor` loading the wrong class or failing despite the config being recognized.

## Pipeline Integration

A built-in pipeline class should implement:

- `_sanitize_parameters`
- `preprocess`
- `_forward`
- `postprocess`

Register the task with `PIPELINE_REGISTRY.register_pipeline`, including the pipeline class, supported backend model class such as a relevant `AutoModelFor...`, default model information when appropriate, and task type.

The public `pipeline(...)` API includes `task`, `model`, `config`, `tokenizer`, `feature_extractor`, `image_processor`, `video_processor`, `processor`, `revision`, `use_fast`, `token`, `device`, `device_map`, `dtype='auto'`, `trust_remote_code`, `model_kwargs`, `pipeline_class`, and `**kwargs`. When a model extension changes pipeline compatibility, check that these arguments still route to the right components.

## Copied-From Rules

`# Copied from ...` blocks are synchronized by repository tooling. Do not directly edit a copied block unless intentionally breaking the copied-from link. Prefer editing the original source block and running:

```bash
make fix-repo
```

If the generated copy should diverge, remove or adjust the copied-from marker intentionally and explain why in the change summary.

## Documentation Touchpoints

A model extension usually needs docs:

- model doc page under `docs/source/en/model_doc/`
- docs index or table of contents updates when required
- examples or snippets showing `AutoConfig`, `AutoTokenizer`, `AutoProcessor`, `pipeline`, or task heads
- notes for optional dependencies and backend support

Documentation should describe public APIs, not private conversion scratch files.
