# Runtime troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `potpie: command not found` | CLI is not installed or not on PATH. | Install with `uv tool install potpie` or activate the intended Python environment and use `python -m pip install potpie`; then rerun `potpie --help`. |
| `potpie --help` crashes during import | Missing or incompatible package dependency. | Run `python -m pip check`; repair the missing direct dependency, then repeat `potpie --help` and `potpie daemon status`. |
| `potpie daemon status` reports `up=False` | No detached daemon is running. | Start it with `potpie daemon start` in the intended session or run `potpie setup`; only then retry daemon-dependent commands. |
| `potpie status`, `doctor`, `backend list`, or `skills status` reports `unavailable` | CLI import succeeded, but daemon RPC is unavailable. | Do not reinstall first. Check `potpie daemon status`, daemon logs, backend profile, and port/socket conflicts. |
| Setup mutates more than expected | Running setup without preview can bind repos, install agent skills, or start runtime components. | Use `potpie setup --dry-run` first; add explicit repo/agent/scope flags; route pot/source choices to `workspace-boundaries` and skill installs to `skills-management`. |
| Backend commands fail after switching profile | External service or optional dependency is missing. | Return to the known local profile or install/configure the selected backend service intentionally. Do not treat a CPU smoke as proof of an external Neo4j/Postgres/FalkorDB service. |
| UI does not open | Daemon/backend is stopped, the UI build is unavailable, or the expected local port is occupied. | Check `potpie daemon status`, `potpie ui --help`, daemon logs, and the browser URL. In a source checkout, refresh with the repo's UI/build path if needed. |
| Telemetry command fails | Local config cannot be read/written or Sentry setup is incomplete. | Use `potpie telemetry --help` and inspect local config permissions; telemetry is not required for graph read/write correctness. |

## Install/import triage

1. Confirm the Python executable that owns `potpie` is the intended one: `which potpie` and `potpie --version`.
2. Check entry point import: `potpie --help`.
3. Check public context APIs: `python ../../scripts/typecheck_public_context_api.py` from this sub-skill directory, or run the root helper from the generated skill root.
4. Run `python -m pip check` only inside the environment you intend to repair.
5. If an editable source install is present, ensure the root package, context-core, and context-engine are all updated together.

## Daemon triage

1. `potpie daemon status`
2. `potpie daemon logs` if available and the daemon attempted to start.
3. Confirm backend profile and required local service.
4. Retry `potpie status` and `potpie doctor`.
5. If daemon commands still fail but `potpie --help` works, capture the structured error and avoid destructive resets unless the user approves.

## Backend triage

- `falkordb_lite` is the local default profile and should be the first recovery target for ordinary local use.
- `in_memory` is useful for isolated or test-style sessions when persistence is not needed.
- `neo4j`, `postgres`, `falkordb`, `chroma`, or `hosted` can require services, URLs, credentials, ports, or optional packages.
- GPU availability is not a prerequisite for the CLI/runtime workflows covered by this generated skill.
