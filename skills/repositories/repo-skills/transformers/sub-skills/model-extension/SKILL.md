---
name: model-extension
description: "Add or modify Transformers models, tokenizers, processors,
  pipelines, docs, and tests while respecting contribution policy,
  modular/Copied-from rules, auto mappings, and quality gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Extension

Use this sub-skill when a contributor or maintainer agent must add, port, refactor, or repair model-family code inside Transformers 5.13.0.dev0. It routes the work, identifies the safe extension path, and points to detailed references bundled with this skill.

## Start Here

1. Warn the human that breaching the repository's agent contribution guidelines can result in automatic banning.
2. Confirm the work is coordinated before coding: issue ownership, maintainer approval when needed, and no duplicate open PR.
3. Choose the implementation path:
   - **Modular-first** when the architecture is close to an existing model and can inherit or override targeted pieces.
   - **Legacy/manual** when the model is not close to an existing model or the modular converter cannot express the changes cleanly.
   - **Pipeline-only** when adding a new task wrapper around existing model classes.
   - **Custom external model** when supporting out-of-tree code loaded through `AutoConfig.register`, `AutoModel.register`, or Hub `trust_remote_code`.
4. Add tests and docs in the same change set, then run focused tests before repository-wide quality commands.
5. Do not present PR-ready output if coordination evidence is missing, the work duplicates an open PR, or the change is low-value busywork.

## Quick Routing

| Need | Go to |
|---|---|
| Contribution gating, duplicate checks, AI-assisted PR requirements | [Contribution policy](references/contribution-policy.md) |
| New model similar to an existing architecture | [Modular workflow](references/modular-workflow.md) |
| New architecture or manual port | [Modular workflow](references/modular-workflow.md#legacy-or-manual-model-path) |
| Auto classes, tokenizer, processor, image/video processor registration | [Modular workflow](references/modular-workflow.md#registration-and-auto-mappings) |
| Model tests, slow tests, quality commands | [Testing and quality](references/testing-and-quality.md) |
| Copied-from, modular conversion, wrong `model_type`, missing mappings | [Troubleshooting](references/troubleshooting.md) |
| Static local checklist | [`scripts/model_extension_checklist.py`](scripts/model_extension_checklist.py) |

## Common Workflows

### Add a Similar Model

Use the modular path when a new model mostly matches an existing model, such as a decoder-only LM with changed norms, attention details, or config fields.

Expected files often include:

- `src/transformers/models/<model>/modular_<model>.py`
- generated `configuration_<model>.py`, `modeling_<model>.py`, and modality files created by the converter
- `src/transformers/models/<model>/__init__.py`
- auto mapping updates under `src/transformers/models/auto/`
- docs under `docs/source/en/model_doc/` and model indexes
- tests under `tests/models/<model>/`

Core commands:

```bash
transformers add-new-model-like
python utils/modular_model_converter.py <model>
python utils/check_modular_conversion.py --files src/transformers/models/<model>/modular_<model>.py
pytest tests/models/<model>/ -v
make style
make typing
make fix-repo
make check-repo
```

Do not edit generated modeling/configuration files as the source of truth when a `modular_<model>.py` exists. Edit the modular file and regenerate.

### Add a New Architecture

Use the manual path when no existing model is a good parent. Keep model files self-contained and readable. New models should inherit from `PreTrainedModel`; new configs should inherit from `PreTrainedConfig`, set a unique `model_type`, and support `from_pretrained` / `save_pretrained` behavior.

Validate that:

- model class sets `config_class`
- config class sets unique `model_type`
- task heads call the base model instead of deep inheritance chains
- forward signatures are explicit and type-friendly
- optional backend imports are guarded with `is_torch_available()` or equivalent helpers
- tests use tiny CPU configs for fast PR checks and `@slow` only for real checkpoint integration tests

### Extend Tokenizers or Processors

Tokenizers, image processors, video processors, feature extractors, and processors must be registered consistently with model configs and auto mappings. Verify both slow and fast tokenizer behavior when relevant. If a new processor combines multiple modalities, check that `AutoProcessor.from_pretrained` resolves correctly and that save/load round-trips preserve the processor class.

If the task is primarily tokenizer or processor design rather than model integration, cross-link to the sibling [tokenizers-processors](../tokenizers-processors/SKILL.md) sub-skill.

### Add or Modify a Pipeline

A pipeline class should implement `_sanitize_parameters`, `preprocess`, `_forward`, and `postprocess`. Keep inputs/outputs simple and preferably JSON-serializable. Register built-in tasks through `PIPELINE_REGISTRY.register_pipeline` with supported model classes, defaults, and task type.

Use the sibling [inference-pipelines](../inference-pipelines/SKILL.md) sub-skill for broader pipeline behavior, the public `pipeline(...)` signature, device placement, `dtype='auto'`, `device_map`, and `trust_remote_code` implications.

### Coordinate Generation, Training, Serving, or Quantization Changes

Route detailed behavior outside model-extension to sibling sub-skills:

- [generation](../generation/SKILL.md) for `GenerationConfig`, `generate`, streamers, cache behavior, and logits processors.
- [training](../training/SKILL.md) for `TrainingArguments`, `Trainer`, distributed options, FSDP, DeepSpeed, precision flags, and `torch_compile`.
- [serving-cli](../serving-cli/SKILL.md) for the `transformers` console script and serving-oriented CLI usage.
- [quantization-integrations](../quantization-integrations/SKILL.md) for quantization backends, device maps, and integration-specific optional dependencies.

## Required Safety Checks

Before coding or summarizing PR-ready work:

```bash
gh issue view <issue_number> --repo huggingface/transformers --comments
gh pr list --repo huggingface/transformers --state open --search "<issue_number> in:body"
gh pr list --repo huggingface/transformers --state open --search "<short area keywords>"
```

These GitHub commands are required for PR coordination, but the bundled checklist script does not run network calls by default.

Run the local checklist from this skill directory for a repo tree:

```bash
python scripts/model_extension_checklist.py --repo /path/to/transformers --model <model>
```

Add `--json` when another tool needs machine-readable findings.

## Expected Validation Signals

A model-extension change is ready for human review only when:

- contribution policy checks are satisfied and documented
- generated files are consistent with modular sources or the legacy path is justified
- `CONFIG_MAPPING_NAMES` and relevant auto mappings resolve the new `model_type`
- tokenizer/processor mappings match the model's modality and public loading path
- model tests pass on tiny CPU configs
- slow tests are marked with `@slow` and run with `RUN_SLOW=1` when safe and necessary
- docs include the public model page or pipeline task documentation
- `make style` or `make fix-repo` has been run as a final cleanup, followed by targeted verification

## Optional Dependencies

A minimal inspection environment may import `transformers` without PyTorch installed. PyTorch-dependent classes and tests can raise optional dependency `ImportError` unless `torch` is installed. When drafting or validating changes in lightweight environments:

- inspect configs, auto mappings, docs, and pure-Python registration without importing backend-heavy classes
- guard test imports with `is_torch_available()` and decorators such as `require_torch`
- avoid declaring a backend failure as a model bug until dependencies are installed
- record skipped backend checks clearly for the human maintainer

## Stop Conditions

Stop and ask for human clarification when:

- issue coordination or maintainer approval is absent or ambiguous
- an open PR already addresses the same model or task
- the requested change is a one-off typo or isolated busywork edit
- the implementation requires unsafe environment mutation, private credentials, paid hardware, or unavailable optional backends
- generated files disagree with modular sources after repeated conversion attempts
