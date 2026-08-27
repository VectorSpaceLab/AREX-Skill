# Troubleshooting

## When to read

Use this for cross-cutting Solace Agent Mesh install/import/build/service issues. For workflow-specific failures, also read the nearest sub-skill troubleshooting file.

## Install and import problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `sam: command not found` | The `solace-agent-mesh` distribution is not installed in the active environment or the environment's scripts directory is not on `PATH`. | Run `python scripts/check_install.py`; install `solace-agent-mesh`; invoke with the environment's console entry point. |
| `ModuleNotFoundError: solace_agent_mesh.cli` after local editable install | The packaged CLI files are force-included into wheels; editable installs can expose a different layout than the packaged wheel. | Prefer a normal package/wheel install for operating checks. In repo-development contexts, use the repository's test `pythonpath` conventions rather than treating editable CLI behavior as packaged behavior. |
| Package build complains about missing frontend/docs assets | The build hook needs Config Portal, Web UI, and docs static assets unless told to skip and assets already exist. | For release-like local builds, ensure Node/npm frontend builds complete or use the package's documented skip behavior only when static assets are already present. Do not run frontend builds as a dry skill validation step. |
| `pip check` reports `pydantic` or `rich` conflicts after installing `sam-rest-client` with the main package | `sam-rest-client` pins versions that differ from the main `solace-agent-mesh` pins. | Install `sam-rest-client` in a separate environment, or choose one package surface per environment. Root helper `scripts/check_install.py --include-rest-client` can check whichever environment includes the client. |
| Import succeeds from a repository checkout but fails from another directory | The checkout path is masking a missing or broken package install. | Run import checks from outside the checkout and use `python scripts/check_install.py`. |

## CLI and config errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Unknown command or option | Package version differs from this skill or command family changed. | Check `sam --version`, `sam --help`, and `references/repo-provenance.md`; refresh the skill if command help differs. |
| YAML parser errors | Invalid indentation, anchors, or templated values. | Parse with a safe YAML parser first; use sub-skill validators for projects/workflows/evaluation. |
| Environment placeholders remain unresolved at runtime | `.env` not loaded, wrong env file, or missing process variables. | Inspect `.env`, `configs/shared_config.yaml`, and command flags; separate dry placeholders from values required for live service calls. |
| Invalid agent/component name | CLI name validators require safe alphanumeric/underscore identity fields and normalized filesystem names. | Normalize the name and re-run project/plugin inspectors before writing. |

## Runtime service issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `sam run` starts but no tasks complete | Broker, namespace, LLM provider, or gateway config is wrong; agent discovery may not be ready. | Use `runtime-operations` guidance; inspect logs and configs; verify broker and model credentials before retrying. |
| `sam task send` timeout | Gateway unreachable, wrong URL/port, target agent unavailable, task still running, or task timeout too low. | Run `sub-skills/runtime-operations/scripts/check_gateway.py` for GET probes; confirm the target agent name and timeout separately. |
| REST client returns auth or 404 errors | Wrong base URL, token, API version, namespace, or gateway not serving REST endpoints. | Use `runtime-operations/references/rest-client.md`; check `sam-rest-cli --help`; verify URL without submitting tasks first. |
| Browser-based command hangs or cannot open browser | Headless environment, port conflict, firewall, or frontend assets missing. | Use non-GUI CLI mode when possible; pass explicit host/port where supported; inspect generated files rather than assuming the browser completed setup. |

## Storage, databases, and artifacts

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| SQLite database file cannot be created | Project data directory missing or permissions issue. | Validate project tree with `project-bootstrap/scripts/inspect_project.py`; create data directory or choose a writable database URL. |
| PostgreSQL/S3/GCS failures | Credentials, endpoint, region, bucket, or network not available. | Treat as live external-service verification; do not mark dry validation as proof. Confirm env vars and minimal connectivity separately. |
| Artifacts not available to the model or UI | Artifact service type/scope or artifact handling mode does not match intended behavior. | Review `configuration-concepts.md` and `project-bootstrap` references; choose `ignore`, `embed`, or `reference` intentionally. |

## Sub-skill handoff map

- Project layout, `sam init`, `sam add`, component names, artifact/session/database defaults: `sub-skills/project-bootstrap/references/troubleshooting.md`.
- Plugin metadata, installer commands, catalog/browser/server, build outputs, target overwrites: `sub-skills/plugin-lifecycle/references/troubleshooting.md`.
- `sam run`, `sam task`, REST gateway/client, docs/tools: `sub-skills/runtime-operations/references/troubleshooting.md`.
- Workflow DAG/node/template/schema validation: `sub-skills/workflow-authoring/references/troubleshooting.md`.
- Evaluation config/test-case/result/scorer issues: `sub-skills/evaluation/references/troubleshooting.md`.

## Stop conditions

Stop and ask for missing user/environment input instead of guessing when:

- A command would install or uninstall packages in a user-owned environment.
- A live command needs broker, LLM, database, cloud storage, auth, or REST credentials that are not supplied.
- A plugin install/build source is ambiguous or would overwrite project files.
- An evaluation run would submit real prompts or artifacts without user confirmation.
- Public command help or schema facts differ from this skill's provenance snapshot.
