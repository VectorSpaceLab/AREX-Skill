# Repository Provenance

schema: `disco.repo-provenance.v1`

This skill was generated from MONAI repository evidence and live package inspection.

| Field | Value |
| --- | --- |
| Repository | Project-MONAI/MONAI |
| Remote URL | https://github.com/Project-MONAI/MONAI.git |
| Commit | `15f50736067093ec3716dfebdf37fe454ef79189` |
| Branch | `dev` |
| Exact tag | none detected |
| Working tree state | dirty: generated `skills/` directory untracked during skill creation |
| Installed distribution | `monai` |
| Inspected package version | `0+untagged.1.g15f5073` |
| Base Python requirement | Python `>=3.10` |
| Base dependencies | `torch>=2.8.0`, `numpy>=1.24,<3.0` |

## Evidence Paths

- `README.md`
- `setup.cfg`
- `setup.py`
- `pyproject.toml`
- `requirements.txt`
- `requirements-min.txt`
- `requirements-dev.txt`
- `docs/source/installation.md`
- `docs/source/transforms.rst`
- `docs/source/transforms_idx.rst`
- `docs/source/data.rst`
- `docs/source/lazy_resampling.rst`
- `docs/source/networks.rst`
- `docs/source/losses.rst`
- `docs/source/metrics.rst`
- `docs/source/inferers.rst`
- `docs/source/visualize.rst`
- `docs/source/engines.rst`
- `docs/source/handlers.rst`
- `docs/source/optimizers.rst`
- `docs/source/precision_accelerating.md`
- `docs/source/bundle.rst`
- `docs/source/bundle_intro.rst`
- `docs/source/config_syntax.md`
- `docs/source/mb_specification.rst`
- `docs/source/mb_properties.rst`
- `docs/source/auto3dseg.rst`
- `docs/source/apps.rst`
- `docs/source/applications.md`
- `monai/transforms/`
- `monai/data/`
- `monai/networks/`
- `monai/losses/`
- `monai/metrics/`
- `monai/inferers/`
- `monai/visualize/`
- `monai/engines/`
- `monai/handlers/`
- `monai/optimizers/`
- `monai/bundle/`
- `monai/auto3dseg/`
- `monai/apps/auto3dseg/`
- `monai/apps/nnunet/`
- `tests/data/`
- `tests/transforms/`
- `tests/inferers/`
- `tests/losses/`
- `tests/metrics/`
- `tests/networks/`
- `tests/engines/`
- `tests/handlers/`
- `tests/optimizers/`
- `tests/bundle/`
- `tests/apps/`
- `tests/auto3dseg/`
- `tests/integration/`

## Refresh Guidance

Refresh this skill when MONAI changes public APIs, Bundle config syntax or CLI commands, Auto3DSeg interfaces, required Python/Torch versions, optional dependency groups, or major docs/workflow examples. A dirty checkout means the commit alone is not a complete source baseline; compare the current repository state and evidence paths before assuming the skill is still current.
