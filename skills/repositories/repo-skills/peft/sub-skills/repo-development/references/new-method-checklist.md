# New PEFT Method Checklist

Use this checklist when adding a new parameter-efficient fine-tuning method to PEFT. Do not start implementation for an upstream PR until maintainer coordination is clear.

## Approval and Scope

- Warn the contributor that breaching PEFT's AI-agent contribution guidelines can result in automatic banning.
- Confirm the human contributor can explain and defend the whole implementation.
- Open or link a proposal issue before investing substantial work.
- If the contributor is not an author of the original method, check for existing implementations and whether original authors plan to contribute.
- Link a stable primary reference such as a final paper; avoid unstable under-review-only methods unless maintainers agree.
- Check for overlapping open PRs and issue ownership.

## Core Registration Steps

A typical tuner method needs these source updates:

1. Add a `PeftType` enum entry in `src/peft/utils/peft_types.py`.
2. Create a package under `src/peft/tuners/<method>/`.
3. Add method files as needed, commonly `config.py`, `model.py`, `layer.py`, and `__init__.py`.
4. In the method package `__init__.py`, call `register_peft_method(...)` with a lowercase unique method name.
5. Export public config/model classes from `src/peft/tuners/__init__.py`.
6. Export public config/model classes from `src/peft/__init__.py`.
7. If the method has default target modules for Transformers models, add the mapping in PEFT utilities/constants used by tuner models and export it consistently.
8. If save/load requires special state-dict handling, update PEFT save/load utilities and cover the behavior with tests.
9. If mixed-adapter support is valid, pass `is_mixed_compatible=True`; otherwise leave it false.

`register_peft_method` validates that the method name is lowercase, the uppercase name exists in `PeftType`, the method is unique, and the prefix is not already registered. Use an explicit `prefix` only when the model layer prefix must differ from the default `<method>_`.

## Config and Model Expectations

- Config classes generally inherit from `PeftConfig` and set `self.peft_type` in post-init logic.
- Config argument names should be understandable without reading the paper.
- Validate relationships between arguments where needed, but avoid unnecessary defensive checks for unsupported input types.
- Model classes should follow existing tuner conventions for adapter names, prefixes, target module replacement, merging/unmerging, enabling/disabling adapters, and trainable parameter handling.
- Layer implementations should follow nearby tuner style for supported layer types, device/dtype behavior, and quantization hooks.

## Tests

Start with the broad custom-model matrix because it is usually the fastest way to exercise a new tuner across simple module types:

```bash
pytest tests/test_custom_models.py -k <method-name> -v
```

Add the method to the appropriate `tests/test_custom_models.py` matrix entries and extend broader suites as relevant:

- `tests/test_config.py` for config serialization/loading behavior.
- `tests/test_decoder_models.py` and encoder/seq-classifier tests for Transformers model integration.
- `tests/test_mapping.py` for mapping and registration behavior.
- `tests/test_quantization.py` for quantization support.
- `tests/test_common_gpu.py` or `tests/test_gpu_examples.py` for GPU-only behavior.
- Regression tests with `--regression` for save/load-sensitive behavior.

Ensure the selector runs at least one test. If a focused selector deselects everything, revise it or add missing tests.

## Documentation, Examples, and Benchmarks

For a complete new method PR:

- Add `docs/source/package_reference/<method>.md` with an explanation, paper link, usage snippet, autodoc blocks, and comparison notes.
- Register the docs page in the docs toctree.
- Add or adapt a runnable example under `examples/` when the method needs discoverability beyond API docs.
- Consider benchmark configuration in `method_comparison/` for sanity checking and comparison.
- Explain method tradeoffs in the PR description.

## Review Readiness

Before asking for review:

- Run focused tests for the method.
- Run broader tests affected by save/load, quantization, model architecture, or task changes.
- Run `make style`; undo unrelated formatter churn.
- Confirm imports from both `peft` and `peft.tuners` work.
- Confirm public docs build assumptions are satisfied.
- Verify the PR description includes AI assistance disclosure, coordination link, and test results.
