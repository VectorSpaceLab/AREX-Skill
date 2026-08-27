# Service configuration

DeepPavlov serving reads settings from the active settings directory.

## Settings directory

- Default location: the packaged `utils/settings` directory in the installed DeepPavlov tree.
- Override with `DP_SETTINGS_PATH`.
- Inspect the active path with `python -m deeppavlov.settings`.
- Restore/populate default files with `python -m deeppavlov.settings -d`.

## `server_config.json`

The default `common_defaults` values are:

```json
{
  "host": "0.0.0.0",
  "port": 5000,
  "model_args_names": [],
  "https": false,
  "https_cert_path": "",
  "https_key_path": "",
  "socket_type": "TCP",
  "unix_socket_file": "/tmp/deeppavlov_socket.s",
  "socket_launch_message": "launching socket server at"
}
```

Notes:
- `model_args_names` can stay empty to reuse `chainer.in`.
- A custom settings file may add `model_endpoint`; when omitted, the server falls back to `/model`.
- Model-specific overrides belong under `model_defaults` and are selected by `metadata.server_utils` in the model config.
- Non-empty values in a matching `model_defaults` block override the common defaults.

## `dialog_logger_config.json`

- `enabled`: turns dialog logging on or off.
- `logger_name`: subdirectory name under the log root.
- `log_path`: destination root, default `~/.deeppavlov/dialog_logs`.
- `logfile_max_size_kb`: rotates to a new file after the current file reaches this size.
- `ensure_ascii`: when `true`, writes Unicode escape sequences instead of raw non-ASCII characters.

## CLI precedence

- `riseapi`: `-p`, `--https`, `--key`, and `--cert` override the settings file.
- `risesocket`: `--socket-type`, `-p`, and `--socket-file` override the settings file.
- Use `0.0.0.0` for external binding and `127.0.0.1` for local client checks when needed.

## Built-in service behavior

- REST uses CORS with permissive origins, methods, headers, and credentials.
- `/metrics`, `/api`, `/probe`, `/docs`, and `/` are served by the service itself and do not depend on the model endpoint.
