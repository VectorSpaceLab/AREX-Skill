# H2O LLM Studio app runtime setup

This reference covers the H2O Wave GUI and container entry points. It intentionally avoids training configuration details; route experiment YAML and training execution questions to the neighboring configuration and training sub-skills.

## Runtime root expectations

Start the app from an H2O LLM Studio runtime root: a directory that contains the `llm_studio/` package plus runtime assets such as `pyproject.toml`, `prompts/`, and `model_cards/`. The app imports `llm_studio.app`, but several initialization paths also use relative asset paths for icons, config modules, prompt templates, and model-card templates. If you launch from an unrelated current working directory, import may succeed while the first Wave request fails to find assets.

Python runtime expectations verified from the package metadata:

- Python `3.10.*`.
- H2O Wave is a required dependency (`h2o-wave` in the package dependency set).
- Production fine-tuning is GPU-oriented. The public setup guidance expects Ubuntu with a recent NVIDIA GPU and driver; larger models need substantial VRAM. App import and many UI diagnostics can still be checked without starting a training job.

## Local GUI commands

### Preferred checkout-style command

```bash
make setup
make llmstudio
```

`make setup` uses `uv sync --frozen --no-dev` and then applies maintained third-party patches. Optional `flash-attn` is attempted by default through the `FLASH` make variable; use the repository's normal setup policy when choosing whether to keep or skip that optional acceleration extra.

`make llmstudio` performs this sequence:

1. Run `nvidia-smi`.
2. Set `HF_HUB_DISABLE_TELEMETRY=1`.
3. Set Wave upload/download environment variables.
4. Run `uv run wave run --no-reload llm_studio.app`.

Because of the `nvidia-smi && ...` guard, a host without working NVIDIA tooling will not reach the Wave command through this target.

### Direct Wave command

Use this when you are in a custom Python environment or diagnosing app startup separately from the `make llmstudio` GPU guard:

```bash
H2O_WAVE_MAX_REQUEST_SIZE=25MB \
H2O_WAVE_NO_LOG=true \
H2O_WAVE_PRIVATE_DIR="/download/@${H2O_LLM_STUDIO_WORKDIR:-$PWD}/output/download" \
wave run llm_studio.app
```

For a no-reload production-like process, add `--no-reload` after `wave run`:

```bash
wave run --no-reload llm_studio.app
```

Open `http://localhost:10101/` in a browser after Wave reports that the server is ready. Chrome is the browser used in the public quickstart guidance.

### Stop the service

- Foreground launch: press `Ctrl-C` in the terminal running Wave.
- Helper target: `make stop-llmstudio` kills the process listening on port `10101`.
- Manual check: `lsof -ti :10101` shows the process occupying the default port.

## Core environment variables

### H2O Wave variables

| Variable | Use | Practical guidance |
|---|---|---|
| `H2O_WAVE_MAX_REQUEST_SIZE` | Maximum request/upload size accepted by Wave. | The documented app launch sets `25MB`. Increase deliberately for larger uploads only when the Wave server and proxy allow it. |
| `H2O_WAVE_NO_LOG` | Suppresses Wave logging when true. | Local commands set it to `true`/`True`; unset it temporarily when diagnosing server traffic. |
| `H2O_WAVE_PRIVATE_DIR` | Maps a browser URL prefix to a private filesystem directory for downloads. | Use `/download/@<workdir>/output/download` where `<workdir>` is the resolved H2O LLM Studio workdir. If downloads open 404s, verify this points at the same `output/download` tree used by the app. |
| `H2O_WAVE_ALLOWED_ORIGINS` | Allows browser origins when access is proxied or remote. | Set to a specific public origin when possible. The documented broad escape hatch for cloud/proxy testing is `*`. |
| `H2O_WAVE_APP_CONNECT_TIMEOUT` | App connection timeout in seconds. | Default is 5 seconds. Increase for slow remote/proxy setups; `-1` disables the timeout. |
| `H2O_WAVE_APP_WRITE_TIMEOUT` | App write timeout in seconds. | Same timeout behavior as above. |
| `H2O_WAVE_APP_READ_TIMEOUT` | App read timeout in seconds. | Same timeout behavior as above. |
| `H2O_WAVE_APP_POOL_TIMEOUT` | App connection-pool timeout in seconds. | Same timeout behavior as above. |
| `H2O_WAVE_BASE_URL` | Public base URL used by app download links in cloud mode. | The app prepends it to download paths when `H2O_CLOUD_ENVIRONMENT` is present. Keep it aligned with the external route users open in the browser. |
| `H2O_WAVE_RELOAD_EXCLUDE` | Excludes directories from Wave reload watching. | The developer `make wave` target excludes `data:output:reports` to avoid reload loops from app artifacts. |
| `H2O_WAVE_DATA_DIR` | Wave server data directory. | The container image places Wave state under the mounted workdir. |

### H2O LLM Studio variables

| Variable | Use | Practical guidance |
|---|---|---|
| `H2O_LLM_STUDIO_WORKDIR` | Persistent application workdir. | Defaults to the process current working directory. Set it to a durable location before the first browser session if you want data, databases, and outputs outside the runtime root. |
| `H2O_LLM_STUDIO_ENABLE_HEAP` | Enables Heap analytics integration. | Default is off. Container app metadata may set it to true in managed runtimes. |
| `H2O_LLM_STUDIO_DEFAULT_LM_MODELS` | Comma-separated default causal-LM model list in UI settings. | Use only to change the model choices shown by default; it does not download models by itself. |
| `H2O_LLM_STUDIO_DEFAULT_S2S_MODELS` | Comma-separated default sequence-to-sequence model list. | Same behavior as the causal-LM list. |
| `H2O_LLM_STUDIO_DEMO_DATASETS` | Directory containing pre-bundled demo parquet datasets. | When absent, first-session default dataset preparation may call external dataset downloads. Container builds use this to avoid runtime network for demo datasets. |
| `MIN_DISK_SPACE_FOR_EXPERIMENTS` | Minimum free-space threshold parsed by the app. | Default is `2GB`; accepts suffixes such as `MB`, `GB`, and `TB`. |
| `ALLOWED_FILE_EXTENSIONS` | Comma-separated upload/import extensions. | Default includes `.zip`, `.csv`, `.pq`, and `.parquet` in lower and upper case. |
| `HF_HUB_DISABLE_TELEMETRY` | Hugging Face telemetry control. | The local helper targets and container disable telemetry for the app process. |
| `HF_HOME` | Hugging Face cache root. | Container runtime points it into the mounted workdir so caches persist across container restarts. |
| `TRITON_CACHE_DIR` | Triton cache root. | Container runtime points it into the mounted workdir. |
| `HF_HUB_ENABLE_HF_TRANSFER` | Enables/disables Hugging Face transfer acceleration. | The app settings expose this as a toggle; set to `0` when troubleshooting transfer issues. |
| `AWS_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Initial AWS connector defaults. | Values seed settings; persistent settings and credential storage can override them after the first session. |
| `WANDB_API_KEY`, `WANDB_PROJECT`, `WANDB_ENTITY` | Initial Weights & Biases defaults. | Used when launching experiments from the UI. |
| `HF_TOKEN` | Initial Hugging Face token default. | Used by dataset import, model download/export, and publishing flows when saved in settings. |
| `OPENAI_API_TYPE`, `OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_API_DEPLOYMENT_ID`, `OPENAI_API_VERSION` | Initial OpenAI/Azure OpenAI defaults for evaluation settings. | Settings persist separately after users save them. |
| `GPT_EVAL_MAX` | Default maximum sample count for GPT evaluation. | Use it to cap cost exposure for GPT-based metrics. |

## Persistent workdir layout

The app derives these paths from `H2O_LLM_STUDIO_WORKDIR` or, when unset, from the current working directory at app startup:

```text
<workdir>/
  data/
    dbs/
      user.db             # SQLite tables for datasets and experiments
      <wave-user>.yaml    # non-secret persisted settings
      <wave-user>.env     # optional secret values when .env credential storage is selected
    user/                 # uploaded/imported user datasets and prepared default datasets
  output/
    user/                 # experiment directories created by GUI-launched runs
    download/             # symlink-backed files served through Wave private download URLs
```

The Wave user id comes from Wave authentication state. If a deployment changes auth subjects between sessions, settings may appear to disappear because the app uses a different `<wave-user>.yaml` and `<wave-user>.env` name.

## Default dataset behavior

On first client initialization, the app tries to create default datasets when dataset id `1` does not exist in the SQLite database. If `H2O_LLM_STUDIO_DEMO_DATASETS` is set, it reads local parquet files from that directory. Otherwise it uses the Hugging Face `datasets` package to download public datasets for causal language modeling, DPO, classification, and regression examples. Download failures are logged and rolled back; the app can still be used after importing your own dataset.

## Docker runtime

### Pull and run a published image

```bash
mkdir -p "$(pwd)/llmstudio_mnt"
chmod 777 "$(pwd)/llmstudio_mnt"

docker pull h2oairelease/h2oai-llmstudio-app:latest

docker run \
  --runtime=nvidia \
  --shm-size=64g \
  --init \
  --rm \
  -it \
  -u "$(id -u):$(id -g)" \
  -p 10101:10101 \
  -v "$(pwd)/llmstudio_mnt:/mount" \
  h2oairelease/h2oai-llmstudio-app:latest
```

Open `http://localhost:10101/` after the container starts. Useful lifecycle commands are `docker ps` to find the running container and `docker kill <container>` to stop it.

### Build locally

```bash
docker build -t h2o-llmstudio .
mkdir -p "$(pwd)/llmstudio_mnt"
docker run \
  --runtime=nvidia \
  --shm-size=64g \
  --init \
  --rm \
  -it \
  -p 10101:10101 \
  -v "$(pwd)/llmstudio_mnt:/mount" \
  h2o-llmstudio
```

The containerized app uses `/mount` as `H2O_LLM_STUDIO_WORKDIR`, stores Hugging Face and Triton caches under that mount, exposes port `10101`, and starts by running `nvidia-smi` followed by `wave run --no-reload llm_studio.app`. The entrypoint also ensures `USER` is set for arbitrary numeric container users.

## Optional UI test evidence

The repository's UI test approach is optional because it requires a running Wave server, browser automation dependencies, and sometimes remote-login credentials. The local pattern is:

```bash
make setup-dev
make llmstudio
# in a second terminal
export LOCAL_LOGIN=True
export PYTEST_BASE_URL=localhost:10101
make test-ui-headed
```

The optional UI scenarios cover local login, home page visibility, importing and deleting a dataset, creating a tiny experiment, and deleting the experiment. Treat these as integration tests, not as safe default smoke checks.
