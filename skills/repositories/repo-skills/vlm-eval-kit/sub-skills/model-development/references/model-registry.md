# Model registry, discovery, JSON config, and `--base-url`

This reference helps choose the least invasive way to make a model available to VLMEvalKit. It is distilled from `docs/en/Quickstart.md`, `docs/en/ConfigSystem.md`, `run.py`, `vlmeval/tools.py`, `vlmeval/config.py`, `vlmeval/vlm/__init__.py`, `vlmeval/api/__init__.py`, and `tests/test_litellm_api.py`.

## Selection matrix

| User need | Preferred route | Why |
| --- | --- | --- |
| Use a built-in model alias | Existing `supported_VLM` key | No code changes; compatible with `vlmutil mlist` and `run.py --model`. |
| Use built-in class with different kwargs | JSON `--config` model entry | Avoids patching `config.py`; supports local aliases and per-run settings. |
| Use a running OpenAI-compatible service | `run.py --base-url` | Avoids registry edits; maps directly to `LMDeployAPI`. |
| Add a reusable model alias for the package | Edit `vlmeval/config.py` and possibly `vlmeval/vlm/__init__.py` or `vlmeval/api/__init__.py` | Makes the model discoverable by `vlmutil mlist` and standard `--model`. |
| Add dataset-specific prompt/payload behavior for an API endpoint | Adapter in `vlmeval/api/adapters/` plus `custom_prompt` | Keeps provider transport separate from prompt policy. |
| Add a new transport or provider | API subclass in `vlmeval/api/` | Use `BaseAPI` / `OpenAISDKWrapper` contracts. |
| Add a new local model implementation | VLM subclass in `vlmeval/vlm/` | Use `BaseModel` and model-family dependencies. |

Creation-time installed inspection counted 554 `supported_VLM` entries and verified the `vlmutil` discovery path; treat the source registry as canonical because it can change between versions.

## Discover available models

Use `vlmutil mlist` for discovery after VLMEvalKit is installed:

```bash
vlmutil mlist all
vlmutil mlist api
vlmutil mlist 4.37.0
vlmutil mlist 4.37.0 small
vlmutil mlist 4.37.0 large
```

`vlmeval/tools.py` implements `MLIST` as follows:

- `mlist all` returns every key in `supported_VLM`.
- Other categories come from curated model-category lists, with optional `small`/`large` filtering.
- The command prints one model key per line.

When a user says a model is missing, first check spelling and category with `vlmutil mlist all`, then decide between JSON config, `--base-url`, or registry changes.

## How `supported_VLM` is built

`vlmeval/config.py` defines many series dictionaries, for example local VLM families, API model families, LiteLLM aliases, LMDeploy-backed API aliases, video models, and long-tail contributed families. Near the end of the file:

1. Related dictionaries are combined into higher-level series such as `internvl_series` and `interns1_series`.
2. `model_groups` lists all included series dictionaries.
3. Extra series are appended or extended.
4. `supported_VLM = {}` is populated with `supported_VLM.update(grp)` for every group.

A registry entry is usually a `functools.partial` pointing to a class imported through `vlmeval.vlm` or `vlmeval.api`.

## Add a local VLM wrapper to the registry

1. Implement the wrapper in a suitable module under `vlmeval/vlm/` using `BaseModel`.
2. Export the class in `vlmeval/vlm/__init__.py`.
3. Add a series dictionary in `vlmeval/config.py`:

```python
my_series = {
    "MyModel-7B": partial(vlm.MyModel, model_path="org/model-or-local-id", use_custom_prompt=False),
}
```

4. Insert `my_series` into `model_groups` before the loop that updates `supported_VLM`.
5. Verify the key appears in `vlmutil mlist all`.
6. Run `vlmutil check MyModel-7B` only when dependencies, weights, media files, and hardware are available; it constructs the model and calls `generate` on small image prompts.

Keep the registered key stable and descriptive. Avoid embedding machine-specific paths in committed config; if a local path is unavoidable for a private run, prefer JSON config outside the package or environment variables interpreted by your wrapper.

## Add an API provider to the registry

1. Implement the provider under `vlmeval/api/` using `BaseAPI` or `OpenAISDKWrapper`.
2. Export the class in `vlmeval/api/__init__.py` and `__all__`.
3. Add registry entries in `vlmeval/config.py`, normally in an API series dictionary:

```python
my_api_models = {
    "MyVisionAPI": partial(api.MyVisionAPI, model="provider-model", temperature=0, retry=10),
}
```

4. Ensure any credentials are read from environment variables or explicit kwargs, not hard-coded.
5. Verify import and construction without making live calls unless credentials and network access are intentionally provided.

LiteLLM examples already follow this pattern with `api.LiteLLMAPI` entries such as `LiteLLM_GPT4o` and `LiteLLM_Claude_Sonnet4`.

## Use JSON config instead of editing `config.py`

`docs/en/ConfigSystem.md` defines a JSON format with `model` and `data` dictionaries. The key is the run-visible alias; the value either references a class or uses `{}` as a shortcut to an existing registry key.

### Local VLM example

```json
{
  "model": {
    "MyLocalAlias": {
      "class": "MyModel",
      "model_path": "org/model-id",
      "use_custom_prompt": false
    }
  },
  "data": {
    "MMBench_DEV_EN": {}
  }
}
```

### API example

```json
{
  "model": {
    "MyLiteLLMAlias": {
      "class": "LiteLLMAPI",
      "model": "provider/model-name",
      "temperature": 0,
      "max_tokens": 2048,
      "retry": 3
    },
    "GPT4o_20241120": {}
  },
  "data": {
    "MMBench_DEV_EN": {}
  }
}
```

`run.py` resolves `class` names from `vlmeval.api` first, then `vlmeval.vlm`; missing class names raise a clear unsupported-class error. For built-in shortcuts with `{}`, the JSON key must already exist in `supported_VLM`.

## Use `--base-url` instead of registering a model

When a service exposes an OpenAI-compatible chat-completions endpoint, `run.py --base-url` constructs `LMDeployAPI` dynamically:

```bash
python run.py --data DATASET_NAME --model SERVED_MODEL_NAME --base-url http://host:port/v1 --key "$PROVIDER_TOKEN"
```

Rules:

- Pass the API root to `--base-url`; `run.py` appends `/chat/completions`.
- The `--model` value is sent as the provider model name.
- Use `--custom-prompt ADAPTER_NAME` when the served model needs an adapter from `vlmeval/api/adapters/`.
- Use `--video-llm` only if the endpoint accepts native `video_url` payloads.
- Use `--local-media` only if the endpoint can read local file URLs from the same filesystem context.
- Use `--extra-body '{"key": "value"}'` for provider-specific JSON kwargs that are not first-class CLI flags.

If the same endpoint will be reused frequently, promote it to JSON config or `config.py` after the one-off setup is stable.

## Validation snippets

Use these snippets after code edits; they do not make live model calls unless you instantiate a heavy model yourself.

```bash
python - <<'PY'
from vlmeval.config import supported_VLM
print(len(supported_VLM))
print('MyModel-7B' in supported_VLM)
PY
```

```bash
python - <<'PY'
import inspect
from vlmeval.api.litellm_api import LiteLLMAPI
from vlmeval.api.base import BaseAPI
from vlmeval.vlm.base import BaseModel
print(inspect.signature(LiteLLMAPI.__init__))
print(inspect.signature(BaseAPI.generate_inner))
print(inspect.signature(BaseModel.generate_inner))
PY
```

```bash
vlmutil mlist all | grep -x 'MyModel-7B'
```

For execution of `run.py` jobs, status reuse, and result files, switch to the evaluation sub-skill.
