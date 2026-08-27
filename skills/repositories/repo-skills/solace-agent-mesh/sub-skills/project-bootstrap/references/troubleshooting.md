# Project bootstrap troubleshooting

Use this reference when `sam init` / `sam add` output is missing, surprising, or unsafe to run. Keep diagnosis file-based until a runtime sub-skill is explicitly selected.

## First dry checks

Run the bundled inspector from the generated skill tree:

```bash
python sub-skills/project-bootstrap/scripts/inspect_project.py path/to/sam-project
```

Then inspect the reported files before rerunning generators that might overwrite user edits.

## Symptom-to-fix map

| Symptom | Likely cause | Dry fix |
| --- | --- | --- |
| `sam init` created files in the wrong place | The CLI always targets the current working directory. | Move into the intended empty project directory before rerunning. If files were generated in a parent directory, back them up and clean manually. |
| Invalid orchestrator agent name | `sam init --agent-name` accepts only letters, numbers, and underscores. | Use a name like `OrchestratorAgent` or `Main_Orchestrator_1`; avoid hyphens and spaces for the initial orchestrator. |
| Component file name differs from input | Add commands normalize names into snake/Pascal/kebab forms. | Use the normalized file stem: `my-agent` becomes `configs/agents/my_agent_agent.yaml` or `src/my_agent/`. |
| Generated YAML still contains `__PLACEHOLDER__` tokens | A template was not fully processed or a partial file was copied. | Recreate the affected component from the CLI or replace the unresolved field with a concrete value. The inspector flags these tokens. |
| `!include ../shared_config.yaml` fails later | Component YAML moved without adjusting include path, or `configs/shared_config.yaml` is missing. | Keep app YAML under `configs/agents/`, `configs/gateways/`, or `configs/services/` with the relative include path intact; otherwise update the include path deliberately. |
| `*planning_model`, `*general_model`, or another alias is undefined | No model provider was selected, or `shared_config.yaml` does not define that model anchor. | Either choose/configure models in the UI workflow, add matching model anchors to `shared_config.yaml`, or remove the `model: *...` line if the component is intended to rely on dynamic model configuration. |
| `sam add agent --session-service-type memory` still emits SQL | Current CLI collection path normalizes new agents to SQL session service before writing. | Edit the generated YAML deliberately or use a GUI/direct configuration path that supplies the desired session block. Preserve project SQL requirements if using Projects UI features. |
| Project features are not visible in the UI | Projects require SQL persistence; memory session service disables project endpoints. | Ensure Web UI/orchestrator session services use `type: "sql"` with valid `database_url`; avoid disabling `projects.enabled` or `frontend_feature_enablement.projects`. |
| Web UI gateway missing | Init ran with Web UI disabled or the portal did not submit data. | Rerun init in a clean directory with Web UI enabled, or add `configs/gateways/webui.yaml` and `configs/services/platform.yaml` from a controlled scaffold. |
| Platform service missing while Web UI exists | Partial initialization or manual file deletion. | Recreate `configs/services/platform.yaml` or rerun initialization in a clean directory and compare. Web UI `platform_service.url` should match `PLATFORM_SERVICE_URL`. |
| `requirements.txt` missing or unexpected | Project files step failed or was overwritten. | Regenerate in a clean project or add a requirements file with the SAM package version expected by the environment. |

## GUI and configuration portal issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Browser did not open | Browser automation failed. | Open `http://127.0.0.1:5002` manually for init, `http://127.0.0.1:5002/?config_mode=addAgent` for adding an agent, or `http://127.0.0.1:5002/?config_mode=addGateway` for adding a gateway. |
| Portal cannot start | Port `5002` already in use, packaged frontend missing, or Flask import failed. | Stop the process on port `5002`, reinstall a packaged SAM distribution that includes the portal frontend, and retry. |
| CLI resumes with no data | Portal closed, aborted, or submitted incomplete data. | Rerun the command; verify the portal reports successful save before closing. |
| Portal starts on a host that cannot be reached from the browser | Host binding mismatch. | The backend honors a `CONFIG_PORTAL_HOST` environment override. Use it only when you understand the local networking implications. |
| GUI route gives frontend/static errors | Installed package may not include built frontend assets. | Reinstall the packaged wheel or use a distribution image that includes the portal frontend. |

## Existing files and overwrites

| Case | Behavior | Safer action |
| --- | --- | --- |
| Re-adding an agent with the same name | Target YAML can be overwritten. | Back up or diff `configs/agents/<name>_agent.yaml` first. |
| Re-adding a gateway interactively | CLI prompts before overwriting conflicting source/config files. | Answer no unless the overwrite is intended. |
| Re-adding a gateway with `--skip` | Existing scaffold can be overwritten without a prompt. | Avoid `--skip` for hand-edited gateways. |
| Re-adding a proxy with the same name | Target proxy YAML can be overwritten. | Back up `configs/agents/<name>_proxy.yaml` first. |

## Database URL issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| SQLite URL rejected or points to an unexpected place | Wrong URL form. | Use `sqlite:///relative.db` or a deliberate absolute SQLite URL. Three slashes are required for file paths. |
| PostgreSQL URL rejected | Wrong scheme or missing driver. | Use `postgresql://user:pass@host:port/dbname`; install SAM with PostgreSQL driver support in the runtime environment. |
| Project/session APIs return not-implemented behavior | Session persistence is not SQL. | Set `session_service.type: "sql"` and a valid `database_url` for Web UI/orchestrator configs. |
| Database env variable not found | YAML references `${NAME_DATABASE_URL}` but `.env` lacks it and no default exists. | Add the variable to `.env` or change the YAML expression to include a safe default. |

## Artifact storage issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Artifact writes fail with permission errors | Filesystem `base_path` is not writable by the runtime user. | Choose a writable path and keep it stable across agents/gateways that share artifacts. |
| Artifacts disappear after restart | `type: "memory"` artifact service. | Use filesystem, GCS, or S3 for durable artifacts. |
| GCS/S3 artifacts fail at runtime | Bucket or credentials missing. | Provide bucket/credential environment values in the runtime environment. The bootstrap inspector only checks shape, not cloud access. |
| Artifacts not shared between components | Mixed `artifact_scope` choices. | Use consistent `namespace` scope for shared artifacts or `app` scope for intentional isolation. |
| Gateway filesystem base path appears wrapped in `${ARTIFACT_BASE_PATH, ...}` | Gateway generator wraps plain paths for environment override support. | This is expected. Ensure `ARTIFACT_BASE_PATH` is set if you want to override the default. |

## Port, frontend, and platform service issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Web UI port conflict | `FASTAPI_PORT` default `8000` is already used. | Change `--webui-fastapi-port` at init or edit `.env` before runtime. |
| Platform API port conflict | `PLATFORM_API_PORT` default `8001` is already used. | Change `--platform-api-port` at init or edit `.env` before runtime. |
| Browser cannot reach Web UI in Docker | FastAPI bound to loopback inside the container. | Set `FASTAPI_HOST="0.0.0.0"` and map the container port. |
| Web UI cannot reach platform service | `PLATFORM_SERVICE_URL` does not match platform host/port or protocol. | Align `.env` `PLATFORM_SERVICE_URL` with `PLATFORM_API_HOST` and `PLATFORM_API_PORT`; use HTTPS only when SSL files are configured. |
| Speech or binary preview features fail | Optional provider keys or LibreOffice are absent. | Disable related frontend feature flags or provide the optional runtime dependencies. |

## Missing templates or packaged CLI modules

If scaffold creation reports missing templates or import failures, the installed package may not include CLI/template assets. Use an installed packaged distribution rather than an incomplete editable checkout. Do not patch generated project files around missing template errors until the CLI package itself can load its templates.

## Generated project structure questions

When the user asks whether a project is ready for a live run, stay within this sub-skill by answering from file evidence:

1. Are required config directories present?
2. Do app YAML files parse after safe include/alias preprocessing?
3. Do includes point to existing files?
4. Are model aliases defined or intentionally absent?
5. Are database and artifact service blocks shaped correctly?
6. Are Web UI and platform files consistent if Web UI is enabled?
7. Are dangerous defaults such as placeholder secrets still present?

If these checks pass, hand off to `runtime-operations` for any actual `sam run`, gateway, task, REST, broker, or LLM behavior.
