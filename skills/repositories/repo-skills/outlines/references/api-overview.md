# Outlines API overview

Outlines is a Python package for structured output generation. It separates four concerns:

1. **Output type**: the structure to generate (`JsonSchema`, Pydantic class, regex, CFG, choice, Python type).
2. **Model wrapper**: local steerable model or remote/black-box provider.
3. **Prompt/input**: string prompt, `Chat`, or multimodal assets.
4. **Generation call**: direct model call or reusable `Generator`/`Application`.

## Common imports

```python
import outlines
from outlines import Generator, Template
from outlines.inputs import Chat, Image, Audio, Video
from outlines.types import Regex, CFG, JsonSchema, Choice
```

`Chat` is in `outlines.inputs`. Top-level `outlines` exports `Image`, `Audio`, and `Video`, but using `outlines.inputs` keeps all input carriers together.

## Model categories

### Local steerable models

Local wrappers expose logits/structured decoding control:

```python
model = outlines.from_transformers(hf_model, hf_tokenizer)
model = outlines.from_llamacpp(llama)
model = outlines.from_mlxlm(mlx_model, tokenizer)
model = outlines.from_vllm_offline(vllm_llm)
```

Use `sub-skills/local-models/SKILL.md` for setup and `sub-skills/structured-generation/SKILL.md` for output types/backends.

### Remote/server providers

Provider wrappers adapt an existing SDK/client object:

```python
model = outlines.from_openai(openai_client, "gpt-4o")
model = outlines.from_anthropic(anthropic_client, model_name)
model = outlines.from_tgi(inference_client)
model = outlines.from_vllm(openai_client, model_name)
```

Provider wrappers are black-box/server routes with provider-specific structured output formats, async/stream support, and error normalization.

## Generation calls

Direct call:

```python
raw = model("Classify this review", output_type, max_new_tokens=100)
```

Reusable generator:

```python
generator = Generator(model, output_type)
raw = generator("Classify this review", max_new_tokens=100)
```

Reusable application:

```python
template = Template.from_string("Summarize: {{ text }}")
app = outlines.Application(template, output_type)
raw = app(model, {"text": "..."}, max_new_tokens=100)
```

Raw structured output usually needs caller-side parsing:

```python
obj = Schema.model_validate_json(raw)
```

## Output type choices

- `int`, `float`, `bool`, `list[...]`, `dict[...]`: simple structured output.
- `Literal`, `Enum`, `Choice`: finite labels.
- Pydantic/dataclass/TypedDict/GenSON/`JsonSchema`: JSON objects.
- `Regex`: regular languages.
- `CFG`: context-free grammar constraints.
- Custom `OutlinesLogitsProcessor`: advanced local-model control only.

## Inputs

- Plain `str`: supported by all model routes.
- `Chat`: message history with `role` and `content` fields.
- `[prompt, Image(...)]`: multimodal input for wrappers/providers that support vision.
- `Audio`/`Video`: wrappers whose actual support is model/provider specific.

## Exception model

Remote providers normalize supported SDK errors into `outlines.exceptions.APIError` subclasses such as `AuthenticationError`, `RateLimitError`, `ServerError`, `APITimeoutError`, and `GenerationError`. Local model wrappers preserve native runtime exceptions.
