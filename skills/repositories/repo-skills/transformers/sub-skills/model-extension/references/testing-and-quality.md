# Testing and Quality for Model Extension

Transformers model changes need focused tests first, then repository quality commands.

## Focused Test Commands

Run the smallest relevant tests while iterating:

```bash
pytest tests/models/<model>/test_modeling_<model>.py -v
pytest tests/models/<model>/test_modeling_<model>.py::<ModelTest>::test_model -v
pytest tests/models/<model>/ -k integration -v
pytest tests/models/auto/test_configuration_auto.py -v
pytest tests/models/auto/test_tokenization_auto.py -v
pytest tests/models/auto/test_processor_auto.py -v
pytest tests/models/auto/test_image_processing_auto.py -v
pytest tests/models/auto/test_video_processing_auto.py -v
```

Pick only the auto tests matching the files changed. For example, a model-only mapping change may need configuration and modeling auto tests, while a processor change needs processor and image/video tests.

## Slow Tests

Use slow tests for real checkpoints, network downloads, large datasets, or tests that take more than a few seconds. Mark them with `@slow` and run them explicitly:

```bash
RUN_SLOW=1 pytest tests/models/<model>/ -v
```

On Windows shells, set the environment variable with shell-specific syntax before running pytest.

Expected signal: fast PR tests pass without `RUN_SLOW=1`; slow integration tests are skipped by default and pass when explicitly enabled in a safe environment.

## Model Test Structure

Most model tests use a tester class plus a unittest class with mixins.

Common base choices:

| Base | Use for | Coverage |
|---|---|---|
| `CausalLMModelTest` | decoder-only causal language models | modeling, generation, pipelines, training, tensor parallel |
| `VLMModelTest` | vision-language models | modeling, generation, pipelines, multimodal inputs |
| `ALMModelTest` | audio-language models | modeling, generation, pipelines, audio placeholders |
| custom `ModelTesterMixin` composition | encoder-only, encoder-decoder, nonstandard architectures | selected mixins |

The tester should create tiny CPU-friendly configs and inputs. Keep dimensions small enough for fast PR checks.

Useful helpers commonly used in model tests:

- `ids_tensor(shape, vocab_size)` for token IDs and labels
- `random_attention_mask(shape)` for binary attention masks
- `floats_tensor(shape, scale=1.0)` for continuous tensors such as pixel values or input embeddings
- `ConfigTester` for config save/load behavior

## Registration Tests

After adding or modifying a model, verify public loaders:

```python
from transformers import AutoConfig, AutoTokenizer, AutoProcessor

config = AutoConfig.from_pretrained("<local-or-test-model>")
tokenizer = AutoTokenizer.from_pretrained("<local-or-test-model>")
processor = AutoProcessor.from_pretrained("<local-or-test-model>")
```

Use local temporary fixtures or tiny test repositories when possible. Avoid requiring network access in fast tests.

Check these expected signals:

- `config.model_type` is the intended unique key
- `AutoConfig` returns the new config class
- tokenizer fast/slow selection is expected under `use_fast=True` and `use_fast=False`
- `AutoProcessor`, `AutoImageProcessor`, `AutoVideoProcessor`, or `AutoFeatureExtractor` returns the intended class
- save/load round trips preserve classes and key attributes

## Pipeline Tests

For pipeline additions or compatibility changes:

- add tests under the pipeline test suite
- keep outputs structurally asserted rather than numerically brittle for random tiny models
- use `ANY`-style assertions when random model values are not meaningful
- verify task registration in the pipeline registry
- confirm the public `pipeline(...)` call routes model, tokenizer, processor, `device`, `device_map`, and `dtype` correctly when relevant

Use the sibling [inference-pipelines](../../inference-pipelines/SKILL.md) sub-skill for broader pipeline usage guidance.

## Quality Commands

Repository guidance names these commands:

```bash
make style
make typing
make fix-repo
make check-repo
```

Meanings:

- `make style` runs formatters and linters, including Ruff.
- `make typing` runs the type checker and model structure rules.
- `make fix-repo` auto-fixes copied blocks, modular conversions, doc TOCs, docstrings, and style fixes.
- `make check-repo` runs typing and consistency checks.

Run `make style` or `make fix-repo` as the final cleanup before PR review. If `make fix-repo` changes generated files, inspect the diff and re-run focused tests.

## Utility Checks

Useful utilities for model-extension work:

```bash
python utils/check_auto.py
python utils/check_auto.py --fix_and_overwrite
python utils/check_modular_conversion.py --files src/transformers/models/<model>/modular_<model>.py
python utils/check_modeling_structure.py
python utils/sort_auto_mappings.py
python utils/create_dummy_models.py output_dir -m <model_type>
```

Use `create_dummy_models.py` when dummy artifacts are needed for tests, but do not make public skill instructions depend on private local artifact paths.

## Optional Dependency Boundaries

A lightweight environment may import `transformers` while backend-dependent classes fail because PyTorch or other optional packages are absent. Treat this as expected unless the task specifically promises that backend.

Safe patterns:

- guard imports with `is_torch_available()` or modality-specific availability helpers
- decorate tests with `require_torch` or other `require_*` decorators
- place backend imports inside availability blocks
- skip or xfail tests only with a precise reason
- document that PyTorch-dependent model classes require `torch`

Do not diagnose optional dependency `ImportError` as a mapping failure until the relevant dependency is installed.

## Final Review Checklist

Before handing the change to a human reviewer, confirm:

- contribution policy and duplicate-work checks are satisfied
- modular or legacy path is justified
- copied-from blocks were not edited directly by accident
- generated files match modular sources after conversion
- auto mappings include every intended config/model/tokenizer/processor path
- tests cover base model, task heads, generation, pipeline, tokenizer, processor, and docs as applicable
- slow tests are marked and documented
- `make style` or `make fix-repo` ran at the end
- remaining skipped checks are explained with dependency or environment reasons
