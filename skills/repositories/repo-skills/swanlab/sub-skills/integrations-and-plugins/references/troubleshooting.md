# Troubleshooting

Use this reference when a SwanLab framework adapter or plugin fails to import, logs twice, overwrites another callback, silently misses a notification, or writes CSV output in an unexpected location.

## Missing third-party framework packages

If importing an adapter raises an error that names a framework package, fix the training environment first. Do not debug callback arguments until the package import succeeds.

| Adapter area | Typical install hint |
| --- | --- |
| Accelerate | `pip install accelerate` |
| FastAI | `pip install fastai` |
| Keras | `pip install keras` plus the backend stack the user's Keras setup requires |
| PyTorch Lightning | `pip install lightning` |
| MMEngine | `pip install mmengine` |
| PaddleNLP | `pip install paddlenlp` |
| Ray Tune | `pip install 'ray[tune]'` |
| Stable-Baselines3 | Install the Stable-Baselines3 distribution; Python imports it as `stable_baselines3`. |
| Torchtune | `pip install torchtune` |
| Transformers | `pip install transformers` |
| XGBoost | `pip install xgboost` |

Some adapters import successfully without the third-party framework because the framework is only touched inside a hook. That is still not proof that real training will run; it only means the adapter module is lazy enough to inspect.

## Duplicate distributed logging

Symptoms:

- the same metric appears more than once for a single step;
- a notification arrives once per worker;
- CSV receives several rows for one intended run;
- a user added both direct `swanlab.log(...)` calls and a framework adapter that logs the same values.

Fixes:

1. Prefer the framework adapter's built-in guard: Transformers/PaddleNLP world-process-zero, Lightning rank-zero wrappers, Accelerate main-process-only, Torchtune rank 0, and Ray per-trial logging actors.
2. Register CSV and notification callbacks only in the process that owns the SwanLab run.
3. Avoid adding manual `swanlab.log(...)` calls for metrics already emitted by the adapter.
4. For Ray, let `SwanLabLoggerCallback` own trial logging instead of creating SwanLab runs in every worker.
5. If repeated Ultralytics plots are the issue, remember the adapter de-duplicates plots by timestamp; repeated scalar metrics may have a different cause.

## Callback merge and overwrite surprises

SwanLab's callback manager uses callback `name` as the dictionary key.

- `merge_callbacks(...)` accepts `None`, a single callback, or an iterable of callbacks.
- Non-callback values raise `TypeError: Expected swanlab.Callback`.
- Global callbacks are merged first; local run callbacks are merged second.
- Same-name callbacks are overwritten. They are not both executed.
- `remove_callback(name)` is silent when the callback is absent.

If a callback seems to disappear, inspect `callback.name` for every global and local callback. Give custom callbacks distinct names when both should run.

## Notification credentials and send path

Symptoms:

- `on_run_finished` returns but no message appears;
- logs show webhook, SMTP, or bot errors;
- the notification lacks a run link;
- it works in a test but not inside distributed training.

Checks:

1. Confirm the callback was passed to `swanlab.init(callbacks=[...])` or otherwise merged into the active run.
2. Confirm `on_run_initialized` ran; without captured settings/path, `NotificationCallback.on_run_finished` intentionally does nothing.
3. Check the credential field for the selected sender: webhook URL, bot token/chat id, SMTP password/server/port, Bark URL/key.
4. For Lark and DingTalk, confirm the secret belongs to that platform. DingTalk signing is for signed webhook secrets that start with `SEC`.
5. If the run is `local` or has no path, no public run URL is added to the notification; that does not prevent the message body from being sent.
6. In multi-process training, send notifications only from rank zero or the process that owns the SwanLab run.

Credential acquisition, environment variables, and host selection route to settings-and-modes.

## Background executor failures

Notification callbacks submit the real send operation to a shared safe thread-pool executor.

- A background failure may be logged without raising in the training thread.
- During shutdown the executor is designed to degrade safely rather than crash the caller.
- To make failures synchronous in a test, call the concrete sender's `_send_notification(...)` with network/SMTP transports patched.
- To verify scheduling only, patch the executor's `run(...)` method and assert it received the sender callable.

## CSV path confusion

Symptoms:

- no CSV appears under the run directory;
- the CSV appears in a previously used folder;
- a later run adds unexpected columns;
- rows have blank config columns.

Checks:

1. Resolve the process current working directory and `CSVWriter(dir=..., filename=...)`; the writer joins those directly.
2. Remember the run directory is used for reading `files/config.yaml`, not for choosing the CSV output path.
3. If new scalar/config keys appear in later runs, `CSVWriter` rewrites the header and appends columns.
4. Delete the old CSV if the user wants a fresh schema.
5. Blank config columns usually mean the run had no config file or the key was absent for that run.

## Quick safe diagnostic

Run the bundled validation helper from this skill tree when you need local evidence without installing optional frameworks or making network calls:

```bash
python scripts/check_plugin_callback.py
```

Run it from the `integrations-and-plugins` sub-skill directory, or pass the script's path explicitly from another working directory. Expected evidence includes callback overwrite behavior, CSVWriter output path/header, notification executor scheduling with patched HTTP, safe executor behavior, optional framework import hints, and distributed-guard surface notes.
