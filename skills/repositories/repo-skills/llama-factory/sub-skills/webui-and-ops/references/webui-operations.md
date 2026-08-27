# Web UI Operations

## Launch modes

Use `llamafactory-cli webui` for the full LlamaBoard application. It creates Gradio tabs for training, evaluation/prediction, chat, export, top-level model/config controls, and footer controls. It initializes the main Web UI `Engine` with `pure_chat=False` and creates default DeepSpeed config files in the UI cache when not in demo mode.

Use `llamafactory-cli webchat` for the pure chat web demo. It initializes the same Web UI engine with `pure_chat=True`, only exposes the chat box and language selector, and skips full training/eval/export controls.

Both launch paths print a visit hint like `http://127.0.0.1:7860`, call the proxy fixer, build a Gradio queue, and call `launch(...)` with an environment-derived server name.

## Gradio environment controls

| Variable | Effect |
| --- | --- |
| `GRADIO_SERVER_NAME` | Overrides the bind host. If unset, Web UI binds to `0.0.0.0` by default, or `[::]` when IPv6 mode is enabled. |
| `GRADIO_IPV6=1` | Enables IPv6 binding default and clears common proxy variables before launch. |
| `GRADIO_SHARE=1` | Requests Gradio share-link mode. Use only when exposing the UI externally is acceptable. |

The Web UI's proxy fixer sets `no_proxy=localhost,127.0.0.1,0.0.0.0`. In IPv6 mode it also removes `http_proxy`, `HTTP_PROXY`, `https_proxy`, `HTTPS_PROXY`, `all_proxy`, and `ALL_PROXY` to prevent Gradio loopback issues.

## Local state and generated files

LlamaBoard uses repo-relative/default working-directory state names:

| Path | Purpose |
| --- | --- |
| `llamaboard_cache/user_config.yaml` | UI language, selected hub, last model, model path map, and cache directory. |
| `llamaboard_cache/ds_z*_config.json` | Generated DeepSpeed templates for UI-launched jobs. |
| `llamaboard_config/` | Saved UI configurations. |
| `data/` | Default dataset directory detected by `llamafactory-cli env` and used by UI defaults. |
| `saves/` | Default root for UI-generated train/eval outputs. |

The UI warns when a user supplies complex checkpoint/output paths because some UI features expect simple path components under `saves/`.

## Training/eval subprocess behavior

When a user starts a train or eval run from LlamaBoard, the UI:

1. Validates selected model name, model path, dataset, output directory, JSON extra args, and PPO reward-model requirements.
2. Builds a training/eval argument dictionary from UI controls.
3. Saves a LlamaBoard config snapshot under the output directory.
4. Sets `LLAMABOARD_ENABLED=1` and `LLAMABOARD_WORKDIR=<output_dir>` for the subprocess.
5. Sets `FORCE_TORCHRUN=1` automatically when a DeepSpeed config is selected.
6. Runs `llamafactory-cli train <generated_training_args.yaml>` without `shell=True`.
7. Writes subprocess stdout/stderr to `webui_subprocess.log` in the output directory.
8. Polls progress and logs through the Web UI, including a SwanLab link when trainer info provides one.

Use this behavior when debugging UI-only failures: inspect the generated YAML/config and `webui_subprocess.log` before changing model or dataset settings.

## Hub selection

The top-level Web UI hub selector maps directly to environment toggles:

- `modelscope` sets `USE_MODELSCOPE_HUB=1` and `USE_OPENMIND_HUB=0`.
- `openmind` sets `USE_OPENMIND_HUB=1` and `USE_MODELSCOPE_HUB=0`.
- Other/default selections set both to `0`.

These toggles affect default model path resolution and dataset/model downloads. They do not convert Hugging Face model IDs automatically in every field; use IDs valid for the selected hub.

## Docker exposure

For containerized Web UI use, expose Gradio's default `7860` and bind to an externally reachable host:

```bash
docker run -dit --ipc=host --gpus=all -p 7860:7860 --name llamafactory llamafactory:latest
```

Inside the container, run:

```bash
GRADIO_SERVER_NAME=0.0.0.0 llamafactory-cli webui
```

If also running API workflows, expose `8000` as well and route API-specific details to `inference-and-serving`.
