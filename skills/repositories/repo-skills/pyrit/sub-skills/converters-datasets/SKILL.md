---
name: converters-datasets
description: "Use PyRIT converters, converter stacks, message normalization, and
  seed datasets safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyRIT converters and datasets

Use this sub-skill when an agent needs to transform prompt/message values, compose converter stacks, normalize PyRIT messages for targets, or create/load seed datasets for PyRIT `1.1.0.dev0`.

## Start here

1. For direct offline transformation, choose a converter and call `convert_async()` or `convert_tokens_async()` using the contracts in [references/converters-and-datasets.md](references/converters-and-datasets.md).
2. For stacks passed into attacks, build `ConverterConfiguration` objects here, then route attack execution to [../attacks-scenarios/SKILL.md](../attacks-scenarios/SKILL.md).
3. For target sends, target capability checks, and scorer configuration, route to [../targets-scorers/SKILL.md](../targets-scorers/SKILL.md). This sub-skill only prepares messages, converters, and datasets.
4. For session initialization, memory setup, registry/default configuration, and persistent seed storage, route to [../setup-memory-core/SKILL.md](../setup-memory-core/SKILL.md).
5. For CLI dataset listing or backend scanner commands, route to [../cli-backend-scanner/SKILL.md](../cli-backend-scanner/SKILL.md).

## Runtime references and helper

- [Converter and dataset workflows](references/converters-and-datasets.md) covers converter modalities, offline versus service-backed converters, converter stacks, message normalizers, and dataset provider APIs.
- [Data formats and YAML schemas](references/data-formats.md) covers `PromptDataType`, `Message`/`MessagePiece`, `SeedPrompt`, `SeedDataset`, seed YAML shapes, template parameters, and bundled response JSON schemas.
- [Troubleshooting](references/troubleshooting.md) covers modality mismatches, optional media dependencies, LLM-backed converter target requirements, regex errors, YAML validation, remote dataset/cache failures, and missing template parameters.
- [scripts/converter_dataset_smoke.py](scripts/converter_dataset_smoke.py) is a no-secret/no-network smoke helper that imports installed PyRIT, inspects core signatures, exercises `Base64Converter`, `SearchReplaceConverter`, `SeedPrompt`, and a tiny local `SeedDataset`, and prints a JSON summary.

## Safety and boundary reminders

- Prefer offline converters for smoke tests and deterministic debugging. `Base64Converter` and `SearchReplaceConverter` are safe offline examples.
- LLM-backed converters call a `converter_target` and therefore may use credentials, rate limits, network, and target-specific chat capabilities. Do not instantiate them for a no-secret smoke unless a target has already been configured and authorized.
- Remote dataset providers can download from public URLs, HuggingFace, or ZIP archives and may populate PyRIT's data cache. Use local YAML or explicit small `dataset_names` for bounded work.
- `NoOpConverter` is not exported from `pyrit.converter` in this checkout; use an empty converter list when no conversion is needed.
