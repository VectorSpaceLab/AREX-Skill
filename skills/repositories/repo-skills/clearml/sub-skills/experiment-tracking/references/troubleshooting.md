# Experiment Tracking Troubleshooting

Use this guide when ClearML instrumentation is present but tracking behavior is missing, duplicated, blocked by credentials, or not uploading artifacts/models as expected.

## Credentials Or Server Configuration Missing

Symptoms:

- `Task.init` raises an authentication, host, or connection error.
- The script hangs or retries before training starts.
- No task appears in the ClearML UI.

Likely causes:

- `clearml-init` was not run or the ClearML config file is not available in the runtime environment.
- `api_server`, `web_server`, or `files_server` URLs point to the wrong server.
- Credentials are unavailable in the local machine, CI job, container, or remote worker.
- The user expected the old public demo behavior; ClearML no longer uses it by default.

Fixes:

- Ask the user to configure ClearML credentials through the normal ClearML setup flow, or run in offline mode for local/no-network execution.
- Verify server URLs and that the API server, web server, and files server are all reachable from the runtime environment.
- For scripts that must run anywhere, add an explicit offline flag that calls `Task.set_offline(True)` before `Task.init`.
- Do not hard-code access keys, secret keys, or local config paths in generated code.

## Offline Mode Not Working

Symptoms:

- Offline run still tries to contact a server.
- Switching back online raises a usage error.
- Offline session cannot be imported later.

Likely causes:

- `Task.set_offline(True)` was called after `Task.init` instead of before it.
- The code uses `Task.create`; offline capture is for `Task.init`.
- The current task is still open when `Task.set_offline(False)` is called.
- The offline session path was not preserved by the script or job environment.

Fixes:

- Move `Task.set_offline(True)` before `Task.init`.
- Use `task.close()` before switching offline mode back to `False`.
- Save or print `task.get_offline_mode_folder()` so the session can be imported later.
- Import with `Task.import_offline_session(session_folder_or_zip)` only when credentials/network are available.

## Duplicate Or Overwritten Tasks

Symptoms:

- Repeated local runs overwrite metrics/logs from a previous run.
- The same task ID is reused unexpectedly.
- New logs continue from old iteration numbers without the user intending resume behavior.

Likely causes:

- `Task.init` defaulted to `reuse_last_task_id=True`.
- `continue_last_task=True` or a string task ID was left from a resume workflow.
- The project/name pair is too generic, such as `examples/train` for many scripts.

Fixes:

- Set `reuse_last_task_id=False` for new task per run behavior.
- Use `continue_last_task=True` only when the user explicitly wants to append to a previous run.
- Use an explicit task ID with `reuse_last_task_id="..."` when continuing a known task.
- Make `task_name` include the experiment role or model family, not timestamps unless the user wants a new UI entry for every launch.

## Artifact Upload Fails

Symptoms:

- `task.upload_artifact` returns `False` or logs upload errors.
- Artifacts are missing from the UI after a short script exits.
- Folder or wildcard artifacts are empty or unexpectedly large.

Likely causes:

- `Task.init(output_uri=False)` disabled default upload storage, or no default storage is configured.
- Cloud storage URI is used without the matching ClearML extra and credentials.
- The script exits before background uploads finish.
- A local path is wrong relative to the process working directory.
- A custom object requires pickle or a serialization function.

Fixes:

- Use `output_uri=True` for default file-server storage or a validated URI for shared/cloud storage.
- For S3, Google Cloud Storage, or Azure uploads, ensure the relevant ClearML extra and storage credentials are configured by the user.
- Use `wait_on_upload=True` for important artifacts and `retries` for unreliable storage.
- Use explicit `artifact_object` paths and verify they exist before upload.
- Prefer dictionaries, DataFrames, arrays, PIL images, and file paths; use `auto_pickle=True` only after considering portability/security.

## Model Upload Or Registration Missing

Symptoms:

- Checkpoint files are created locally but no model appears in ClearML.
- `OutputModel.update_weights` does not upload weights.
- Framework auto-logging captures some files but not the desired checkpoint.

Likely causes:

- `Task.init` was called after framework checkpoint callbacks or writers were created.
- `auto_connect_frameworks` was disabled or model-file wildcards did not match the extension.
- No upload destination is configured through `output_uri` or `OutputModel.set_upload_destination`.
- The model save format is unsupported by auto-connect and needs explicit `OutputModel` handling.

Fixes:

- Move `Task.init` before framework logger/callback/checkpoint setup.
- Set `auto_connect_frameworks` with explicit wildcards such as `{"pytorch": ["*.pt", "*.pth"]}`.
- Add manual `OutputModel(task=task, name="...")`, `update_labels(...)`, and `update_weights(weights_filename="...")`.
- Set task-level `output_uri=True` or a model-specific upload destination.

## Logger Calls Do Nothing Or Fail

Symptoms:

- `Logger.current_logger()` is `None` or report calls fail.
- Scalars/images are missing even though code calls `Logger.report_*`.
- Reports appear under confusing graph names or overwrite each other.

Likely causes:

- Logger calls happen before `Task.init`.
- Code constructs `Logger()` directly instead of using the task logger.
- `iteration` is omitted or constant, causing reports to overlap.
- `title` and `series` are swapped or inconsistent across loops.
- The process exits before background flush.

Fixes:

- Use `logger = task.get_logger()` after `Task.init`; pass it into helpers.
- Use `Task.current_task().get_logger()` only after initialization.
- Provide numeric, monotonically increasing `iteration` values.
- Use stable `title` for graph groups and `series` for train/valid/test variants.
- Call `logger.flush(wait=True)` or `task.flush(wait_for_uploads=True)` before fast process exit.

## Config Or Hyperparameters Not Captured

Symptoms:

- CLI arguments are absent from the Hyper-Parameters section.
- YAML/JSON config edits in the UI do not affect remote runs.
- Connected dictionaries do not reflect updates made after connection.

Likely causes:

- Parser parsing happened before ClearML auto-connect was active.
- The script reads the config file before calling `connect_configuration`.
- The code ignores the returned object from `task.connect` or `task.connect_configuration`.
- `ignore_remote_overrides=True` was set unintentionally.
- Sensitive keys were intentionally excluded by `auto_connect_arg_parser` mapping.

Fixes:

- Initialize before parser parsing when using `auto_connect_arg_parser=True`, or connect the parsed namespace explicitly.
- Call `config_path = task.connect_configuration(path, name="...")` before opening the config file, then read `config_path`.
- Reassign dictionaries and config values to the returned objects.
- Remove `ignore_remote_overrides=True` unless audit-only behavior is intended.
- Review parser include/exclude mappings for overly broad `"*": False` rules.

## Framework Auto-Connect Missing Metrics Or Plots

Symptoms:

- TensorBoard, Matplotlib, PyTorch, Keras, XGBoost, or scikit-learn outputs are not captured automatically.
- Matplotlib plots show locally but not in ClearML.
- TensorBoard hparams or model files are missing.

Likely causes:

- Framework objects were created before `Task.init` patched integrations.
- Optional framework packages are missing or versions are unsupported.
- `auto_connect_frameworks=False` or a mapping disabled a specific integration.
- Model-file wildcard filters exclude the actual filename.
- The script runs in a subprocess or distributed setting where initialization happens only in another process.

Fixes:

- Move `Task.init` before imports or object creation that initialize framework logging where practical, and always before writer/callback/checkpoint setup.
- Use explicit `Logger` calls for core metrics even when framework auto-connect is enabled.
- Review `auto_connect_frameworks` mapping and add the needed framework key or wildcard.
- In distributed scripts, initialize ClearML only in the main/rank-zero process unless the user wants per-rank tasks.
- Avoid requiring optional ML frameworks in static validation; generated instrumentation should remain importable when only ClearML is installed.

## `output_uri` Confusion

Symptoms:

- Metrics appear but artifacts/models are not uploaded.
- Uploads go to local paths instead of shared storage.
- Cloud upload errors mention missing packages or credentials.

Likely causes:

- `output_uri=None` relies on project/server defaults that may not be set.
- `output_uri=False` intentionally disables default upload destinations.
- `output_uri=True` uses the default file server, not necessarily cloud storage.
- Cloud URI support requires installed extras and configured credentials.

Fixes:

- Use `output_uri=True` for a simple default file-server upload path.
- Use an explicit URI only when the user has configured that storage backend.
- For cloud storage issues, route detailed dataset/storage credential work to `../data-storage/SKILL.md`.
- For model-specific destinations, use `OutputModel.set_upload_destination(uri)` after creating the `OutputModel`.

## Deferred Init Side Effects

Symptoms:

- Early logs, plots, or framework events are missing at process start.
- Accessing task properties unexpectedly blocks.

Likely causes:

- `deferred_init=True` returns before backend initialization completes.
- Early framework auto-logged events occur before initialization finishes.

Fixes:

- Use default synchronous initialization for most generated instrumentation.
- Use `deferred_init=True` only when startup latency is a hard requirement and missing very early events is acceptable.
- Force synchronization before critical setup by accessing a task property or avoiding deferred init.

## Static Validator Limitations

The bundled validator catches likely instrumentation issues, not runtime connectivity. It cannot verify ClearML credentials, server reachability, cloud storage permissions, optional ML framework behavior, actual artifact existence after dynamic path construction, or remote override semantics. Combine static validation with a small offline-mode smoke run when the user allows execution.
