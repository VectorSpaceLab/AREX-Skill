# PyCaret Cross-Cutting Troubleshooting

Use this reference when the failure does not clearly belong to one surface yet, or when several surfaces may be involved.

## First decision

- Engine workflow, model registry, event stream, or notebook recipe issue → `sub-skills/engine-workflows/references/troubleshooting.md`.
- FastAPI route, CLI, auth, run lifecycle, storage, or LLM advisory issue → `sub-skills/control-plane-api/references/troubleshooting.md`.
- React/Vite route, form, auth state, or npm issue → `sub-skills/web-ui/references/troubleshooting.md`.
- Docker, queues, secrets, backups, or GPU routing issue → `sub-skills/platform-operations/references/troubleshooting.md`.
- Repository policy, tests, release notes, or kill-list issue → `sub-skills/repo-development/references/troubleshooting.md`.

## Common cross-cutting symptoms

| Symptom | Likely cause | First check |
| --- | --- | --- |
| `ImportError` for `pycaret` | engine package not installed or editable install missing | `python scripts/check_pycaret_stack.py --json` |
| `ImportError` or CLI failure for `pycaret-server` | backend package missing, stale environment, or broken dependencies | `python scripts/check_pycaret_stack.py --json` |
| UI checks fail before a browser opens | Node/npm mismatch or missing `apps/web` install | `cd apps/web && npm install` then rerun the UI sub-skill helper |
| A workflow mentions the wrong surface | the request belongs to another sub-skill | open the root skill and route by task family first |
| Results differ from an earlier session | skill may be stale relative to the repo checkout | compare the checkout to `references/repo-provenance.md` |

## Cross-cutting recovery steps

1. Confirm the task belongs to the intended surface and read the owning sub-skill.
2. Run the bundled helper for that surface instead of guessing from source files.
3. Reinstall only the package surface that failed rather than rebuilding every dependency group.
4. If the root helper reports a mismatch between `pycaret` and `pycaret-server`, fix the package install before debugging the workflow itself.
5. If a task mixes engine and backend behavior, verify the engine surface first, then the backend surface, then the UI or ops surface as needed.

## Safety notes

- Do not hard-code private environment paths into runtime instructions.
- Do not use networked dataset helpers as a smoke test unless the user explicitly expects network access.
- Do not assume GPU support from a CPU-only import check; use the platform-operations or engine sub-skill guidance for any accelerator-specific claim.
