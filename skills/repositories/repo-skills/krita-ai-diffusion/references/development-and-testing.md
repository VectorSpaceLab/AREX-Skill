# Development and Testing Reference

Use this reference when a user asks how to edit, test, lint, or safely inspect
Krita AI Diffusion plugin behavior. Keep runtime instructions self-contained:
when a helper is needed, use the bundled scripts in this skill rather than
source checkout scripts unless the user explicitly asks for maintainer release
operations.

## Runtime and dependency rules

- The plugin runs inside Krita's embedded Python interpreter at runtime.
- Plugin code should not add arbitrary third-party runtime libraries. The
  documented runtime exception is Qt/PyQt and the bundled `websockets` package;
  server-side ComfyUI dependencies live outside the plugin.
- Outside Krita, tests use the repo's mock Krita module and PyQt event-loop
  helpers. Set `QT_QPA_PLATFORM=offscreen` for headless Qt checks.
- Source checkouts must have the vendored websockets submodule or a release-style
  package layout; otherwise `import ai_diffusion` raises the explicit missing
  websockets ImportError.
- Generated skill and review artifacts under `skills/` are not source evidence
  and should not be included in package discovery or production builds.

## Maintainer commands

The repo's own guidance requires activating the project virtual environment and
running these checks after changes:

```bash
ruff check
ruff format
pyright
```

Native tests should be selected by risk and scope:

1. Focused test file first, for example:

   ```bash
   QT_QPA_PLATFORM=offscreen pytest tests/test_api.py -q
   QT_QPA_PLATFORM=offscreen pytest tests/test_custom_workflow.py -q
   ```

2. Fast no-inference test suite when broader coverage is needed:

   ```bash
   QT_QPA_PLATFORM=offscreen pytest tests --ci
   ```

3. Only after workflow-generation changes, run workflow tests. These may require
   ComfyUI/cloud setup depending on options and fixtures:

   ```bash
   QT_QPA_PLATFORM=offscreen pytest tests/test_workflow.py
   ```

4. Only after cloud client changes and with explicit service approval:

   ```bash
   QT_QPA_PLATFORM=offscreen pytest tests/test_workflow.py --cloud
   ```

5. Only after installer/server changes and with explicit approval for downloads,
   installation, and filesystem mutation:

   ```bash
   QT_QPA_PLATFORM=offscreen pytest tests/test_server.py --test-install
   ```

## Safe bundled checks

Use these bundled helpers for no-side-effect inspection:

```bash
python scripts/check_krita_ai_diffusion_environment.py --static-only
python scripts/list_krita_ai_diffusion_resources.py --summary
python sub-skills/inference-workflows/scripts/inspect_workflow_input.py --kind generate --round-trip
python sub-skills/custom-graphs/scripts/inspect_custom_workflow.py workflow.json
python sub-skills/ui-workspaces/scripts/inspect_workspace_enums.py --static-only
python sub-skills/document-image-state/scripts/inspect_prompt_style.py --prompt "cat <lora:fur:0.6> # note" --style-prompt "cinematic {prompt}" --lora-id fur --metadata
```

Use `--strict` or import-live modes only in an environment where the plugin can
import successfully. These helpers do not launch Krita, connect to ComfyUI,
download models, install a server, or call cloud APIs.

## Source artifact import map

| Source repo artifact | Decision | Bundled skill replacement | Owner | Reason |
| --- | --- | --- | --- | --- |
| `scripts/download_models.py` | reference-only | `sub-skills/server-resources/references/resources-and-models.md` and `scripts/list_krita_ai_diffusion_resources.py` | server-resources | The source script downloads model files into a ComfyUI tree; unsafe without explicit user approval. The skill preserves catalog/selection guidance and a read-only resource lister. |
| `scripts/file_server.py` | exclude | none | server-resources | Test support server for installer tests; not a user-facing plugin workflow. |
| `scripts/package.py` | reference-only | `references/development-and-testing.md` | root | Release packaging mutates build artifacts and bundles vendor code; maintainer-only and not needed for operating tasks. |
| `scripts/translation.py` | reference-only | `references/development-and-testing.md` | root/ui-workspaces | Localization maintenance is outside selected runtime skill scope; mention only as maintainer context. |
| `tests/data/workflow-custom.json` | adapt by behavior | `sub-skills/custom-graphs/scripts/inspect_custom_workflow.py` | custom-graphs | The bundled helper can inspect any equivalent ComfyUI JSON graph without depending on the test fixture. |
| Workflow/model tests | adapt by behavior | `sub-skills/inference-workflows/scripts/inspect_workflow_input.py` and sub-skill references | inference-workflows | Tests anchor behavior; bundled helper constructs tiny in-memory inputs instead of requiring fixtures or generation. |
| Text/style tests | adapt by behavior | `sub-skills/document-image-state/scripts/inspect_prompt_style.py` | document-image-state | Safe reusable prompt/style/LoRA behavior is extracted into an offline helper. |

## Native test candidate map

| Candidate | Workflow | Safety | Backend | Criticality | CPU substitute | Skill owner | Expected evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pytest tests/test_api.py -q` | API serialization | safe-runnable | cpu | required | full | inference-workflows | `WorkflowInput` round-trip behavior passes. |
| `pytest tests/test_comfy_workflow.py tests/test_resolution.py -q` | Comfy graph/resolution helpers | safe-runnable | cpu | required | full | inference-workflows | Graph helper and resolution assertions pass. |
| `pytest tests/test_custom_workflow.py -q` | custom graph parameters | safe-runnable | cpu | required | full | custom-graphs | ETN parameter parsing/validation passes. |
| `pytest tests/test_model.py tests/test_connection.py tests/test_properties.py -q` | Qt workspace/model state | safe-runnable | cpu | required | full | ui-workspaces/document-image-state | Workspace generation routing, connection, properties pass. |
| `pytest tests/test_text.py tests/test_image.py tests/test_persistence.py -q` | prompt/image/persistence helpers | safe-runnable | cpu | required | full | document-image-state | Prompt/image/persistence assertions pass when selected. |
| `pytest tests/test_client.py -q` | live Comfy client | skip-unsafe | external ComfyUI/GPU optional | optional | partial | server-resources | Requires running server and resources. |
| `pytest tests/test_server.py --test-install` | managed server install/download | skip-unsafe | network/filesystem/backend optional | optional | partial | server-resources | Downloads and mutates server installation. |
| `pytest tests/test_workflow.py --cloud` | cloud generation | skip-unsafe | cloud credentials | optional | none | inference-workflows/server-resources | Requires service token/cost and live backend. |

## Coverage/depth matrix

| Capability | Kind | Evidence | Output location | Verification expectation |
| --- | --- | --- | --- | --- |
| Generation/refine/inpaint/upscale/control request construction | primary workflow | `api.py`, `workflow.py`, `tests/test_workflow.py`, `tests/test_model.py` | `sub-skills/inference-workflows/` | Bundled helper round-trips `WorkflowInput`; safe native workflow/model tests pass where selected. |
| ComfyUI/cloud/server resource setup and diagnosis | primary/support workflow | docs installation/common issues/comfyui setup, `server.py`, `resources.py`, client tests | `sub-skills/server-resources/` | Resource lister and URL parser pass; unsafe installs/generation explicitly skipped. |
| UI workspace state and job lifecycle | primary workflow | `model.py`, `jobs.py`, `connection.py`, `tests/test_model.py` | `sub-skills/ui-workspaces/` | Workspace enum helper and selected model/connection tests pass. |
| Custom Graph workspace workflows | primary workflow | custom graph docs, `custom_workflow.py`, `comfy_workflow.py`, custom workflow tests | `sub-skills/custom-graphs/` | Graph inspector parses ETN placeholders and parameter order. |
| Document/layer/image/prompt/style persistence | support workflow | `document.py`, `layer.py`, `image.py`, `text.py`, `style.py`, persistence tests | `sub-skills/document-image-state/` | Prompt/style helper and selected text/image/persistence tests pass. |
| Contributor checks and test selection | maintainer workflow | `AGENTS.md`, `CONTRIBUTING.md`, `tests/pytest.ini` | root `references/development-and-testing.md` | Commands and risk-based test order are documented. |

## Long-tail gaps

- Full generation quality and GPU/cloud performance are not verified by this
  skill; those require explicit user-approved ComfyUI/cloud runs.
- Managed server installer workflows are represented as troubleshooting and
  resource guidance, not executed proof, because they download and mutate large
  server directories.
- Release packaging and translation maintenance are not runtime operating
  workflows. Use repository maintainer docs if the user explicitly asks for a
  release task.
