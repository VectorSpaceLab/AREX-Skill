# HuggingGPT chat orchestration

Source evidence names: README.md; hugginggpt/README.md; hugginggpt/server/awesome_chat.py; hugginggpt/server/demos/demo_parse_task.json; hugginggpt/server/demos/demo_choose_model.json; hugginggpt/server/demos/demo_response_results.json.

## Runtime surfaces

HuggingGPT's chat controller is implemented by `awesome_chat.py`. It supports these user-facing surfaces:

| Surface | Source mode | What the user gets | Important constraints |
|---|---|---|---|
| CLI | `--mode cli` | Terminal prompt that keeps a `messages` history until the user types `exit`. | Requires a configured controller endpoint at startup; route-level dynamic endpoint fields are not available. |
| Server/API | `--mode server` | Waitress/Flask app serving `/hugginggpt`, `/tasks`, and `/results`. | Uses `http_listen.host` and `http_listen.port`; CORS is enabled; credentials can come from config/env or per-request route fields. |
| Test | `--mode test` | Hard-coded demonstration prompts. | Source-level smoke/demo mode; do not treat as a production verifier. |
| Gradio-style import path | module imported instead of run as `__main__` | Source sets mode to `gradio` and default config to `configs/config.gradio.yaml`. | The full Gradio app is outside this sub-skill; use this only to explain why gradio config lacks normal server fields. |

The controller creates relative runtime output folders named `logs`, `public/images`, `public/audios`, and `public/videos` when it starts. Future agents should describe those as server working-directory outputs, not as guaranteed persistent skill files.

## Four-stage controller loop

A full `/hugginggpt` request runs `chat_huggingface(messages, ...)`, which implements the paper's four stages:

1. **Task planning** via `parse_task(context, input, ...)`.
   - `context` is every chat message except the last; `input` is the last message content.
   - Prompt text, system task prompt, logit bias, and demonstration presteps come from config fields.
   - The controller truncates earlier chat history when token budget would leave 800 or fewer tokens for the response.
   - The expected task JSON is a list of objects with `task`, `id`, `dep`, and `args` fields.
2. **Model selection** via `choose_model(input, task, metas, ...)` when more than one available model exists.
   - Candidate model metadata comes from `data/p0_models.jsonl` and is truncated by `max_description_length`.
   - The LLM is asked to return strict JSON: `{"id": "...", "reason": "..."}`.
   - If the model-selection response is not valid JSON, the code attempts a best-effort field extraction for `id` and `reason`.
3. **Task execution** via `run_task(...)` and `model_inference(...)`.
   - Independent tasks can run in threads once dependencies are satisfied.
   - Dependency placeholders like `<GENERATED>-0` are replaced with generated text, image, or audio from prior results.
   - Summarization, translation, conversational, text-generation, and text2text-generation tasks are handled directly by the controller LLM instead of a Hugging Face model.
   - Remote Hugging Face model calls and optional local model-server calls are separated by `hosted_on`.
4. **Response generation** via `response_results(input, results, ...)`.
   - The LLM receives the execution logs and is prompted to answer directly, summarize the workflow, include relevant model outputs, and report when no useful result exists.

## Task schema and dependency behavior

A planned task should look like:

```json
{
  "task": "image-to-text",
  "id": 0,
  "dep": [-1],
  "args": {"image": "sample.jpg"}
}
```

Key conventions:

- `dep: [-1]` means the task can start from the original user inputs.
- `dep: [0]` means the task waits for task `0`.
- `args` should use only `text`, `image`, or `audio` keys.
- `<GENERATED>-N` refers to a generated resource from task `N`.
- `fix_dep` recomputes dependencies from `<GENERATED>-N` placeholders when needed.
- `unfold` splits a task that names multiple generated dependencies in one argument.
- For local files, `run_task` prepends `public/` unless the value already starts with `public/` or `http`.

The task-planning prompt allows NLP, vision, audio, video, document question answering, visual question answering, image-to-image, image-to-text, text-to-image, depth estimation, ControlNet preprocessing tasks, and ControlNet text-to-image tasks. The detailed model catalog is summarized in `model-and-endpoint-reference.md`.

## API routes

All three routes are POST routes that expect JSON. The common request shape is:

```json
{
  "messages": [
    {"role": "user", "content": "Describe sample.jpg and answer a question about it."}
  ]
}
```

Server routes accept optional override fields:

```json
{
  "messages": [{"role": "user", "content": "Summarize this text."}],
  "api_type": "openai",
  "api_endpoint": "https://api.openai.com/v1/completions",
  "api_key": "<redacted>"
}
```

Do not paste real keys into examples, logs, or handoffs.

| Route | Function | Return shape | Use when |
|---|---|---|---|
| `/hugginggpt` | full four-stage flow | Usually `{"message": "..."}`. Errors from parsing or inference can also be summarized in `message`. | User wants the final Jarvis answer. |
| `/tasks` | planning only (`return_planning=True`) | A JSON array of planned tasks. | User wants to debug task decomposition or inspect Stage 1 without executing models. |
| `/results` | planning, model selection, and execution (`return_results=True`) | A JSON object/dict keyed by task id, each containing the task, choose-model result, and inference result. | User wants Stage 1-3 intermediate evidence without response-generation prose. |

If `api_key`, `api_type`, or `api_endpoint` is unavailable globally and absent from a route request, the route returns an error asking for those fields. CLI and test modes assert a configured endpoint at startup and cannot use per-request dynamic fields.

## API endpoint type selection

At startup the source picks a controller LLM API type with this priority:

1. `dev: true` means a local OpenAI-compatible controller endpoint under `local.endpoint`.
2. An `azure` config block means Azure OpenAI.
3. An `openai` config block means OpenAI.
4. If none is present, server mode can still accept per-request dynamic endpoint fields, but CLI/test cannot start.

`use_completion: true` selects `/v1/completions` and converts chat messages into a completion-style prompt. `use_completion: false` selects `/v1/chat/completions`.

## Local endpoint gate

When `inference_mode` is not `huggingface`, `awesome_chat.py` constructs a local model-server URL from `local_inference_endpoint.host` and `.port`, then calls `/running` before serving CLI or API traffic. If that request fails, startup fails with a message telling the user to start the local inference endpoint or switch to `inference_mode: huggingface` for a feature-limited experience.

This sub-skill did not verify the heavy local model server. For local/hybrid CUDA operation, treat `/running`, `/status/<model_id>`, and `/models/<model_id>` as source-defined endpoints that need separate environment and model validation.

## Practical request debugging sequence

1. Run the bundled config inspector against the exact config file or named config.
2. If using CLI, make sure the config has a valid OpenAI/Azure/local controller endpoint and a valid Hugging Face token or matching env var.
3. If using server mode, check the server's `http_listen` host/port and test `/tasks` before `/hugginggpt` to isolate task planning from model execution.
4. If `/tasks` succeeds but `/results` fails, inspect the planned task names, dependency placeholders, and model availability.
5. If a planned task is ControlNet-related in `inference_mode: huggingface`, route the user to the documented local-only limitation instead of searching for remote ControlNet endpoints.
