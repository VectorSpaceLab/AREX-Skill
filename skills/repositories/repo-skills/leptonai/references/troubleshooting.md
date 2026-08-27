# Cross-cutting troubleshooting

Use this before or after a focused sub-skill when the problem spans install/import, global CLI behavior, workspace auth, network, or skill staleness.

## `import leptonai` or `lep` is missing

**Symptoms:** `ModuleNotFoundError: No module named 'leptonai'`, `lep: command not found`, or scripts cannot find the package.

**Likely causes:** package is not installed in the current Python, the CLI entry point is not on `PATH`, or a source checkout was installed without the expected environment.

**Recovery:**

```bash
python -m pip install -U leptonai
python -c "import leptonai; print(leptonai.__version__)"
python -m pip show leptonai
lep --help
```

If working in a source checkout, use `python -m pip install -e .` and add `.[test]` only when running repo-native tests. Do not install lint/dev extras for ordinary SDK/CLI use.

## `lep` prints a newer-version warning

**Symptom:** help or workspace commands print `A newer version of leptonai (...) is available` before normal output.

**Likely cause:** the CLI checks PyPI once per cache interval and warns when the local installed version is older.

**Recovery:** treat it as informational unless the task requires a feature that only exists in a newer release. If exact behavior matters, run `lep --version`, inspect `lep <group> --help`, and update with `pip install -U leptonai` only after the user approves changing the environment.

## Current workspace is missing or wrong

**Symptoms:** `No current workspace is set`, `Workspace configuration error`, a command targets an unexpected workspace, or environment variables and persisted workspace records disagree.

**Recovery:** route to [../sub-skills/workspace-and-auth/SKILL.md](../sub-skills/workspace-and-auth/SKILL.md). Use safe context checks first:

```bash
python ../sub-skills/workspace-and-auth/scripts/check_workspace_context.py
lep workspace list
lep workspace id
lep workspace url
lep workspace status
```

Redact tokens. Avoid `lep workspace token` unless raw token retrieval is explicitly the task.

## 401, 403, 404, URL mismatch, or token expiry

**Symptoms:** `WorkspaceUnauthorizedError`, `WorkspaceForbiddenError`, `WorkspaceNotFoundError`, 401/403/404 API messages, or expiry warnings.

**Likely causes:** expired token, token from a different Lepton environment, wrong workspace URL/origin URL, newly created workspace not ready, insufficient permissions, or stale persisted record.

**Recovery:**

1. Compare intended workspace ID and sanitized URL; do not print the token.
2. Re-login with the correct workspace ID/token and workspace URL when required.
3. If the workspace was just created, wait for propagation before retrying.
4. Do not proceed to resource mutations until a read-only workspace status/list succeeds.

## Network, DNS, socket, or timeout failures

**Symptoms:** DNS resolution errors, `FailedToOpenSocket`, request timeouts, server 5xx, or sandboxed network errors.

**Recovery:** separate local syntax/help checks from live API checks. Help-only bundled scripts can still run. For live Lepton reads/mutations, surface the exact error and ask whether to retry with broader network access or after the service recovers.

## Empty option value rejected

**Symptom:** a `lep` command fails because a string option is empty or whitespace-only.

**Likely cause:** the CLI's custom Click command class rejects blank values passed explicitly on the command line.

**Recovery:** omit the flag when unset, or provide a non-empty value. This affects both single string options and repeated options.

## Cloud mutation in an automated plan

**Symptoms:** the user asks to delete/stop/create/update/upload/download/replace endpoints in auto mode, or a broad command such as `remove-all`, `stop-all`, `rmdir -r`, or `ingress set-endpoints` appears.

**Recovery:** do not execute immediately. Use the root safety defaults: read current state, show exact command and impact, then ask for explicit confirmation for the single target. For resource-specific details, route to `cli-operations`, `workload-management`, or `storage-secrets-ingress`.

## Local GPU confusion

**Symptom:** user assumes local CUDA is required because Lepton can launch GPU workloads.

**Clarification:** the `leptonai` package and `lep` CLI are local Python/cloud-control tools. They do not require local CUDA for package import or command planning. GPU shape availability is a remote workspace capacity question and should be checked with authorized Lepton node/resource-shape commands.

## Skill may be stale

Read [repo-provenance.md](repo-provenance.md). Refresh this repo skill when:

- The current package commit differs from the provenance commit.
- The `lep --help` command tree or key flags differ from the bundled references.
- Public Python signatures, entry points, or dependency metadata changed.
- The working tree has source changes affecting `leptonai/`, `pyproject.toml`, README, docs, CLI modules, API modules, or tests.
