---
name: swanlab
description: "Use SwanLab for ML experiment tracking, logging, media charts,
  modes, CLI/Open API, sync/converters, integrations, plugins, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SwanLab Repo Skill

Use this skill when a task involves SwanLab, the `swanlab` Python package, the `swanlab` CLI, experiment tracking/visualization, local/offline run sync, Open API queries, media logging, converter workflows, framework callbacks, notification plugins, or SwanLab troubleshooting.

SwanLab is an ML experiment tracking and visualization library. It supports cloud, offline, local, and disabled modes; a Python SDK; a Click CLI; media/chart artifacts; local run synchronization; converters for other experiment trackers; and adapters/plugins for common ML frameworks.

## First checks

1. Confirm the package is installed in the user's target environment:

   ```bash
   python -c "import swanlab; print(swanlab.__version__)"
   swanlab --help
   ```

2. If the user has no API key or network access, start in `mode="disabled"`, `mode="offline"`, or `mode="local"` instead of copying a cloud-only quick start.
3. If the task touches rich media, framework callbacks, dashboard, S3, or cloud/self-hosted APIs, check the relevant optional dependencies, credentials, service endpoints, and hardware before running a long training job.
4. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a SwanLab checkout or whether to refresh it.

## Route by task

| User task | Read next |
| --- | --- |
| Add SwanLab to a training loop; call `init`, `log`, `finish`; debug `swanlab.run`; smoke-test tracking without credentials | [sub-skills/experiment-tracking/SKILL.md](sub-skills/experiment-tracking/SKILL.md) |
| Choose `online`, `offline`, `local`, or `disabled`; configure `Settings`; handle login/API hosts; reason about env/YAML/secret precedence | [sub-skills/settings-and-modes/SKILL.md](sub-skills/settings-and-modes/SKILL.md) |
| Log text, HTML, images, audio, video, pyecharts/ECharts, molecules, 3D objects, or custom charts | [sub-skills/media-and-custom-charts/SKILL.md](sub-skills/media-and-custom-charts/SKILL.md) |
| Use `swanlab.Api` or `swanlab api` for workspaces, projects, runs, metrics, summaries, columns, media, logs, exports, or self-hosted admin data | [sub-skills/open-api-and-cli/SKILL.md](sub-skills/open-api-and-cli/SKILL.md) |
| Upload local/offline runs; validate run directories; sync crash logs; convert TensorBoard, W&B, or MLflow records | [sub-skills/sync-and-converters/SKILL.md](sub-skills/sync-and-converters/SKILL.md) |
| Add framework callbacks or plugins: Transformers, Lightning, Keras, XGBoost, LightGBM, Ray, Accelerate, notifications, CSV writer, custom callbacks | [sub-skills/integrations-and-plugins/SKILL.md](sub-skills/integrations-and-plugins/SKILL.md) |
| Install/import failure, optional dependency issue, CLI command not found, API-key/host confusion, network/service issue | [references/troubleshooting.md](references/troubleshooting.md) plus the nearest sub-skill troubleshooting file |
| Public install choices, extras, smoke checks, Python support, optional dependency matrix | [references/installation-and-environment.md](references/installation-and-environment.md) |
| Maintainer questions about protobuf generation, package build/test commands, Go core boundary, or repo-local PR-review skills | [references/protobuf-and-maintainer-notes.md](references/protobuf-and-maintainer-notes.md) |

## Common safe snippets

Credential-free tracking smoke:

```python
import swanlab

run = swanlab.init(project="smoke", mode="disabled")
swanlab.log({"loss": 0.1, "acc": 0.9})
swanlab.finish()
assert swanlab.run is None
```

For a reusable command-line check, run [scripts/swanlab_disabled_smoke.py](scripts/swanlab_disabled_smoke.py). For CLI registration checks, run [scripts/check_swanlab_cli.py](scripts/check_swanlab_cli.py).

## Public install and extras

- Base package: `pip install swanlab`.
- Source/editable development: install the package from a SwanLab checkout only when the user is actively developing SwanLab itself.
- Rich media extras: `pip install "swanlab[media]"` for audio/image/video/molecule dependencies when a workflow needs them.
- Dashboard extension: `pip install "swanlab[dashboard]"` when `swanlab watch` or offline-board usage requires the dashboard package.
- S3 support: `pip install "swanlab[s3]"` when uploads or storage paths require boto3/S3 behavior.
- Framework adapters usually require the framework package itself; the base SwanLab install intentionally does not install every training stack.

## Validation expectations

Use this order when validating a task-specific answer:

1. Import/package check: `python -c "import swanlab; print(swanlab.__version__)"`.
2. Route-specific safe helper from this skill, when available.
3. CLI help or dry-run checks before live network/API calls.
4. Native or user-provided training/API cases only after credentials, service endpoints, optional dependencies, data paths, and hardware are explicitly available.

Do not claim that real cloud upload, self-hosted administration, GPU/vendor hardware monitoring, dashboard service startup, rich media conversion, or framework training has been verified unless the task environment actually exercised that surface.
