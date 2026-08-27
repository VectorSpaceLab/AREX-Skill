# Playground and API reference

The API server keeps one loaded model in module-global state and runs a single-worker Uvicorn process. The playground loads the model inside the Gradio app after the user clicks **Load**.

## Gradio playground behavior

### Construction and defaults

```python
from xturing.ui.playground import Playground

Playground()
Playground(model_path="/path/to/model")
```

Default generation settings inside the playground:

- `penalty_alpha = None`
- `top_k = None`
- `top_p = 0.92`
- `do_sample = True`
- `max_new_tokens = 256`

### Load flow

- the visible UI expects a model path
- the load button calls `BaseModel.load(model_path)`
- after a successful load, the prompt box becomes interactive
- `Clear chat` clears the chat history only
- the decoding radio switches between top-p sampling and contrastive search controls
- an empty prompt returns `Enter a valid prompt`
- generation failures are shown as a friendly error message in the UI

### UI notes

- the current visible controls load from a path textbox
- a `model_name` branch exists in code for a small built-in map, but the public UI does not surface it
- the chat pane shows a conversational history and prefixes model replies in the display layer

## Health and docs routes

### `/health`

Response shape:

```json
{"success": true, "message": "API server is running"}
```

The FastAPI application also exposes its standard interactive documentation routes when enabled by FastAPI defaults.

## Legacy `/api`

### Request body

```json
{
  "prompt": "Write a short summary" ,
  "params": {
    "penalty_alpha": 0.6,
    "top_k": 50,
    "top_p": 1.0,
    "do_sample": false,
    "max_new_tokens": 256
  }
}
```

Schema summary:

- `prompt`: string or list of strings
- `params`: optional generation config wrapper

`Params` fields:

- `penalty_alpha`
- `top_k`
- `top_p`
- `do_sample`
- `max_new_tokens`

Behavior:

- prompt lists are forwarded unchanged to model generation
- the active model generation config is updated before generation
- success response shape: `{"success": true, "response": ...}`
- failure response shape: `{"success": false, "message": "..."}`

## OpenAI-compatible routes

### `/v1/models`

Response shape:

```json
{
  "object": "list",
  "data": [
    {"id": "<model_id>", "object": "model"}
  ]
}
```

- `model_id` comes from the loaded model name when available
- if no model is loaded, the route returns HTTP 503

### `/v1/chat/completions`

Request shape:

```json
{
  "model": "optional-model-id",
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Say hi"}
  ],
  "temperature": 0.2,
  "top_p": 0.9,
  "max_tokens": 128,
  "stream": false,
  "n": 1
}
```

Rules:

- `messages` must not be empty
- `n` must be `1`
- messages are converted to a plain prompt by joining `"role: content"` lines with newlines
- `temperature > 0` enables sampling and clears `penalty_alpha`
- `top_p` also enables sampling and clears `penalty_alpha`
- `max_tokens` maps to `max_new_tokens`

Non-stream response shape:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "optional-model-id",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  }
}
```

Streaming skeleton:

- server-sent events are returned
- the first chunk contains the full assistant output in `delta.content`
- the second chunk marks `finish_reason: "stop"`
- the stream ends with `data: [DONE]`
- this is a skeleton, not token-by-token streaming

### `/v1/completions`

Request shape:

```json
{
  "model": "optional-model-id",
  "prompt": "Summarize xTuring in one sentence.",
  "temperature": 0.2,
  "top_p": 0.9,
  "max_tokens": 64,
  "stream": false,
  "n": 1
}
```

Rules:

- `prompt` may be a string or a list of strings
- `n` must be `1`
- list prompts are forwarded as a list and produce one choice per prompt item
- `max_tokens` maps to `max_new_tokens`

Non-stream response shape:

```json
{
  "id": "cmpl-...",
  "object": "text_completion",
  "created": 1700000000,
  "model": "optional-model-id",
  "choices": [
    {"index": 0, "text": "...", "finish_reason": "stop"}
  ],
  "usage": {
    "prompt_tokens": 6,
    "completion_tokens": 8,
    "total_tokens": 14
  }
}
```

Streaming skeleton:

- server-sent events are returned
- each output choice is emitted as a `text_completion` chunk
- a final stop chunk is emitted for all choices
- the stream ends with `data: [DONE]`

## Usage accounting

- usage counts are rough whitespace-token estimates
- they are intended for lightweight compatibility, not exact tokenizer accounting
