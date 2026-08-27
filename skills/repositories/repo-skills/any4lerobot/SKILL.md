---
name: "any4lerobot"
description: "Guides Any4LeRobot dataset conversions, LeRobot-to-RLDS export,
  and LeRobot v1.6-v3.0 format migrations with schema validation, version-aware
  environments, and safe publication boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Any4LeRobot

Any4LeRobot is a script-oriented toolbox for moving robotics datasets into and
between LeRobot formats. Use this skill to plan a conversion from a documented
source layout, select the matching route, validate schemas before writing, and
keep Ray, Beam, simulator, video, and Hub side effects explicit.

## Start here

1. Identify the **source format**, target format/version, local source root,
   output root, desired modalities, and whether publication is requested.
2. Read [workflow selection](references/workflow-selection.md) and choose one
   focused route below. Load [troubleshooting](references/troubleshooting.md)
   before changing dependencies or retrying a failed run.
3. Check [repository provenance](references/repo-provenance.md) when working
   from a checkout or deciding whether the guidance needs refreshing.
4. Run the safe environment probe in `scripts/check_environment.py` before
   executing any converter. It reports core and optional import/API status but
   never downloads data or writes a dataset.
5. Build a no-write preflight: verify input layout, feature shapes/dtypes,
   version/API compatibility, distinct output path, backup/rollback plan, and
   resource budget. Start with local/debug execution; defer Hub publication.

This skill contains distilled guidance, not a dependency on the original
checkout. Do not tell a future agent to run a source-repository script or
checkout-relative `convert.sh`; use the route references and their commands as
recipes, then verify the equivalent entry point in the selected environment.

## Route map

| User request or input | Read this route |
|---|---|
| Design an adapter, use local/Ray DataTrove execution, aggregate task outputs, resume, or publish | [`generic-conversion`](sub-skills/generic-conversion/SKILL.md) |
| Open X-Embodiment/RLDS/TFDS → LeRobot | [`openx-conversion`](sub-skills/openx-conversion/SKILL.md) |
| AgiBotWorld raw tree → LeRobot | [`agibot-conversion`](sub-skills/agibot-conversion/SKILL.md) |
| RoboMIND benchmark/embodiment HDF5 → LeRobot | [`robomind-conversion`](sub-skills/robomind-conversion/SKILL.md) |
| LIBERO HDF5 → LeRobot or LIBERO rerender planning | [`libero-conversion`](sub-skills/libero-conversion/SKILL.md) |
| RoboCasa HDF5, subset, depth/segmentation, or rerender planning | [`robocasa-conversion`](sub-skills/robocasa-conversion/SKILL.md) |
| LeRobot → RLDS/TFDS | [`rlds-export`](sub-skills/rlds-export/SKILL.md) |
| LeRobot v1.6, v2.0, v2.1, or v3.0 migration | [`version-migration`](sub-skills/version-migration/SKILL.md) |

Do not conflate the two RLDS directions: `openx-conversion` consumes an RLDS
builder, while `rlds-export` produces one. Do not use `version-migration` to
convert raw HDF5 or to repair missing modalities.

## Environment contract

Any4LeRobot has no `pyproject.toml`, `setup.py`, or declared distribution. The
usual baseline is a private Python 3.10/3.11 environment with a LeRobot writer
compatible with the selected source script, NumPy, h5py, pyarrow/pandas,
Pillow/OpenCV, tqdm, and the video codec stack. Add only what the route needs:

- `datatrove` for the shared pipeline; Ray/DataTrove Ray extras only for
  distributed execution.
- `tensorflow` and `tensorflow-datasets` for either RLDS direction; Apache Beam
  is optional and should be disabled for small/lossless exports.
- `datasets`, `jsonlines`, `safetensors`, and the exact historical LeRobot
  revision for version migration. Keep v2.x and v3.x environments separate.
- RoboCasa/robosuite or LIBERO plus their assets only for simulator rerendering;
  these are not required for ordinary HDF5 conversion and are not verified by
  this skill.

Verify the installed API rather than trusting a package import alone:

```bash
python -c "from lerobot.datasets.lerobot_dataset import LeRobotDataset, LeRobotDatasetMetadata; print('LeRobot API OK')"
python -c "import h5py, pyarrow, torch, torchcodec; print('core dependencies OK')"
```

The source snapshot mixes historical and current LeRobot import locations. In
particular, a current release may not re-export `LeRobotDataset` from
`lerobot.datasets` or provide `lerobot.datasets.dataset_writer.py`. Treat that
as a compatibility stop gate; do not patch imports or metadata behavior by
guesswork. Read the route-specific troubleshooting before selecting another
revision.

## Safety gates

- Never use the raw source tree as the output root. Inventory existing output
  and temporary paths first; several converters delete an existing destination.
- Never enable `--push-to-hub`, Hub deletion/tagging, Git-LFS moves, or public
  upload during the first local pass. Use a new staging root or test branch.
- Do not run Ray, Beam, simulator rendering, or large video/data conversions as
  an import or help check. Record external datasets, credentials, assets, and
  hardware as explicit prerequisites.
- Preserve source version, feature schemas, task text, and episode counts.
  A successful file open is not proof that all episodes or modalities are
  convertible.

## Shared references

- Read [workflow selection](references/workflow-selection.md) for route
  triggers, directionality, and the preflight record.
- Read [troubleshooting](references/troubleshooting.md) for install/import,
  optional backend, schema, output, and publication failures.
- Run [the environment probe](scripts/check_environment.py) for a no-write
  dependency/API status summary.
- Read [provenance](references/repo-provenance.md) before refresh or when the
  repository commit differs from this generated baseline.
