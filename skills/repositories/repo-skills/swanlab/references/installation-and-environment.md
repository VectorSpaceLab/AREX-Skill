# Installation and Environment

Read this when deciding how to install SwanLab, which optional extras are needed, and what safe checks to run before a task touches credentials, services, media, or framework training.

## Base install

```bash
pip install swanlab
python -c "import swanlab; print(swanlab.__version__)"
swanlab --help
```

The package metadata supports Python 3.9 and newer Python 3 releases. Use a project virtual environment rather than installing into a shared interpreter when possible.

## Optional dependency matrix

| Need | Install/check | Notes |
| --- | --- | --- |
| Basic experiment tracking, settings, CLI, Open API client, lightweight text/html/ECharts support | `pip install swanlab` | Base dependencies include Click, Requests, Pydantic, Rich, Protobuf, pyecharts, watchdog, psutil, and NVIDIA ML Python bindings. |
| Rich media inputs: images, audio, videos, molecules, numeric arrays, plot helpers | `pip install "swanlab[media]"` | Adds packages such as Pillow/numpy/soundfile/moviepy/imageio/rdkit. If missing, base import should still work; only the media branch should fail. |
| Offline dashboard / `swanlab watch` dashboard extension | `pip install "swanlab[dashboard]"` | The dashboard package is intentionally separate from base tracking. |
| S3-related storage/upload features | `pip install "swanlab[s3]"` | Adds boto3. Still requires credentials and endpoint configuration. |
| Third-party framework callbacks | Install SwanLab plus the framework package, for example `transformers`, `lightning`, `keras`, `xgboost`, `lightgbm`, `ray[tune]`, `accelerate`, or `ultralytics`. | SwanLab does not install every ML framework by default. Missing framework imports are expected until the user installs that stack. |
| Real GPU/vendor hardware monitoring or framework training | Install the user's framework/backend stack and verify the device in that environment. | Base package import does not prove CUDA/ROCm/MPS/vendor training or monitoring. |
| Cloud upload, Open API operations, self-hosted admin, notification webhooks | SwanLab install plus API key/host/network/service credentials. | Never invent or echo API keys. Prefer offline/local/disabled examples when credentials are absent. |

## Safe checks by risk level

### No credentials, no network

```bash
python -m swanlab --help
python scripts/swanlab_disabled_smoke.py
python scripts/check_swanlab_cli.py
```

These checks validate importability, CLI registration, and basic run lifecycle without upload.

### Local/offline run work

- Confirm `mode="offline"` or `mode="local"` intentionally writes local run files.
- Validate a run directory before syncing; read [../sub-skills/sync-and-converters/SKILL.md](../sub-skills/sync-and-converters/SKILL.md).
- Do not run `swanlab sync` until the user has chosen the target host/account and supplied valid credentials.

### Cloud/self-hosted API work

- Confirm `api_host` and `web_host` are the intended pair.
- Use `swanlab login` or explicit `Api(api_key=..., host=...)` according to the task's security policy.
- Start with help/list/query commands and small pages before all-page exports.

### Optional frameworks and media

- Import the framework or media dependency before editing a long training script.
- If a task only asks for code generation, produce code and dependency notes without installing/training unless the user asks for execution.
- If a task asks for verification, run a tiny fixture and skip real training/downloads unless the user provides data, budget, and hardware.

## Minimal smoke recipe

```python
import swanlab

run = swanlab.init(project="smoke", mode="disabled")
swanlab.log({"loss": 0.1})
swanlab.finish()
assert swanlab.run is None
```

If this fails, resolve import/install/runtime problems before debugging cloud credentials or framework integrations.
