# VLMEvalKit model and API invocation contracts

This reference covers implementation contracts for model wrappers and API providers. It is distilled from `docs/en/Development.md`, `docs/en/Quickstart.md`, `docs/en/EvalByLMDeploy.md`, `run.py`, `vlmeval/vlm/base.py`, `vlmeval/api/base.py`, `vlmeval/api/litellm_api.py`, `vlmeval/api/lmdeploy.py`, `vlmeval/api/openai_sdk.py`, and `tests/test_litellm_api.py`.

## Common message format

VLMEvalKit model-side and API-side wrappers normalize user inputs into a list of dictionaries:

| Accepted raw input | Normalized form |
| --- | --- |
| `"question"` | `[{'type': 'text', 'value': 'question'}]` |
| `{'type': 'text', 'value': 'question'}` | one-item list |
| `['image.jpg', 'question']` | strings are parsed as media paths/URLs when possible, otherwise text |
| `[{'type': 'image', 'value': 'image.jpg'}, {'type': 'text', 'value': 'question'}]` | used directly after validation |

Allowed content types are `text`, `image`, and `video`. Paths and URLs are validated through VLMEvalKit file parsing before the inner generation method is called. A wrapper must not assume raw strings reach `generate_inner()` unchanged.

## `BaseModel` contract for local VLM wrappers

`BaseModel` lives in `vlmeval/vlm/base.py` and is the base contract for local or package-backed VLM classes.

| Surface | Required? | Behavior to preserve |
| --- | --- | --- |
| `INTERLEAVE` | optional class attr, default `False` | Set `True` only when the model can consume arbitrarily interleaved image/text messages. |
| `allowed_types` | inherited | Keep `text`, `image`, `video` unless intentionally narrowing behavior. |
| `generate(message, dataset=None)` | inherited | Validates/preprocesses input and calls `generate_inner(message, dataset)`. Return should be the prediction string. |
| `generate_inner(message, dataset=None)` | required | Feed the normalized message list to the model and return a string answer. |
| `chat(messages, dataset=None)` | inherited | Normalizes each role-keyed turn, retries by dropping old turns after exceptions, and calls `chat_inner`. |
| `chat_inner(messages, dataset=None)` | optional | Add only if the model supports multi-turn history; last turn should be a user turn. |
| `use_custom_prompt(dataset)` | optional | Return `True` only for datasets where the model wrapper should override dataset prompt construction. |
| `build_prompt(line, dataset)` | optional with custom prompt | Return a VLMEvalKit multimodal message list for the sample line. |
| `set_dump_image(dump_image_func)` | inherited | Store the dataset image-dump callback used by custom prompt builders. |
| `message_to_promptimg(message, dataset=None)` | inherited helper | For non-interleaved image models: concatenate text and choose the first image; BLINK concatenates images. |
| `message_to_promptvideo(message)` / `message_to_promptvideo_withrole(...)` | inherited helpers | Require `self.VIDEO_LLM`; otherwise raise unsupported-video errors. |
| `message_to_lmdeploy(messages, system_prompt=None)` | helper | Converts image messages to LMDeploy/OpenAI-compatible image-url payloads. Requires LMDeploy/PIL dependencies. |

### Minimal local wrapper skeleton

```python
from vlmeval.vlm.base import BaseModel

class MyModel(BaseModel):
    INTERLEAVE = False

    def __init__(self, model_path=None, **kwargs):
        super().__init__()
        # load tokenizer/model/client here when dependencies and weights exist

    def generate_inner(self, message, dataset=None):
        prompt, image = self.message_to_promptimg(message, dataset=dataset)
        # call the model and return a plain string
        return "..."
```

Add `chat_inner()` only when the backend can consume VLMEvalKit chat history. Add `use_custom_prompt()` and `build_prompt()` only when the model genuinely needs dataset-specific prompt construction; otherwise rely on dataset prompts.

## `BaseAPI` contract for API wrappers

`BaseAPI` lives in `vlmeval/api/base.py` and handles retry, wait, system prompt, role preprocessing, and failure fallback for API providers.

| Surface | Default / required behavior |
| --- | --- |
| `__init__(retry=10, wait=1, system_prompt=None, verbose=True, fail_msg='Failed to obtain answer via API.', **kwargs)` | Store retry behavior and any default generation kwargs. |
| `generate_inner(inputs, **kwargs)` | Required. Return `(ret_code, answer, log)`. `ret_code == 0` means success. |
| `generate(message, **kwargs)` | Validates content, merges default kwargs with call kwargs, retries `generate_inner`, and returns an answer string. If `log` is a dict on success, it returns `{'prediction': answer, 'extra_records': log}`. |
| `chat(messages, **kwargs)` | Normalizes role-keyed turns, asserts the last turn is `user`, merges kwargs, retries `chat_inner`, and returns the answer string or `fail_msg`. |
| `chat_inner(inputs, **kwargs)` | Default implementation calls `generate_inner` on shrinking histories; override only for provider-specific chat behavior. |
| `preprocess_message_with_role(message)` | Extracts `role='system'` text into `self.system_prompt` and leaves the rest as user/media messages. |
| `verbose` | Enables answer printing and ret-code/log/error diagnostics. |
| `wait` | Used to sleep for a random delay before retries. |
| `fail_msg` | Returned when all attempts fail or answer is empty; avoid returning this string on success. |

### Minimal API wrapper skeleton

```python
from vlmeval.api.base import BaseAPI

class MyAPI(BaseAPI):
    is_api = True

    def __init__(self, model, key=None, api_base=None, **kwargs):
        self.model = model
        self.key = key
        self.api_base = api_base
        super().__init__(**kwargs)

    def generate_inner(self, inputs, **kwargs):
        # inputs is a list of {'type': ..., 'value': ...} dicts
        try:
            answer = "..."  # call provider
            return 0, answer, {"provider": "myapi"}
        except Exception as err:
            return -1, self.fail_msg, str(err)
```

## LiteLLM provider contract

`LiteLLMAPI` in `vlmeval/api/litellm_api.py` is a `BaseAPI` subclass for LiteLLM-supported providers. Creation-time native tests exercise construction, message preparation, kwargs forwarding, config registration, and error paths with mocked LiteLLM; they do not prove live provider access.

### Constructor

```python
LiteLLMAPI(
    model='gpt-4o',
    key=None,
    api_base=None,
    retry=10,
    wait=1,
    system_prompt=None,
    verbose=True,
    temperature=0,
    max_tokens=2048,
    timeout=300,
    img_size=-1,
    litellm_kwargs={...},
    **kwargs,
)
```

Important behavior:

- `key` overrides `LITELLM_API_KEY`; if neither is set, no `api_key` argument is passed to LiteLLM.
- `api_base` overrides `LITELLM_API_BASE`; if neither is set, no `api_base` argument is passed.
- `litellm_kwargs` is merged first into `litellm.completion(...)`, then the wrapper adds `model`, `messages`, `temperature`, `max_tokens`, `timeout`, and `drop_params=True`.
- Text-only input becomes one user content item with newline-joined text.
- Image input is opened with PIL, encoded as `data:image/jpeg;base64,...`, and sent as `image_url` content. `img_size` is forwarded to the image encoder.
- `system_prompt` is inserted as a system message before the user message.
- If LiteLLM is not installed, `generate_inner()` raises an import error with an install hint.
- Provider exceptions are caught in `generate_inner()` and returned as `(-1, fail_msg, str(err))`; `BaseAPI.generate()` then applies retry/fallback behavior.

### LiteLLM registry examples

`vlmeval/config.py` contains LiteLLM entries such as `LiteLLM_GPT4o`, `LiteLLM_GPT4o_Mini`, `LiteLLM_Claude_Sonnet4`, `LiteLLM_Gemini_2.5_Flash`, `LiteLLM_Gemini_2.5_Pro`, `LiteLLM_Bedrock_Claude`, `LiteLLM_Llama_Vision`, and `LiteLLM_Groq_Llama4`.

Use a JSON config when the provider string or kwargs differ from those built-ins:

```json
{
  "model": {
    "MyLiteLLMVision": {
      "class": "LiteLLMAPI",
      "model": "provider/model-name",
      "temperature": 0,
      "max_tokens": 2048,
      "litellm_kwargs": {"drop_params": true}
    }
  },
  "data": {
    "MMBench_DEV_EN": {}
  }
}
```

## LMDeploy and OpenAI-compatible API route

`LMDeployAPI` in `vlmeval/api/lmdeploy.py` subclasses `OpenAISDKWrapper` and is used both for LMDeploy-served models and generic OpenAI-compatible endpoints.

### Constructor and environment

`LMDeployWrapper.__init__` accepts `model`, `key`, `api_base`, `custom_prompt`, `video_llm`, `local_media`, `timeout`, `retry`, `wait`, `system_prompt`, `stream`, and generation kwargs. It resolves:

- `LMDEPLOY_API_KEY` when `key` is not provided.
- `LMDEPLOY_API_BASE` when `api_base` is not provided. In config/env usage this should be the full chat-completions endpoint URL.
- `VLMEVAL_LOCAL_MEDIA=1` or `local_media=True` to send `file://...` media paths instead of base64 data URLs.

### `run.py --base-url` route

When `--base-url` is supplied, `run.py` builds `LMDeployAPI` kwargs without editing `vlmeval/config.py`:

- The model name is taken from `--model`.
- `api_base` becomes `BASE_URL.rstrip('/') + '/chat/completions'`; pass the API root such as `http://host:port/v1`, not the full `/chat/completions` path.
- `--custom-prompt` selects a registered adapter by name.
- `--max-tokens`, `--timeout`, `--temperature`, `--top-k`, `--top-p`, `--repetition-penalty`, `--stream`, `--video-llm`, `--local-media`, and `--extra-body` become generation/provider kwargs.

Command shape:

```bash
python run.py --data DATASET_NAME --model SERVED_MODEL_NAME --base-url http://host:port/v1 --key "$PROVIDER_TOKEN" --custom-prompt internvl3
```

For actual evaluation-job planning, switch to the evaluation sub-skill; this reference only defines the model construction route.

### Payload behavior

- Image messages are sent as `image_url` entries. By default images are base64 data URLs; with local media enabled, they are `file://` URLs.
- Video messages are sent as `video_url` entries. Native video requires `video_llm=True` and a server that understands that format.
- Text-only messages are newline-joined into one content item.
- Role-keyed multi-turn messages are preserved, and the last turn must be `user`.
- Adapter hooks can override model args, rewrite inputs, mutate the HTTP payload, and postprocess the response.

## Compatibility notes for local wrappers

`README.md` lists model-family-specific dependency recommendations. Treat them as first-line triage when a local wrapper imports but fails at runtime:

- `transformers` versions vary by model family; examples include older pins for Qwen/InternVL/LLaVA-era models and newer or latest versions for PaliGemma, Ovis, Idefics-3, GLM-4v, Video-LLaVA-HF, Molmo, and Qwen3.5.
- Some models need `torchvision>=0.16`, notably Moondream series and Aria.
- Aria documents `pip install flash-attn --no-build-isolation`.
- Performance and exact scores are environment-sensitive across `transformers`, CUDA, and torch versions.

Do not present a dependency import check as proof of large-model correctness. Real local VLM behavior requires model weights, compatible hardware, and a task-specific evaluation or smoke prompt.
