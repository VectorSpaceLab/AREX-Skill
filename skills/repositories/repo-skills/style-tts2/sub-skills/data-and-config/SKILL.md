---
name: data-and-config
description: "Prepare and validate StyleTTS2 data lists, OOD text files, config
  YAML, and asset paths before training or inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-and-config

Use this sub-skill to check the inputs StyleTTS2 workflows depend on before any stage launch or demo handoff.

## Covers
- train/val list schema, speaker labels, and OOD text files
- 24 kHz audio-root assumptions and validation split handling
- config fields that drive stage selection, checkpoint loading, model layout, and memory use
- safe inspectors:
  - [scripts/validate_data_lists.py](scripts/validate_data_lists.py) checks list rows, optional wav existence, speaker ids, and OOD text readiness without training.
  - [scripts/inspect_config.py](scripts/inspect_config.py) summarizes high-impact config fields, path semantics, and stage warnings without launching a run.

## Route elsewhere
- Training launches, checkpointed stage progression, and resume behavior: [training sub-skill](../training/SKILL.md)
- Pretrained demo assets, reference-audio handling, and synthesis setup: [inference sub-skill](../inference/SKILL.md)

## Quick checks
- Validate rows and optional file presence before training.
- Inspect a config before editing paths, batch size, decoder type, or checkpoint settings.
- Keep explicit speaker ids in public lists, especially for multispeaker data.

## References
- [Data formats](references/data-formats.md)
- [Configuration guide](references/configuration.md)
- [Troubleshooting](references/troubleshooting.md)
