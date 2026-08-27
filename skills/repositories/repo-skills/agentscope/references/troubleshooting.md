# Troubleshooting

## When to read this

Read this if the package does not import cleanly, a sub-skill seems to need the wrong extra, or you are not sure whether a failure belongs to the runtime package, an optional backend, or the host environment.

## Common cross-cutting failures

### `ImportError` on a subpackage

**Symptoms**
- `ImportError` or `ModuleNotFoundError` when importing `agentscope.model`, `agentscope.app`, `agentscope.workspace`, or a provider-specific class.
- `pip check` passes, but a submodule still fails to import.

**Likely causes**
- The wrong extra was installed for the workflow.
- A provider/service/backend dependency is missing from the environment.
- A stale editable install is pointing at an unexpected checkout.

**What to do next**
1. Run `scripts/check_env.py --show-backends`.
2. Install the matching sub-skill extra or the broad `agentscope[full]` set.
3. Re-run the minimal import check from the root skill.

### `pip check` fails

**Symptoms**
- Dependency conflicts, missing extras, or incompatible versions.

**Likely causes**
- Partially updated environment.
- Mixing a targeted extra with an older install of the same package.

**What to do next**
- Reinstall the selected extras in a clean prefix if possible.
- If the environment is a shared user environment, do not mutate it in place without permission.

### Runtime appears to use the wrong module copy

**Symptoms**
- Imported modules resolve to an unexpected path.
- Behavior differs from the version currently on disk.

**Likely causes**
- An editable install, stale `.pth`, or an old prefix is shadowing the intended package.

**What to do next**
- Check `python -c "import agentscope; print(agentscope.__file__)"` from the target environment.
- Refresh the install if the package version or commit has changed.

## Optional-backend confusion

### Service/workspace backend missing

**Symptoms**
- Docker, Redis, Kubernetes, or another backend-specific test is unavailable.
- A demo or live deployment path works in docs but not on the current host.

**Likely causes**
- The optional backend is not installed or the daemon/service is not running.
- The current host is not the right platform for that backend.

**What to do next**
- Use the matching sub-skill troubleshooting page.
- For local validation, prefer the unit-test or in-memory/local workflow first.
- For a live backend, verify the host prerequisite before changing the Python environment.

### Provider API keys missing

**Symptoms**
- Provider constructors import successfully but live calls fail immediately.
- Example scripts or demos mention a missing `*_API_KEY` environment variable.

**Likely causes**
- The provider requires a key, base URL, or local server that has not been configured.

**What to do next**
- Check `provider-connectors/references/troubleshooting.md`.
- Use the mocked unit tests or the provider matrix helper first to confirm the Python-side wiring.

## Safe diagnostic helpers

- `scripts/check_env.py` — quick import and backend-availability check for the full skill tree.
- The sub-skill scripts linked from each workflow — use them only after reading the matching sub-skill.

## When to stop

Stop and ask for a backend, credential, cluster, or local service only if the relevant sub-skill says the capability genuinely depends on that external component. Otherwise, prefer the local or mocked path documented in the matching sub-skill.
