# HuggingGPT chat troubleshooting

Source evidence names: README.md; hugginggpt/README.md; hugginggpt/server/awesome_chat.py; hugginggpt/server/models_server.py; config.default.yaml; config.lite.yaml; config.gradio.yaml; config.azure.yaml; web config and API client files.

Use this reference when a user reports startup, route, model-availability, local endpoint, web, credential, or ControlNet problems. Prefer safe configuration inspection before recommending downloads, CUDA setup, or source edits.

## Fast triage

1. Identify surface: CLI, server route, web client, Gradio-style app, or optional local model server.
2. Identify config: default, lite, gradio, azure, or user-edited file.
3. Run the safe config inspector. It parses YAML only and redacts credentials.
4. If `inference_mode` is `huggingface`, do not debug the local model-server port unless the user intentionally expects local ControlNet or hybrid mode.
5. If `inference_mode` is `local` or `hybrid`, verify the local expert endpoint `/running` before API route debugging.
6. Use `/tasks` to isolate task planning from model execution. Use `/results` to debug model selection/execution before final response generation.

## Symptom table

| Symptom | Likely cause | Fix or next step |
|---|---|---|
| `Incorrect OpenAI key` at startup. | `openai.api_key` is a placeholder or not `sk-...`, and `OPENAI_API_KEY` is absent or not `sk-...`. | Put a valid OpenAI key in the config or set `OPENAI_API_KEY`; do not paste the key into chat. Re-run the config inspector. |
| `Incorrect HuggingFace token` at startup. | `huggingface.token` is a placeholder or not `hf_...`, and `HUGGINGFACE_ACCESS_TOKEN` is absent or not `hf_...`. | Put a valid Hugging Face token in the config or set `HUGGINGFACE_ACCESS_TOKEN`. This is required even in lite mode. |
| Azure config starts but controller calls fail, or endpoint URL is clearly placeholder-derived. | One or more Azure fields remain `REPLACE_WITH_...` or deployment/API version do not match the Azure resource. | Fill `azure.api_key`, `azure.base_url`, `azure.deployment_name`, and `azure.api_version` in config. Source does not read Azure env vars by default. |
| `Only server mode supports dynamic endpoint` or CLI cannot start with a config lacking OpenAI/Azure/local controller fields. | CLI/test modes require API type at startup. Dynamic `api_key`, `api_type`, and `api_endpoint` fields exist only on server routes. | Use a complete config for CLI, or run server mode and pass endpoint fields per request. |
| Startup says the local inference endpoints server is not running. | `inference_mode` is `local` or `hybrid`, so `awesome_chat.py` calls local `/running` and fails. | If local models are not needed, switch to `inference_mode: huggingface` or use lite config. If local models are needed, separately start and validate the optional local model server. |
| User has `config.lite.yaml` with placeholder tokens and asks why CLI/server fails. | Lite avoids local model downloads but still needs OpenAI and Hugging Face credentials. | Run the config inspector; fix `OPENAI_API_KEY`/`openai.api_key` and `HUGGINGFACE_ACCESS_TOKEN`/`huggingface.token`. Do not route them to CUDA/model downloads. |
| Default config fails on a laptop even after keys are fixed. | Default is `hybrid` plus `local_deployment: full`, so it expects a local model server and a large model stack. | For remote-only operation, switch to lite or set `inference_mode: huggingface`. For local full features, treat it as an unverified heavy CUDA path. |
| `/tasks` works but `/results` says no available models. | Task planning succeeded, but candidate status checks found no loaded Hugging Face or local model. | Check `inference_mode`, Hugging Face token, network/proxy, and task label. Try a simpler task with common hosted models. |
| `/hugginggpt` falls back to generic chitchat. | Task parsing returned invalid JSON or empty task list. | Test `/tasks`; inspect the user prompt for unsupported task names, malformed resource references, or too much prior chat context. |
| Planned task is canny/openpose/depth/hed/mlsd/scribble/seg ControlNet and mode is `huggingface`. | Source marks ControlNet services local-only. | Explain the limitation. To run it, the user needs a separately verified local/hybrid model-server path; do not claim remote support. |
| `ControlNet is unavailable` or `service related to ControlNet is not available`. | User requested ControlNet in remote mode or local model server lacks the required model. | In remote mode, this is expected. In local/hybrid mode, verify local `/status/<control-model-id>` and model downloads separately. |
| Import errors from Torch, Diffusers, ControlNet auxiliary packages, ESPnet, Asteroid, SpeechBrain, or audio/video packages. | User tried to run the full local model server without the heavy optional stack. | This sub-skill did not verify that stack. Separate local environment preparation is required; avoid treating it as a lite-mode fix. |
| `ModuleNotFoundError` or heavy import failure when simply checking config. | User imported `awesome_chat.py` or `models_server.py` for inspection. | Use the bundled config inspector instead; it imports only PyYAML and standard library modules. |
| Web page loads but API calls fail with `Network Error`, CORS-like symptoms, or 404. | Web base URL points to the wrong host/port, backend not running, or browser cannot reach it. | Set `HUGGINGGPT_BASE_URL` to the chat API server `http_listen` host/port reachable from the browser. Do not point it at Vite or the local model-server port. |
| Web request times out. | Backend execution exceeded the web client's timeout or a model endpoint hung. | Call `/tasks` first, then `/results`, and reduce the request to a single common task. |
| Video output exists but browser cannot play it. | ffmpeg lacks H.264/libx264 support, conversion failed, or the returned `/videos/...` path is served from the wrong base URL. | Validate ffmpeg/libx264 outside the skill; fetch the video path from the chat API host. |
| OpenAI or Hugging Face calls fail behind a proxy. | `proxy` is unset or incorrect. | Set the config `proxy` field if appropriate, without embedding credentials in reusable skill files. |

## Credential checklist

OpenAI:

- Config key must start with `sk-`, or env `OPENAI_API_KEY` must start with `sk-`.
- The source raises before serving if neither condition is true for OpenAI configs.
- The web ChatGPT-only path also needs an OpenAI key supplied by the UI flow, but that is separate from the HuggingGPT backend config.

Hugging Face:

- Config token must start with `hf_`, or env `HUGGINGFACE_ACCESS_TOKEN` must start with `hf_`.
- Required in lite mode because remote model status/inference still uses Hugging Face authorization.
- Do not print token values in diagnostics.

Azure:

- Fill `api_key`, `base_url`, `deployment_name`, and `api_version` in config.
- Source constructs a deployment URL from those fields.
- Source does not implement `AZURE_OPENAI_*` env fallback. If the user wants env-based Azure, they need source changes or a generated config step outside this runtime skill.

## Lite versus default/hybrid

`config.lite.yaml`:

- `inference_mode: huggingface`;
- no local model-server requirement;
- still needs OpenAI and Hugging Face credentials;
- remote model availability can be unstable;
- ControlNet local-only tasks are unavailable.

`config.default.yaml`:

- `inference_mode: hybrid`;
- `local_deployment: full`;
- requires credentials plus local `/running` endpoint;
- intended for a much heavier local stack with GPU/RAM/disk needs in the source README.

When a user says "I used lite and it still fails," check credentials first. When a user says "I used default and it fails before any API route," check the local endpoint gate.

## Local endpoint checklist, unverified path

Only use this if the user explicitly chose `local` or `hybrid` expert-model mode, or asks for local ControlNet.

- Chat server expects local expert endpoint at `http://{local_inference_endpoint.host}:{local_inference_endpoint.port}`.
- It calls `GET /running` before CLI/server begins handling requests.
- Candidate selection may call `GET /status/<model_id>`.
- Execution calls `POST /models/<model_id>`.
- Local model folders and optional CUDA packages are not bundled in this skill and were not verified here.
- `local_deployment: minimal` is still ControlNet-heavy in the source; it is not a no-dependency CPU smoke path.

## Hard usability cases for verification planning

1. **Lite placeholder credentials:** A user runs CLI/server with `config.lite.yaml` unchanged and asks whether they need to download local models. Expected handling: route to the config inspector, report placeholder OpenAI and Hugging Face fields, explain env var fallbacks, and avoid local model-server advice.
2. **Canny/ControlNet in remote mode:** A user asks for canny-guided image generation while `inference_mode: huggingface`. Expected handling: explain that source ControlNet tasks are local-only, suggest verifying or switching to local/hybrid only if they accept the heavy unverified path, and avoid claiming Hugging Face remote ControlNet support.
