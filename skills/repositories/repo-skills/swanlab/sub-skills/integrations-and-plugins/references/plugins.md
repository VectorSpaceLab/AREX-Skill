# Plugins

Use this reference for SwanLab callbacks that extend a run rather than replacing the base tracking API: notification senders, CSV row writing, and custom callback protocol work.

## Import surface

```python
from swanlab.plugin import (
    CSVWriter,
    LarkCallback,
    DingTalkCallback,
    WeComCallback,
    WXWorkCallback,
    DiscordCallback,
    SlackCallback,
    TelegramCallback,
    EmailCallback,
    BarkCallback,
)
```

`WXWorkCallback` is an alias for `WeComCallback`. Notification callbacks and `CSVWriter` are ordinary SwanLab callbacks and should be passed through the `callbacks=[...]` argument of `swanlab.init(...)` or merged by the callback manager.

## Generic Callback protocol

A custom plugin should subclass or implement SwanLab's `Callback` contract.

| Hook/property | Purpose |
| --- | --- |
| `name` | Globally unique dedupe key. Same-name callbacks overwrite earlier callbacks. |
| `on_run_initialized(run_dir, path, settings, ...)` | Capture run directory, public run path, and settings after `swanlab.init` succeeds. |
| `on_scalar_flush(scalar_records, ...)` | Receive scalar batches. Use the record key and numeric value; keep heavy work outside the training hot path. |
| `on_media_flush(media_records, ...)` | Receive media batches. Route media object construction questions to the media sub-skill. |
| `on_log_flush(log_records, ...)` | Receive terminal/log batches. |
| `on_run_fork()` | Handle multi-process fork events. |
| `on_run_finished(state, error=None, ...)` | Final cleanup, CSV write, or notification send scheduling. |

The callback manager accepts either a single callback or an iterable. It merges global callbacks first and local `swanlab.init(callbacks=...)` callbacks second, so local callbacks overwrite global callbacks with the same `name`. Non-callback items raise `TypeError`.

## Notification callbacks

`NotificationCallback` is the shared base. It captures settings/path on initialization, builds a run URL only when the mode exposes one, and schedules the send operation through a shared `SafeThreadPoolExecutor` so training shutdown is not blocked.

| Callback | Required arguments | Notes |
| --- | --- | --- |
| `LarkCallback` | `webhook_url`, optional `secret` | Adds timestamp/signature fields when a secret is provided. |
| `DingTalkCallback` | `webhook_url`, optional `secret` | Signed webhooks are refreshed when the secret starts with the `SEC` format. |
| `WeComCallback` / `WXWorkCallback` | `webhook_url` | Enterprise WeChat / WXWork sender; alias kept for naming compatibility. |
| `DiscordCallback` | `webhook_url` | Sends the composed text body to a Discord webhook. |
| `SlackCallback` | `webhook_url` | Sends the composed text body to a Slack webhook. |
| `TelegramCallback` | `bot_token`, `chat_id` | Builds the Telegram send-message URL from the bot token. |
| `EmailCallback` | `sender_email`, `receiver_email`, `password`, `smtp_server`, `port` | Supports SMTP with STARTTLS or SSL and emits text/HTML bodies. |
| `BarkCallback` | `url`, optional display and device-key fields | iOS push sender with optional title/icon/group/click-jump settings. |

Credential values themselves belong to the settings/credentials sub-skill. In this sub-skill, only explain which callback argument consumes the already-provided webhook/token/password.

### Notification composition example

```python
import swanlab
from swanlab.plugin import CSVWriter, LarkCallback

callbacks = [
    CSVWriter(dir="reports", filename="runs.csv"),
    LarkCallback(webhook_url="<webhook>", secret="<optional-secret>", language="en"),
]

swanlab.init(project="demo", mode="offline", callbacks=callbacks)
```

This keeps base experiment creation in one `swanlab.init(...)` call while adding CSV and notification side effects. If the user needs online sending, credential and host setup still route to settings-and-modes.

## CSVWriter

`CSVWriter` writes one summary row per SwanLab run.

- Constructor: `CSVWriter(dir=".", filename="swanlab_runs.csv")`.
- Callback name: `CSVWriter`.
- Output path: `dir / filename`. A relative `dir` is relative to the current working directory, not the SwanLab run directory.
- Metadata columns include run id, experiment name, description, project, workspace, timestamp, log directory, and experiment URL.
- On finish, it reads `files/config.yaml` under the run directory if present, then appends config columns as `config/<key>`.
- It keeps the latest scalar value per key and appends scalar columns by metric name.
- If a later run introduces new config or scalar columns, the writer rewrites the header and appends the new columns.

Use CSVWriter for simple run-summary spreadsheets. For complete metric histories or cloud exports, route to open-api-and-cli or sync-and-converters.

## Practical plugin rules

- Keep plugin `name` stable and unique. Same-name callbacks are replacement semantics, not list append semantics.
- Keep network/SMTP calls inside notification callbacks or a protected background worker.
- If a notification does not arrive, first confirm `on_run_initialized` ran; without captured settings/path the base callback intentionally does nothing on finish.
- If training runs in multiple processes, register notification and CSV callbacks only where the run is created, or rely on the framework adapter's rank-zero guard.
- For CSV confusion, print the process current working directory and the resolved `dir / filename` before assuming SwanLab wrote to the wrong location.
