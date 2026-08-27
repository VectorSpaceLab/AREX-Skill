# SwanLab Configuration Reference

This reference covers `swanlab.Settings`, `swanlab.merge_settings`, `swanlab.require`, configuration source precedence, host normalization, and safe terminal/probe settings. Use `modes-and-credentials.md` for login and mode recipes, and `troubleshooting.md` for failure diagnosis.

## Public configuration entry points

| Entry point | Use | Timing |
| --- | --- | --- |
| `from swanlab import Settings` | Build a validated configuration object. | Safe before `swanlab.init`; construction should not create log directories or credentials. |
| `swanlab.merge_settings(settings_or_dict)` | Merge settings into the process-global SwanLab settings snapshot. | Must be called before a run is active. |
| `swanlab.init(..., settings=Settings(...))` | Apply per-run advanced settings while explicit `init` kwargs still have highest run-time priority. | At run creation. |
| `swanlab.require("core_python", "probe_python")` | Select transitional core/probe backend implementations. | Must be called before a run is active. |
| `Settings(...).to_yaml(...)` | Render config as YAML without writing files. | Safe inspection. |
| `Settings(...).save_to_yaml(target_dir, ..., merge=True)` | Persist selected fields to `config.yaml`; creates `target_dir` and merges with an existing file by default. | Intentional config write only. |

## `Settings` top-level fields

`Settings` is a Pydantic settings model. The stable user-facing keyword fields are:

| Field | Default / accepted values | Notes |
| --- | --- | --- |
| `interactive` | `True` | Controls prompts. Set `False` for CI, batch jobs, and non-TTY execution. |
| `mode` | `"online"`; also `"offline"`, `"local"`, `"disabled"`; legacy `"cloud"` maps to `"online"` | Use `disabled` for no-write/no-network checks, `offline` for local records to sync later, `local` for local dashboard behavior, and `online` for cloud upload. |
| `log_dir` | current directory plus `swanlog` | A path value. If the path already exists and is not a directory, validation fails. `Settings` construction does not create it. Non-disabled `init` creates run directories; disabled mode should not. |
| `api_key` | `None` | Used by online login/sync/API flows. Do not hard-code real keys in reusable code. |
| `api_host` | `https://api.swanlab.cn` | Base API host. Host normalization strips paths/query, preserves port, and adds `https://` when missing. |
| `web_host` | `https://swanlab.cn` | Display/browser host for run URLs and prompts. It does not drive SDK HTTP requests. |
| `project` | `Settings.Project(...)` | Project name, workspace, and public visibility. |
| `experiment` | `Settings.Experiment(...)` | Experiment name/color/description/tags/group/job type. |
| `run` | `Settings.Run(...)` | Run id, resume policy, parallel mode, config path, directory naming. |
| `terminal` | `Settings.Terminal(...)` | Terminal log proxy behavior. |
| `integration` | `Settings.Integration(...)` | Webhook and local dashboard settings. |
| `core` | `Settings.Core(...)` | Upload batching and record/file size controls. |
| `probe` | `Settings.Probe(...)` | Hardware/runtime/dependency/Git/SwanLab metadata and monitor controls. |

Example with safe, private-friendly defaults:

```python
import swanlab
from swanlab import Settings

settings = Settings(
    mode="offline",
    interactive=False,
    api_host="https://swanlab.example.internal/api/v1",
    web_host="https://swanlab.example.internal",
    probe=Settings.Probe(
        hardware=False,
        requirements=False,
        git=False,
        monitor=False,
    ),
    terminal=Settings.Terminal(proxy_type="none"),
)

swanlab.merge_settings(settings)  # call before swanlab.init()
```

## Nested settings quick reference

### `Settings.Project`

| Field | Notes |
| --- | --- |
| `name` | Optional project name. If omitted in `swanlab.init`, the current directory name is used as the run project. |
| `workspace` | Optional workspace/organization. |
| `public` | Boolean visibility flag for online projects. |

Legacy environment fallbacks include `SWANLAB_PROJ_NAME`, `SWANLAB_WORKSPACE`, and `SWANLAB_PUBLIC`.

### `Settings.Experiment`

| Field | Notes |
| --- | --- |
| `name`, `color`, `description`, `group`, `job_type` | Optional run metadata. Color must be a hex color such as `#00AAFF`. |
| `tags` | List of tags; string values may be JSON lists or comma-separated. Maximum tag count is 30. |

Useful environment forms include nested names such as `SWANLAB_EXPERIMENT_TAGS` and legacy names such as `SWANLAB_EXP_NAME`, `SWANLAB_EXP_COLOR`, `SWANLAB_DESCRIPTION`, `SWANLAB_TAGS`, `SWANLAB_GROUP`, and `SWANLAB_JOB_TYPE`.

### `Settings.Run`

| Field | Notes |
| --- | --- |
| `id` | Optional run id. `online` with `resume="must"` requires it; `online` with `resume="never"` must not provide it. |
| `resume` | One of `"must"`, `"allow"`, `"never"`. Boolean-like values map as `true/yes/1 -> "allow"` and `false/no/0 -> "never"`. |
| `parallel` | `"none"` or `"shared"`. Non-`none` parallel mode forces `resume="allow"`. |
| `history` | Optional path for previous run history. |
| `config` | Optional JSON/YAML config file path loaded into `run.config` after initialization. |
| `dir` | Optional exact run directory name. |
| `dir_max_length` | 50-255; bounds generated or explicit run directory length. |
| `dir_create_retries` | At least 1; number of unique-name retries when creating run directories. |

### `Settings.Terminal`

| Field | Default | Notes |
| --- | --- | --- |
| `proxy_type` | `"all"` | One of `"all"`, `"stdout"`, `"stderr"`, `"none"`. Use `"none"` when console capture is unwanted. |
| `max_length` | `1024` | Per-line terminal capture limit, between 500 and 4096 characters. |

### `Settings.Integration`

| Field | Notes |
| --- | --- |
| `webhook.url`, `webhook.value`, `webhook.timeout` | Notification webhook settings. Legacy env vars include `SWANLAB_WEBHOOK`, `SWANLAB_WEBHOOK_VALUE`, and `SWANLAB_WEBHOOK_TIMEOUT`. |
| `dashboard.host`, `dashboard.port` | Local dashboard host and port. Legacy env vars include `SWANLAB_DASHBOARD_HOST` and `SWANLAB_DASHBOARD_PORT`; port must be 1-65535. |

### `Settings.Core`

| Field | Default | Notes |
| --- | --- | --- |
| `section_rule` | `0` | Slash index used to split metric keys into section/name. New env var `SWANLAB_CORE_SECTION_RULE` overrides legacy `SWANLAB_SECTION_RULE_IDX`. |
| `record_batch` | `10000` | Records per HTTP request; must be >0 and <100000. |
| `record_interval` | `1.5` | Upload thread batch interval in seconds; must be >0. |
| `save_split` | `100 MiB` | Multipart upload threshold. |
| `save_size` | `50 GiB` | Maximum saved size per file. |
| `save_part` | `32 MiB` | Multipart upload part size. |
| `save_batch` | `100` | Maximum number of files per save upload batch. |

### `Settings.Probe`

| Field | Default | Notes |
| --- | --- | --- |
| `hardware` | `True` | Static hardware snapshot. If `hardware=False` while `monitor=True`, monitor may still access hardware to compute dynamic metrics, but the static snapshot is discarded and not persisted. |
| `runtime` | `True` | Captures OS, Python, hostname, current working directory, and launch command. Disable for privacy-sensitive runs. |
| `requirements` | `True` | Captures Python package versions, similar to `pip freeze`. |
| `conda` | `False` | Captures Conda environment metadata when enabled; can add startup overhead. |
| `git` | `True` | Captures branch, commit, and remote metadata. |
| `swanlab` | `True` | Captures SwanLab version and run directory metadata. |
| `monitor` | `True` | Enables periodic hardware utilization monitoring. |
| `monitor_interval` | `10` | Must be at least 5 seconds. |
| `monitor_disk_dir` | system root directory | Must be an existing directory because it is validated as a directory path. |

## Configuration source precedence

When building `Settings()`, higher-priority values override lower-priority values. The observed source order is:

1. Explicit constructor values, including objects passed through `merge_settings` or `init(..., settings=...)`.
2. `swanlab.yaml` or `swanlab.yml` in the current working directory.
3. YAML files under `SWANLAB_CONFIG_DIR` or the default system config directory, loaded in reverse filename order.
4. Current-directory `.env`.
5. Secret files from `SWANLAB_SECRETS_DIR` and Pydantic file-secret sources. Secret filenames use field names such as `api_key`.
6. Environment variables with the `SWANLAB_` prefix.
7. Current-directory `.swanlab/config.yaml` or `.swanlab/config.yml`.
8. User configuration root `config.yaml` or `config.yml`.
9. Model defaults.
10. `.netrc` credential fallback for `api_key`, `api_host`, and `web_host` when those fields were not explicitly set and the stored host matches the selected API host.

Practical consequences:

- A `swanlab.yaml` in the current working directory can override environment variables. Check it first when CI or notebooks ignore an expected `SWANLAB_*` value.
- `SWANLAB_API_KEY` overrides `.swanlab/config.yaml`, but not a current-directory `swanlab.yaml`, `.env`, or configured secret file.
- CLI mode commands write lower-priority config files; a higher-priority env var or `swanlab.yaml` can make a CLI mode change appear ineffective.
- `SWANLAB_CONFIG_DIR` and `SWANLAB_SECRETS_DIR` are read when the settings module is imported. Set them before starting the Python process.

Common environment variables:

| Setting | Environment examples |
| --- | --- |
| Mode and interaction | `SWANLAB_MODE`, `SWANLAB_INTERACTIVE` |
| Credentials/hosts | `SWANLAB_API_KEY`, `SWANLAB_API_HOST`, `SWANLAB_WEB_HOST` |
| User config root | `SWANLAB_ROOT`, legacy `SWANLAB_SAVE_DIR` |
| Logging | `SWANLAB_LOG_DIR`, legacy `SWANLAB_LOGDIR` |
| Project | `SWANLAB_PROJECT_NAME`, legacy `SWANLAB_PROJ_NAME`; `SWANLAB_PROJECT_WORKSPACE`, legacy `SWANLAB_WORKSPACE`; `SWANLAB_PROJECT_PUBLIC`, legacy `SWANLAB_PUBLIC` |
| Experiment | `SWANLAB_EXPERIMENT_NAME`, `SWANLAB_EXPERIMENT_TAGS`, plus legacy `SWANLAB_EXP_NAME`, `SWANLAB_TAGS`, etc. |
| Run | `SWANLAB_RUN_ID`, `SWANLAB_RUN_RESUME`, legacy `SWANLAB_RESUME`, `SWANLAB_RUN_DIR` |
| Terminal/probe | `SWANLAB_TERMINAL_PROXY_TYPE`, `SWANLAB_PROBE_MONITOR`, `SWANLAB_PROBE_HARDWARE`, `SWANLAB_PROBE_REQUIREMENTS` |
| Integration legacy shorthands | `SWANLAB_WEBHOOK`, `SWANLAB_WEBHOOK_VALUE`, `SWANLAB_WEBHOOK_TIMEOUT`, `SWANLAB_DASHBOARD_HOST`, `SWANLAB_DASHBOARD_PORT` |
| Transitional backend selection | `SWANLAB_REQUIRE=core,probe` or `SWANLAB_REQUIRE=core_python,probe_python` |

## `merge_settings` behavior

Use `swanlab.merge_settings(...)` before `swanlab.init()` to change process-global defaults:

```python
import swanlab
from swanlab import Settings

swanlab.merge_settings({
    "mode": "offline",
    "probe": {"monitor": False},
    "terminal": {"proxy_type": "none"},
})

# Settings objects are also accepted. Only explicitly set fields are merged.
swanlab.merge_settings(Settings(log_dir="./runs"))
```

Important rules:

- `merge_settings` is guarded against active runs. Finish the active run before changing global settings.
- Dict merges are deep for nested settings: `{"probe": {"monitor": False}}` keeps `probe.monitor_interval` and other probe fields intact.
- Merging a `Settings` object uses only fields explicitly set on that object; defaults should not wipe existing settings.
- Merging `{"api_host": "https://host.example/api"}` without `web_host` re-derives `web_host` from the API host. Merging both fields keeps them distinct.
- All normal validation still applies. A bad mode, invalid port, existing non-directory `log_dir`, or too-short `probe.monitor_interval` raises during merge.

## Host normalization

`api_host` and `web_host` are normalized by the same host formatter:

- Leading/trailing whitespace is stripped.
- Empty or all-whitespace host strings raise `ValueError("Host cannot be empty or whitespace.")`.
- Missing schemes default to `https://`.
- Paths, query strings, and trailing slashes are removed.
- Ports are preserved.
- `http://api.swanlab.cn/...` and `http://swanlab.cn/...` normalize to the official `https://` defaults.
- Providing only `api_host` derives `web_host` from it, except official API host values keep the official web host.
- Providing only `web_host` keeps the default official `api_host`.

Examples:

```python
from swanlab import Settings

Settings(api_host="custom.example.com/api/v1").api_host
# "https://custom.example.com"

Settings(api_host="http://api.local/v1/", web_host="http://web.local/").web_host
# "http://web.local"
```

## `swanlab.require` backend selection

`require` selects transitional process-global implementations for core/probe internals. It is not a package installer and does not prove hardware availability.

```python
import swanlab

swanlab.require("core_python", "probe_python")  # explicit built-in Python implementations
# swanlab.require("core")   # selects the Go core backend when that backend is installed and desired
# swanlab.require("probe")  # selects the Rust probe backend when that backend is installed and desired
```

Rules:

- Call before `swanlab.init()`; it is blocked while a run is active.
- Valid tokens are `core`, `probe`, `core_python`, and `probe_python`.
- Unknown tokens passed to `swanlab.require(...)` raise `ValueError`.
- `SWANLAB_REQUIRE` can contain comma-separated tokens and is applied at import time. Set it before launching Python.
- Keep the Python defaults unless the target environment intentionally installed and selected the alternate backend.
