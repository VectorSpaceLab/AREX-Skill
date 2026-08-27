# Cross-Cutting Troubleshooting

Use this reference when a Nesa workflow fails before you know which sub-skill
owns the issue.

## Install/import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: msgspec`, `pydantic_settings`, `nats`, or `httpx` | Backend protocol dependencies missing. | Install the Nesa backend set: `msgspec pydantic-settings python-dotenv nats-py httpx requests tqdm safetensors pyyaml`. |
| `ModuleNotFoundError: torch` or Transformers says no supported ML backend | Local model/demo dependencies missing. | Install a PyTorch build appropriate for the user's CPU/GPU, then `transformers` and `safetensors`. For a CPU-only check, a CPU torch wheel is enough. |
| `ModuleNotFoundError: gradio`, `accelerate`, `markdown`, or `numba` while importing the web UI | Web UI runtime dependency set is incomplete. | Use the web UI sub-skill's install reference; install only the selected platform/runtime group, not every GPU variant. |
| Torch imports but warns about NumPy ABI or fails during tensor operations | NumPy version is incompatible with the installed torch wheel. | Align with the repo requirements by using `numpy==1.26.*` for the checked web UI stack. |
| `pip check` reports conflicts after a broad install | Mixed CPU/GPU or web UI dependency variants. | Create a clean environment for the selected backend instead of repairing a user-owned base environment. |

## Model asset failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Local DistilBERT demo cannot find `config.json` or tokenizer files | The model directory path is wrong or incomplete. | Use `encrypted-distilbert/scripts/validate_model_dir.py` against the directory before loading the model. |
| Model loads but labels are missing or scores are hard to interpret | The config's `id2label` mapping is absent or different from the documented model. | Inspect the model config and report the actual label keys before claiming positive/negative sentiment. |
| Hugging Face download fails or asks for a token | Network, gated model, auth, or branch/file mismatch. | Preview the model/download naming first with `web-ui-runtime/scripts/check_hf_model_plan.py`; then ask the user to provide credentials or a local model path if needed. |

## Backend and service failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `torch.cuda.is_available()` is false despite visible GPUs | CPU torch wheel or incompatible CUDA stack. | Decide whether GPU proof is required. If yes, install the appropriate platform-specific torch build in a clean environment; do not count CPU import as GPU verification. |
| Remote encrypted LLM streaming times out | Nesa stream endpoint unavailable, blocked network, or wrong model mapping. | Use backend request-preview scripts first. Treat actual stream calls as optional network/service checks unless the user explicitly requires them. |
| Web UI launches on `0.0.0.0` without auth | Default or user-supplied flags expose the service. | Do not continue unless the user accepts the exposure or adds `--gradio-auth` / auth file and an appropriate listen host. |
| Web UI loads the wrong model handler | Model name does not match registry keys. | Check the model-specific registry key, usually slash-replaced with underscores for bundled handlers, before calling a handler. |

## Configuration failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| UI mode is ordinary chat/instruct instead of encrypted mode | Settings file omitted or `mode` changed. | Validate that the active settings include `mode: equivariant-encrypt`. |
| Generated prompts look duplicated or malformed | The `equivariant-encrypt_command`, instruction template, or history conversion changed. | Use backend-protocol request-preview scripts to inspect role ordering and sanitized content before sending a request. |
| CPU is used unexpectedly | Command flags include `--cpu`, or the selected installer branch chose CPU mode. | Inspect command flags and environment variables. Remove `--cpu` only after the user has a verified GPU backend. |

## When to stop and ask

Stop for user approval before:

- installing or changing broad GPU/vendor dependency stacks;
- running one-click installers that download Miniconda or mutate local files;
- launching a public web UI endpoint;
- downloading large model weights; or
- contacting Nesa's remote stream endpoint for a live inference request.
