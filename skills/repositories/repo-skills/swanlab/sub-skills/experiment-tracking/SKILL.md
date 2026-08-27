---
name: experiment-tracking
description: "Guide SwanLab experiment tracking with safe init/log/finish, run
  lifecycle, scalar/config logging, file saving, async logging, and
  disabled/local/offline smokes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SwanLab Experiment Tracking

Use this sub-skill when the task is to add, debug, or verify ordinary SwanLab experiment tracking code: `swanlab.init`, `swanlab.log`, `swanlab.finish`, `swanlab.run`, `swanlab.get_run`, `swanlab.has_run`, scalar/config logging, `save`, and `async_log`.

## Route here for

- Converting a basic training loop or README-style quick start into credential-safe SwanLab code.
- Choosing `mode="disabled"`, `mode="local"`, or `mode="offline"` for smoke tests, CI, examples, or no-network environments.
- Managing the one-active-run lifecycle, including `reinit=True`, `with swanlab.init(...) as run:`, and safe `finally` blocks.
- Logging scalar metrics and config dictionaries/files without media-specific detail.
- Checking whether an active run exists before logging from utility code.
- Saving matched files with `run.save` / `swanlab.save` and understanding `now`, `end`, and `live` policies at a high level.
- Using `async_log` safely and knowing why forked child processes cannot use the parent run.

## Route elsewhere

- Credentials, API keys, login, custom hosts, settings precedence, or exact mode configuration: `settings-and-modes`.
- Images, audio, video, text objects, HTML, ECharts, molecules, 3D objects, or custom charts: `media-and-custom-charts`.
- Uploading/syncing an offline/local run after training or converting W&B/TensorBoard/MLflow logs: `sync-and-converters`.
- Framework callbacks for Transformers, Lightning, Keras, Ray, FastAI, Stable-Baselines3, etc.: `integrations-and-plugins`.

## Read these references

- API details and current-version caveats: [references/api-reference.md](references/api-reference.md)
- Credential-safe tracking recipes: [references/workflows.md](references/workflows.md)
- Failure diagnosis and fixes: [references/troubleshooting.md](references/troubleshooting.md)

## Safe smoke check

Run the bundled disabled-mode checker from this sub-skill directory after installing SwanLab:

```bash
python scripts/check_disabled_tracking.py
```

The checker imports SwanLab, starts `mode="disabled"`, logs scalar data, finishes the run, and asserts that the active run resets to `None`. It does not require credentials or network access.
