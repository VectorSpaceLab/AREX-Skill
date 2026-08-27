---
name: settings-and-modes
description: "Configure SwanLab settings, modes, credentials, hosts, login,
  require, and safe probe/terminal behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SwanLab Settings and Modes

Use this sub-skill when the task is about SwanLab configuration rather than experiment logging itself: `Settings`, `swanlab.merge_settings`, `swanlab.require`, run modes, login, credential storage, API/web hosts, environment/YAML/secret precedence, terminal capture, and environment or hardware probe boundaries.

## Route here for

- Choosing `online`, `offline`, `local`, or `disabled` mode for code, CLI defaults, CI, examples, or no-network environments.
- Constructing `swanlab.Settings(...)` or nested settings such as `Settings.Probe(...)`, `Settings.Terminal(...)`, `Settings.Run(...)`, and `Settings.Integration(...)`.
- Merging process-global settings before a run with `swanlab.merge_settings(...)`.
- Explaining `swanlab login`, `swanlab.login(...)`, `swanlab verify`, `swanlab logout`, local versus root credential saves, and non-interactive login.
- Configuring `api_key`, `api_host`, `web_host`, self-hosted/custom hosts, and host normalization.
- Diagnosing configuration source precedence across explicit kwargs, `swanlab.yaml`, `.env`, secrets, environment variables, per-directory config, user config, and netrc fallback.
- Disabling or bounding terminal proxying and probe collection for privacy, reproducibility, or optional hardware failures.
- Selecting transitional backend implementations with `swanlab.require(...)` or `SWANLAB_REQUIRE`.

## Route elsewhere

- Training-loop instrumentation, `swanlab.init`, `swanlab.log`, `finish`, scalar/config logging workflows, active run lifecycle, save policies, and async logging: `experiment-tracking`.
- Media objects, custom charts, image/audio/video/text/html/ECharts/molecule/3D details, and rich media optional dependencies: `media-and-custom-charts`.
- Uploading an offline/local run, validating run directories for sync, or converting W&B/TensorBoard/MLflow records: `sync-and-converters`.
- Object-oriented `swanlab.Api` calls and the `swanlab api ...` CLI surface: `open-api-and-cli`.
- Framework callbacks, notification plugins, CSV callbacks, and third-party integration imports: `integrations-and-plugins`.

## Read these references

- Settings fields, precedence, merge behavior, and probe/terminal controls: [references/configuration.md](references/configuration.md)
- Mode selection, login, credential storage, host handling, and self-hosted cautions: [references/modes-and-credentials.md](references/modes-and-credentials.md)
- Configuration and login failure diagnosis: [references/troubleshooting.md](references/troubleshooting.md)

## Safe local check

After SwanLab is installed, run the bundled checker to validate the local package behavior this sub-skill depends on:

```bash
python skills/disco/swanlab/sub-skills/settings-and-modes/scripts/check_settings_modes.py
```

The checker uses temporary directories, clears `SWANLAB_*` variables inside its process, performs disabled-mode and settings/merge assertions, and never uses credentials or network access.
