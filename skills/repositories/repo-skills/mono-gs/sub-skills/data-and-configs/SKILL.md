---
name: data-and-configs
description: "Acquire MonoGS datasets, validate dataset layouts, and edit
  inherited YAML configs for TUM, Replica, EuRoC, and RealSense workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data and Configs

Use this sub-skill to prepare dataset roots, inspect config inheritance, and preflight MonoGS YAML files before a run.

## Start here
- [references/configuration.md](references/configuration.md)
- [references/data-layouts.md](references/data-layouts.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/validate_monogs_config.py](scripts/validate_monogs_config.py)
- [scripts/download_tum.sh](scripts/download_tum.sh)
- [scripts/download_replica.sh](scripts/download_replica.sh)
- [scripts/download_euroc.sh](scripts/download_euroc.sh)

## Covers
- recursive `inherit_from` config merging
- safe edits to scene-level YAML overrides
- TUM, Replica, EuRoC, and RealSense dataset roots
- dataset layout validation with `--check-files`
- safe dataset download helpers with a configurable target root

## Does not cover
- CUDA or compiler installation
- SLAM execution or runtime tuning
- evaluation metrics or result interpretation
- live camera GUI operation

## Typical use
- Validate a config and its dataset root:
  `python scripts/validate_monogs_config.py --check-files configs/mono/tum/fr3_office.yaml`
- Download the bundled sample datasets:
  `bash scripts/download_tum.sh --target-root datasets`
