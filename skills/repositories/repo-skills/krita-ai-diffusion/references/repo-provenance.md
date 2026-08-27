# Repository Provenance

Use this reference to decide whether the generated skill still matches the
current repository. If the source repository, public API, workflow graph logic,
resource catalog, docs, tests, or dependency policy changed after this snapshot,
run a refresh before relying on version-sensitive details.

## Snapshot

- Repository: `krita-ai-diffusion`
- Upstream remote: `https://github.com/Acly/krita-ai-diffusion.git`
- Branch at extraction: `main`
- Commit at extraction: `3f9007cefb23eaa5c63b4c179076623f81918c27`
- Git tag/describe: `v1.52.1`
- Python package/module version: `ai_diffusion.__version__ == "1.52.1"`
- Resource catalog/server version: `ai_diffusion.backend.resources.version == "1.52.0"`
- Skill id: `krita-ai-diffusion`
- Verification scope: CPU/package inspection and offline graph/resource/model
  checks. Real generation, managed server installation/downloads, GPU backends,
  and cloud service calls were intentionally not selected as required evidence.
- Dirty-state note: generated skill/review artifacts under `skills/` are local
  untracked output and are not source evidence.

## Evidence included during extraction

Primary source roots and docs:

- `ai_diffusion/__init__.py` for plugin version and vendored websockets import
  guard.
- `ai_diffusion/backend/api.py` for `WorkflowInput` and generation request
  dataclasses.
- `ai_diffusion/backend/workflow.py` and `ai_diffusion/backend/comfy_workflow.py`
  for prompt preparation, workflow kind routing, inpaint/upscale/control/custom
  lowering, and ETN node construction.
- `ai_diffusion/backend/client.py`, `ai_diffusion/backend/comfy_client.py`,
  `ai_diffusion/backend/cloud_client.py`, `ai_diffusion/backend/network.py`, and
  `ai_diffusion/backend/server.py` for client/server state, local/cloud
  communication, URL parsing, managed server lifecycle, and error parsing.
- `ai_diffusion/backend/resources.py` for resource catalog version, model
  architectures, custom nodes, model files, workloads, and verification status.
- `ai_diffusion/model/model.py`, `ai_diffusion/model/custom_workflow.py`,
  `ai_diffusion/model/jobs.py`, `ai_diffusion/model/region.py`, and
  `ai_diffusion/model/control.py` for workspace state, job queues, custom graph
  workspace behavior, regions, and control layers.
- `ai_diffusion/document.py`, `ai_diffusion/layer.py`, `ai_diffusion/image.py`,
  `ai_diffusion/text.py`, `ai_diffusion/style.py`, `ai_diffusion/settings.py`,
  `ai_diffusion/persistence.py`, and related helpers for Krita data, prompt
  processing, styles, image/mask conversion, and persisted document/settings
  state.
- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, and user-facing docs under
  `docs/src/content/docs/`, especially basics, installation, ComfyUI setup,
  custom graph, common issues, selections, resolutions, samplers, prompts,
  control layers, and edit models.
- Representative tests under `tests/`, especially API serialization, workflow
  preparation/lowering, custom workflow parsing, model/workspace state,
  connection handling, server helper/error parsing, settings/properties,
  image/text/persistence behavior, and fixtures under `tests/data/`.

## Evidence excluded or de-prioritized

- `.git`, `.github`, `.vscode`, editor metadata, and CI-only configuration as
  runtime guidance.
- Bulk images, screenshots, docs assets, generated documentation site assets,
  test reference images, and media except where a test name anchored a behavior.
- Vendored third-party internals under `ai_diffusion/websockets` and
  `ai_diffusion/debugpy`; the skill only documents the public import guard and
  release packaging requirement.
- Credentials, deployment-only concerns, private caches, model weights, managed
  server installation directories, benchmark results, and local review/test
  artifacts.
- Destructive or expensive native flows: actual model downloads, ComfyUI managed
  server install/upgrade/uninstall, cloud generation, and GPU inference.

## Native verification candidates used as evidence

Safe selected candidates:

- `pytest tests/test_api.py -q` for API dataclass serialization and import
  guard behavior.
- `pytest tests/test_comfy_workflow.py tests/test_resolution.py -q` for ComfyUI
  workflow graph helper and resolution logic.
- `pytest tests/test_custom_workflow.py -q` for custom graph parameter parsing
  and validation.
- `pytest tests/test_model.py tests/test_connection.py tests/test_properties.py -q`
  for workspace model state, queue/progress/error behavior, connection state,
  and observable properties.
- Bundled helper scripts in this skill for import/resource/static graph/prompt
  smoke checks.

Skipped/unsafe native candidates:

- Server installer/download tests in `tests/test_server.py --test-install` and
  server lifecycle tests that mutate ComfyUI installations or require local
  download servers/model resources.
- `tests/test_client.py` and full `tests/test_workflow.py` cases that require a
  running ComfyUI server, cloud service, large model resources, or generation.
- Scripts such as `scripts/download_models.py`, `scripts/file_server.py`,
  `scripts/package.py`, and `scripts/translation.py` as runtime entry points;
  these are maintainer or side-effecting utilities and are represented by safe
  bundled inspection helpers or reference-only notes instead.

## Refresh triggers

Refresh this skill when any of the following change:

- `ai_diffusion.__version__`, resource catalog `version`, or server resource
  workload definitions.
- `WorkflowInput`, `WorkflowKind`, prompt/style/LoRA preparation, inpaint,
  upscale, control, or custom workflow lowering signatures.
- Custom graph ETN placeholder node names, parameter types, output behavior, or
  Graph workspace validation rules.
- `DocumentModel`, workspace enums, settings, connection/job states, or Krita
  document/layer/image APIs.
- ComfyUI required custom node list, model architectures, backend selection,
  server install layout, or cloud/local client protocol.
- AGENTS/CONTRIBUTING test policy, dependency requirements, supported Python or
  Krita version, or bundled websockets/debugpy packaging rules.
