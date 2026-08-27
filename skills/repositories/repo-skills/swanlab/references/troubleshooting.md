# Cross-Cutting Troubleshooting

Read this for SwanLab install/import, CLI, credentials, network, optional dependency, and mode issues before diving into a specific workflow.

## Import or version problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'swanlab'` | Target environment does not have SwanLab installed. | Install with `pip install swanlab`, then run `python -c "import swanlab; print(swanlab.__version__)"`. |
| Import works in one shell but not another | The wrong Python interpreter or environment is active. | Run `python -c "import sys; print(sys.executable)"` in the same shell where the task runs, then install there. |
| Rich media class fails but `import swanlab` works | Optional `media` extra dependency is missing. | Install `swanlab[media]` or use a lightweight object such as `Text`, `Html`, or scalar logging. |
| Framework adapter import error names `transformers`, `lightning`, `keras`, `xgboost`, etc. | SwanLab base install omits the optional training framework. | Install the framework stack in the training environment; read [../sub-skills/integrations-and-plugins/SKILL.md](../sub-skills/integrations-and-plugins/SKILL.md). |
| `swanlab watch`/dashboard cannot start | Dashboard extra or dashboard service dependency is missing. | Install `swanlab[dashboard]` and validate the chosen local port. |

## CLI command not found

- Try `python -m swanlab --help`; if that works but `swanlab --help` does not, the environment's scripts directory is not on `PATH`.
- Use [../scripts/check_swanlab_cli.py](../scripts/check_swanlab_cli.py) for a no-network help check.
- If a CLI subcommand waits for input, check whether the task is non-interactive. Use explicit options or route credential setup to an interactive operator.

## Credentials and hosts

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No API key` or blank API-key error | Cloud/Open API/sync workflow needs credentials. | Use `swanlab login`, pass an explicit key to the API client, or switch the training smoke to `mode="disabled"`, `mode="offline"`, or `mode="local"`. |
| `Host cannot be empty` | Empty string was passed for host/API/web host. | Omit the field to use defaults or pass a real base URL. |
| Links point to the wrong cloud/self-hosted site | `api_host` and `web_host` are mismatched or stale credentials were reused. | Configure both hosts intentionally and avoid reusing credentials across hosts. Read [../sub-skills/settings-and-modes/SKILL.md](../sub-skills/settings-and-modes/SKILL.md). |
| Network/upload fails after local logging succeeds | Service endpoint, credentials, proxy, or server status issue. | Keep local/offline records intact, verify host/API key, then retry sync with a small run first. |

Never print, store in prompts, or upload API keys, tokens, webhook URLs with secrets, SMTP passwords, cookies, or presigned URLs.

## Mode confusion

- `online`: intended for live cloud/self-hosted upload and normally needs credentials/network.
- `offline`: writes local logs for later sync.
- `local`: writes local logs for local/dashboard viewing.
- `disabled`: exercises code paths without creating upload-oriented side effects; best for safe smoke tests and examples without credentials.

If a README-style cloud snippet fails due missing credentials, translate it to `mode="disabled"` first, then separately handle login/host setup.

## Run lifecycle errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `swanlab.run is None` before logging | No active run, or the run has been finished. | Call `swanlab.init(...)` before logging, or guard with `swanlab.has_run()`. |
| Logging fails after `finish()` | Normal lifecycle reset. | Reinitialize a new run or move the log call before finish. |
| Double finish warning | The active run already ended. | Treat finish as idempotent in cleanup, but do not assume more logs will be accepted. |
| Disabled smoke creates unexpected files | The code may not be in disabled mode, or other callbacks/plugins write files. | Use [../scripts/swanlab_disabled_smoke.py](../scripts/swanlab_disabled_smoke.py) to isolate base tracking. |

## Optional backend and hardware claims

Base SwanLab import does not prove any of these:

- CUDA/ROCm/MPS or vendor accelerator training;
- real hardware monitoring values from a device;
- distributed rank-zero behavior in a framework;
- rich media conversion for every file type;
- dashboard service startup;
- cloud/self-hosted upload.

Only claim these surfaces are verified after a task-specific environment runs a tiny representative case.
