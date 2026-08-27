---
name: app-and-ui
description: "Run and troubleshoot the H2O LLM Studio Wave GUI, app runtime,
  Docker entry points, settings storage, and UI/server lifecycle."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# App and UI

Use this sub-skill when the task is about starting, operating, or debugging the H2O LLM Studio graphical app: H2O Wave launch commands, Docker runtime, browser/service lifecycle, app settings, user database paths, credential persistence, download links, and UI-server connectivity.

## Route here for

- Starting the GUI with `make llmstudio` or a direct `wave run llm_studio.app` command.
- Choosing H2O Wave environment variables for uploads, downloads, reverse proxies, remote access, and timeouts.
- Understanding how the Wave app initializes `q.app`, `q.client`, settings, datasets, and the local SQLite database.
- Locating the persistent `data/` and `output/` directories controlled by `H2O_LLM_STUDIO_WORKDIR`.
- Explaining or troubleshooting keyring, `.env` credential storage, YAML user settings, and settings restore/save behavior.
- Running safe preflight checks before starting a long-lived Wave server.
- Planning optional browser/UI verification with Playwright when a server and browser stack are intentionally available.

## Route elsewhere

- Experiment YAML schema, dataset columns, problem types, and import-format validation: `../configuration-and-data/`.
- Training commands, `train.py`, GPU/DeepSpeed training failures, and experiment artifacts after a run starts: `../training-and-experiments/`.
- Interactive prompting, model download/export, and Hugging Face publishing: `../export-and-prompt/`.
- Model wrapper, loss, metric, inference, and evaluation internals: `../modeling-and-evaluation/`.

## First actions

1. Read [runtime setup](references/runtime-setup.md) for launch commands, runtime-root assumptions, Docker commands, workdir layout, and Wave environment variables.
2. Use the safe checker before starting a service:

   ```bash
   python sub-skills/app-and-ui/scripts/check_app_runtime.py --runtime-root .
   ```

   Add `--prepare-dirs` only when you intentionally want the checker to create missing `data/` and `output/` directories.
3. Read [app architecture](references/app-architecture.md) when diagnosing initialization order, settings persistence, SQLite DB state, default dataset import, or download-link behavior.
4. Read [troubleshooting](references/troubleshooting.md) for common service, browser, remote-origin, keyring, Docker, and filesystem failures.

## Operating reminders

- `make llmstudio` is GPU-oriented and runs `nvidia-smi` before launching Wave. For app-import or UI-layout debugging without proving GPU readiness, use the direct `wave run llm_studio.app` form from the runtime root.
- Run the app from a runtime root containing the package assets expected by the app, not from an arbitrary directory. The app uses relative paths for static assets, Python config modules, prompts, and model-card templates.
- The app stores persistent user data under the resolved H2O LLM Studio workdir, not under Wave's process directory unless those are the same.
- For remote or proxied access, treat browser origin, allowed origins, public base URL, and Wave app timeouts as part of the app configuration, not as training issues.
