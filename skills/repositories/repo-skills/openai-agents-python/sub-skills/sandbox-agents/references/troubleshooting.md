# Troubleshooting Sandbox Agents

Sandbox agents are beta. When behavior differs from an example, inspect installed signatures and prefer the current package's source over old docs.

## Quick Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` for Docker client modules | Docker extra is not installed. | Install `openai-agents[docker]` and ensure the Docker daemon is reachable. |
| Hosted sandbox import fails | Provider extra or extension package is missing. | Install the matching provider extra and configure provider credentials outside manifests/prompts. |
| `UnixLocalSandbox is not supported on Windows` | Unix-local backend guards Windows. | Use Docker or a hosted backend on Windows. |
| Manifest entry path rejected as absolute or escaping root | Entry key used `/...`, Windows absolute syntax, or `..`. | Use workspace-relative keys such as `repo` or `data/input.pdf`. |
| `LocalDirReadError` or `LocalFileReadError` with `outside_base_dir` | Source path is outside the SDK process working directory. | Move the source under the working directory or add a trusted narrow `SandboxPathGrant`. |
| Grant path rejected as root or relative | `SandboxPathGrant` requires absolute non-root paths. | Grant a concrete subdirectory, preferably read-only. |
| Symlink source rejected | Local materialization does not support symlink traversal in copied paths. | Resolve/copy the real files into a safe staging directory first. |
| Users/groups fail on Unix-local | Host account provisioning is intentionally blocked. | Use Docker/hosted backends for account provisioning or omit `users`/`groups`. |
| Mount strategy error | Strategy does not match mount type or backend. | Match entry, strategy, backend, and required in-image binaries. |
| Mounted data missing from snapshot | Mounts are ephemeral and skipped/detached by persistence flows. | Recreate mounts through the manifest when restoring snapshots. |
| Snapshot restore mismatch | Snapshot id/backend/session state does not match current client. | Resume with the original backend state or create a fresh session from a compatible snapshot spec. |
| Archive extraction fails | Archive path traversal, oversized input/extracted data, or too many members. | Validate archive structure and tune `SandboxArchiveLimits` only for trusted data. |
| `apply_patch` edits wrong path | Patch paths are workspace-root-relative, not shell `cwd`-relative. | Prefix paths with the workspace entry, such as `repo/src/app.py`. |

## Optional Extras

Base install imports `SandboxAgent`, `Manifest`, `GitRepo`, and `UnixLocalSandboxClient`. Docker and hosted backends are optional.

- Docker: install `openai-agents[docker]`, have Docker running, and choose `DockerSandboxClientOptions(image=...)`.
- Hosted providers: install the provider extra, configure credentials in trusted application config, and use provider-specific mount strategies from extension modules.
- Voice imports are unrelated to sandbox agents and require `openai-agents[voice]`.

Do not put API keys or cloud credentials in public skill content, prompts, or generated manifest examples.

## Host Filesystem Boundaries

The sandbox workspace root and `extra_path_grants` are the host/filesystem boundary controls.

- Manifest entry keys must stay relative to the workspace.
- `LocalFile.src`, `LocalDir.src`, and lazy local skill sources read from the SDK host.
- Sources outside the SDK process working directory require an explicit grant.
- Grants must be trusted application decisions, never model-authored configuration.
- Read-only grants are safer for source material and skills.
- Filesystem-root grants are rejected; broad grants like a home directory are still unsafe even if accepted.

For untrusted manifest JSON, run the bundled validator first:

```bash
python skills/openai-agents-python/sub-skills/sandbox-agents/scripts/validate_manifest.py manifest.json --json
```

The helper validates parseability and warns on risky local sources, writeable grants, broad host paths, absolute entry keys, and remote mounts.

## Remote Mount Policy

Remote mounts combine provider credentials, a mount entry, a strategy, and backend support. Failures usually come from one of these layers.

- Check that the mount type supports the chosen strategy.
- For in-container strategies, check that required binaries exist in the image.
- For Docker volume strategies, check Docker volume driver support on the host.
- For hosted clients, use the provider-specific strategy documented for that backend.
- Keep mounts read-only unless write-back is required and reviewed.
- Remember mounts are ephemeral; snapshots should restore workspace files, not persist mounted remote storage.

When remote mounts are not essential, materialize a small fixture through `File`, `Dir`, `LocalFile`, or `LocalDir` for safer deterministic runs.

## Archive and Materialization Failures

Workspace archive extraction and snapshot restore can fail before the agent runs.

- Path traversal entries or unsafe tar members are rejected.
- `SandboxArchiveLimits` can enforce max input bytes, extracted bytes, and member count.
- Local snapshot ids must be a single path segment because local snapshots persist as `<id>.tar`.
- Local directory materialization recursively copies regular files and rejects unsupported symlink paths.
- If a manifest needs many files, prefer a narrow `LocalDir` source and review concurrency limits instead of granting a parent tree.

## Permission and User Issues

- `Permissions` maps to POSIX modes for materialized entries where supported.
- Docker/hosted backends can support users/groups depending on implementation.
- Unix-local rejects manifest `users` and `groups` to avoid host mutation.
- `run_as` controls model-facing sandbox tool user identity; it does not replace backend account provisioning.
- Mount permissions are not a reliable access-control boundary; enforce remote storage permissions at the provider.

## Snapshot and Session Mismatch

Distinguish these sources:

- Live session: pass `SandboxRunConfig(session=sandbox)` and keep the session open.
- Serialized sandbox state: pass `SandboxRunConfig(session_state=state)` to let the client resume or recreate.
- Snapshot spec/base: pass `snapshot=...` for fresh sessions seeded from saved workspace contents.
- Runner-managed pause/resume: use `RunState` to carry sandbox state with model/run state.

If the original backend sandbox no longer exists, a client may hydrate a replacement from state snapshot data. If no restorable snapshot exists, start a fresh session and reapply the manifest.

## Beta API Drift

Sandbox APIs are marked beta. Guard generated examples against drift:

- Import from public modules first: `agents.sandbox`, `agents.sandbox.entries`, `agents.sandbox.capabilities`, and backend modules under `agents.sandbox.sandboxes`.
- Validate current signatures with `inspect.signature` when maintaining code that wraps constructors.
- Keep `SKILL.md` router-like and detailed API tables in references so future refreshes can update evidence in one place.
- Treat docs/examples from older versions as patterns, not contracts.
