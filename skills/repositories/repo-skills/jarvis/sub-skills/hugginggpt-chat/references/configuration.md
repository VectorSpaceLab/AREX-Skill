# HuggingGPT configuration

Source evidence names: README.md; hugginggpt/README.md; hugginggpt/server/awesome_chat.py; hugginggpt/server/configs/config.default.yaml; config.lite.yaml; config.gradio.yaml; config.azure.yaml.

Use this reference to interpret a HuggingGPT config before recommending CLI/server/API/web execution. Use the bundled `scripts/inspect_hugginggpt_config.py` helper when the user provides a config or checkout.

## Named configs

| Config name | Controller endpoint block | Inference mode | Local deployment field | Intended use | Startup implications |
|---|---|---|---|---|---|
| `default` | `openai` placeholder plus Hugging Face token placeholder | `hybrid` | `full` | Full feature path combining remote Hugging Face and local model server. | Requires valid OpenAI and Hugging Face credentials. Because mode is `hybrid`, the chat server also requires a local inference endpoint to answer `/running` before CLI/server starts. |
| `lite` | `openai` placeholder plus Hugging Face token placeholder | `huggingface` | `minimal` | Lightweight remote mode with no local expert-model server. | Requires valid OpenAI and Hugging Face credentials. Does not require local model downloads, but only tasks with stable Hugging Face Inference API availability can run. |
| `gradio` | Hugging Face token placeholder, no normal `openai`/`azure` block | `huggingface` | `full` | Gradio-style demo path where the surrounding app may provide controller endpoint details. | Do not assume `awesome_chat.py --mode cli` works with this file. It lacks normal `http_listen` and OpenAI/Azure controller fields. |
| `azure` | `azure` placeholder block plus Hugging Face token placeholder | `huggingface` | `full` | Azure OpenAI controller with remote Hugging Face expert models. | Requires Azure fields in config and a valid Hugging Face token. Source does not implement an Azure environment-variable fallback. |

## Core fields

| Field | Meaning | Operational notes |
|---|---|---|
| `model` | Controller LLM name. | Source comments mention `text-davinci-003` and GPT-4 support. Token helper tables include GPT-4, GPT-3.5, and completion models. |
| `use_completion` | Chooses controller endpoint family. | `true` means `/v1/completions` and source converts chat messages into a completion prompt. `false` means `/v1/chat/completions`. Match this with the controller model and provider. |
| `openai.api_key` | OpenAI key in config. | Must start with `sk-` or source falls back to `OPENAI_API_KEY` if that env var starts with `sk-`. Placeholder values cause startup failure in OpenAI configs. |
| `azure.api_key`, `azure.base_url`, `azure.deployment_name`, `azure.api_version` | Azure OpenAI controller fields. | Source builds `/openai/deployments/{deployment_name}/...?...api-version=...`. Azure values are read from config; no Azure env-var fallback is implemented in `awesome_chat.py`. |
| `dev` and `local.endpoint` | Local OpenAI-compatible controller path. | `dev: true` has priority over Azure and OpenAI. Use only when the user intentionally runs a compatible local controller service. |
| `huggingface.token` | Hugging Face access token for model status and inference. | Must start with `hf_` or source falls back to `HUGGINGFACE_ACCESS_TOKEN` if that env var starts with `hf_`. Placeholder values cause startup failure. |
| `inference_mode` | Expert-model endpoint policy: `local`, `huggingface`, or `hybrid`. | `huggingface` avoids local model server startup. `local` and `hybrid` require the local inference endpoint to be running. |
| `local_deployment` | Local model-server scale: `minimal`, `standard`, or `full`. | Applies only to local/hybrid expert models. Minimal still means ControlNet local stack in the source model server, not a verified lightweight CPU path. |
| `device` | Local model device such as `cuda:0` or `cpu`. | Used by `models_server.py`; not verified by this sub-skill. |
| `local_inference_endpoint.host` and `.port` | Expert local model-server address. | `awesome_chat.py` checks `http://{host}:{port}/running` when `inference_mode` is not `huggingface`. |
| `http_listen.host` and `.port` | Chat API server bind address. | Used only by server mode. Web clients must point their base URL to this host/port. |
| `num_candidate_models` | Maximum available models considered after status checks. | Candidate model discovery first reads the task catalog, then probes Hugging Face and/or local status endpoints. |
| `max_description_length` | Metadata truncation length for model selection. | Longer descriptions may improve selection context but increase controller tokens. |
| `proxy` | Optional HTTPS proxy string. | Used for OpenAI/Hugging Face requests when set. Do not store credentials in generated skill files. |
| `logit_bias.parse_task` and `.choose_model` | Controller bias for task JSON and model-choice JSON tokens. | Token ids come from `get_token_ids.py`; installed facts are summarized in the model reference. |
| `tprompt`, `prompt`, `demos_or_presteps` | Prompt templates and demonstration JSON files. | These drive stages 1, 2, and 4. Keep paths relative to the server working directory when running source code. |

## Credential resolution rules

OpenAI config:

1. If `openai.api_key` starts with `sk-`, source uses that value.
2. Else if `OPENAI_API_KEY` exists and starts with `sk-`, source uses that env var.
3. Else startup raises an incorrect OpenAI key error.

Hugging Face config:

1. If `huggingface.token` starts with `hf_`, source sends it as an Authorization bearer token.
2. Else if `HUGGINGFACE_ACCESS_TOKEN` exists and starts with `hf_`, source uses that env var.
3. Else startup raises an incorrect Hugging Face token error.

Azure config:

- The source reads `azure.api_key`, `azure.base_url`, `azure.deployment_name`, and `azure.api_version` from config.
- It does not validate placeholder strings as strictly as OpenAI/Hugging Face, so use the inspector to catch placeholders before runtime.
- Do not assume Azure env vars will be honored unless the user modifies the source.

Route-level dynamic endpoint fields:

- In server mode, `/hugginggpt`, `/tasks`, and `/results` can accept `api_key`, `api_type`, and `api_endpoint` in the request JSON.
- This is useful when a config intentionally omits a controller endpoint block.
- CLI/test mode cannot use those per-request fields because there is no route request.

## Remote/lite versus local/hybrid decision table

| User situation | Recommend | Why |
|---|---|---|
| Wants a low-footprint demo and has OpenAI plus Hugging Face credentials. | `config.lite.yaml` or equivalent `inference_mode: huggingface`. | Avoids local model downloads and `/running` local endpoint gate. |
| Wants canny/openpose/depth/hed/mlsd/scribble/seg ControlNet workflows. | Local or hybrid only, with explicit unverified CUDA/model-server setup. | Source handles ControlNet tasks by choosing local IDs and reports them unavailable in pure Hugging Face mode. |
| Has `config.default.yaml` with placeholder keys and no model server. | Fix credentials and either switch to lite or start/validate local endpoint. | Default is `hybrid`, so credentials alone are not enough. |
| Uses Azure OpenAI. | Start from `config.azure.yaml` and fill all Azure fields plus Hugging Face token. | Azure config avoids OpenAI key checks but still needs Hugging Face token for expert models. |
| Runs browser UI on another host. | Match web `HUGGINGGPT_BASE_URL` to the server's reachable host and port. | Browser calls the chat API server, not the local model-server port. |

## Safe config inspector

The bundled helper is intentionally read-only. It imports PyYAML, parses the selected config, and prints a JSON summary without printing secret values or contacting any endpoint.

Examples from this sub-skill directory:

```bash
python scripts/inspect_hugginggpt_config.py --repo-root <jarvis-repo-root> --config-name lite
python scripts/inspect_hugginggpt_config.py --config <path-to-config.azure.yaml>
```

The summary includes:

- controller `model` and `use_completion`;
- `inference_mode`, `local_deployment`, `http_listen`, and local endpoint URL components;
- OpenAI, Hugging Face, Azure, and local-controller field status without values;
- whether a local expert-model server is required;
- warnings for placeholder/missing credentials, local endpoint gates, ControlNet limitations, and likely completion/chat endpoint mismatches.

Use this before telling a user to download models or debug CUDA. For the common lite-placeholder failure, the correct first fix is credentials, not local model downloads.
