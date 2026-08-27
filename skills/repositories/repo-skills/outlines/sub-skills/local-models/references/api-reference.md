# Local model API reference

Outlines local wrappers adapt an already-created model/client object from the underlying inference library. They are steerable: Outlines can pass logits processors to constrain generation for supported output types.

## Loader signatures

Verified from the installed package:

```text
from_transformers(model, tokenizer_or_processor, *, device_dtype=None)
from_llamacpp(model, chat_mode=True)
from_mlxlm(model, tokenizer)
from_vllm_offline(model)
```

## Transformers

```python
import outlines
from transformers import AutoModelForCausalLM, AutoTokenizer

hf_model = AutoModelForCausalLM.from_pretrained("HuggingFaceTB/SmolLM2-135M-Instruct")
hf_tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-135M-Instruct")
model = outlines.from_transformers(hf_model, hf_tokenizer)
```

Notes:

- Text Transformers use a `TransformerTokenizer` wrapper and tensor library `torch`.
- If the tokenizer has a chat template, string prompts may be formatted as user chat messages.
- `device_dtype` can be supplied when the underlying model supports it.
- Batch generation is implemented for text Transformers. Streaming raises `NotImplementedError` in this source revision.
- Multimodal Transformers are created by passing a compatible processor object instead of a plain tokenizer.

## Transformers multimodal

```python
from outlines.inputs import Image, Chat

model = outlines.from_transformers(vision_language_model, processor)
response = model(["<image>Describe this image", Image(pil_image)], max_new_tokens=32)
```

The prompt/asset shape must match the underlying processor and model. `Image` requires a PIL image with a real `format` value.

## llama.cpp

```python
from llama_cpp import Llama
import outlines

llama = Llama.from_pretrained(repo_id="...", filename="...")
model = outlines.from_llamacpp(llama, chat_mode=True)
```

Notes:

- Tensor library is `numpy`.
- `chat_mode=True` uses chat formatting where the underlying model supports it.
- Streaming is implemented; batch tokenization/generation is not supported.
- CFG/JSON/regex/choice support depends on backend compatibility and installed optional packages.

## MLX-LM

```python
import mlx_lm
import outlines

mlx_model, tokenizer = mlx_lm.load("mlx-community/SmolLM-135M-Instruct-4bit")
model = outlines.from_mlxlm(mlx_model, tokenizer)
```

Notes:

- Intended for Apple Silicon/macOS; Linux CPU hosts should not treat it as available.
- Tensor library is `mlx`.
- Batch generation exists for plain text, but constrained generation with batching is not supported in the tested source behavior.

## vLLM offline

```python
from vllm import LLM
import outlines

llm = LLM("microsoft/Phi-3-mini-4k-instruct")
model = outlines.from_vllm_offline(llm)
```

Notes:

- This is not the same as `from_vllm` server mode.
- The wrapper uses vLLM `SamplingParams` and structured output parameters for guided decoding.
- Batch generation is implemented for text prompts; batch `Chat` inputs are rejected.
- Streaming is not available in this wrapper revision.
- A GPU-capable vLLM installation and model weights are normally required.

## Calling local models

All local wrappers follow the model call pattern:

```python
raw = model(prompt, output_type=None, backend=None, **inference_kwargs)
```

For structured output:

```python
from typing import Literal
raw = model("yes or no?", Literal["yes", "no"], max_new_tokens=8)
```

For reusable constraints:

```python
generator = outlines.Generator(model, OutputSchema, backend="outlines_core")
raw = generator(prompt, max_new_tokens=200)
```

See `../../structured-generation/SKILL.md` for output-type and backend choices.
