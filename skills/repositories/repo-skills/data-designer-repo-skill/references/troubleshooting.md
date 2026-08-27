# Cross-Cutting Troubleshooting

## Purpose

Read this when DataDesigner imports or commands fail before you know which sub-skill owns the problem.

## Common failure surfaces

### 1) Package or CLI not installed

Symptoms:
- data-designer command not found
- import errors for data_designer modules
- pip check fails after installation

Likely causes:
- The package was not installed into the active Python environment.
- The environment is not the one you intended to inspect.
- A partial installation left one workspace package out of sync.

Recovery:
- Re-run the install guidance in the root SKILL.md.
- Run scripts/check_datadesigner_environment.py for a read-only smoke check.
- Verify the config, engine, and interface packages all report the same version.

### 2) No usable model aliases

Symptoms:
- data-designer agent context reports no usable model aliases
- preview/create/check-models complain about missing providers or API keys
- validation works, but generation does not

Likely causes:
- Providers or model configs have not been created yet.
- The provider exists but the required API key is missing.
- The task only needs config inspection, not generation.

Recovery:
- Use cli-and-agent-tools to inspect model alias state.
- Configure providers/models before running generation-backed workflows.
- If you only need schema validation, stay in config-authoring or generation-runtime validate mode.

### 3) Persona assets are missing

Symptoms:
- PersonSamplerParams or person-based recipes mention unavailable locales.
- Agent state shows locales but they are not installed.

Likely causes:
- Managed persona datasets were not downloaded.
- The assets live outside the default managed-assets path.

Recovery:
- Inspect persona state with cli-and-agent-tools.
- Download the needed locale or set DATA_DESIGNER_MANAGED_ASSETS_PATH to the correct directory.
- Use person_from_faker only if the workflow can tolerate the lower-fidelity fallback.

### 4) Plugin or MCP confusion

Symptoms:
- The user names a runtime plugin name when the CLI expects a package name.
- MCP tool aliases are referenced but no tool config is present.
- Plugin load or entry-point discovery fails.

Recovery:
- Use plugins-and-extensions for package vs runtime-name resolution.
- Confirm the installed plugin package exposes the expected entry point.
- Check that the configured MCP provider is reachable before trying check-models or tool-augmented generation.

### 5) Preview/create errors from remote dependencies

Symptoms:
- check-models or generation fails with authentication, timeout, rate-limit, or remote-model errors.
- preview/create works for sampler-only configs but fails once LLM/image columns are added.

Likely causes:
- API key missing or invalid.
- Remote provider unavailable.
- Tool server not reachable.
- The workflow needs a backend or credential that is intentionally not installed in this environment.

Recovery:
- Confirm the task really needs the remote path.
- Use generation-runtime to distinguish validate-only from generation-backed workflows.
- If credentials or network are intentionally unavailable, document the limitation rather than pretending the workflow is fully verified.

## Where to go next

- Config problems -> sub-skills/config-authoring/
- Preview/create/resume/export problems -> sub-skills/generation-runtime/
- CLI and state-file problems -> sub-skills/cli-and-agent-tools/
- Plugin or MCP problems -> sub-skills/plugins-and-extensions/
- Notebook/recipe/integration problems -> sub-skills/recipes-and-integrations/
