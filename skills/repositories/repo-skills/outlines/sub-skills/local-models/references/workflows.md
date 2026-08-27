# Local model workflows

## Transformers text workflow

```python
import outlines
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Literal

model_id = "HuggingFaceTB/SmolLM2-135M-Instruct"
hf_model = AutoModelForCausalLM.from_pretrained(model_id)
hf_tokenizer = AutoTokenizer.from_pretrained(model_id)
model = outlines.from_transformers(hf_model, hf_tokenizer)

answer = model("Answer yes or no: is 2+2=4?", Literal["yes", "no"], max_new_tokens=5)
```

Checklist:

- Use a model small enough for the available device.
- If a tokenizer lacks `pad_token_id`, Outlines sets pad to eos where needed.
- If the tokenizer has a chat template, string input may be formatted as a user message; if not, pass the exact prompt string you want the model to see.
- Use `backend=` only after checking backend compatibility.

## Transformers multimodal workflow

```python
from outlines.inputs import Image, Chat

prompt = ["<image>Describe this image in one sentence.", Image(pil_image)]
response = model(prompt, max_new_tokens=32)
```

For chat-style multimodal input:

```python
chat = Chat([
    {"role": "system", "content": "You are concise."},
    {"role": "user", "content": ["Describe this image", Image(pil_image)]},
])
response = model(chat, max_new_tokens=32)
```

Keep the number of `Image` objects consistent with the processor/model prompt format.

## llama.cpp workflow

```python
from llama_cpp import Llama
import outlines
from outlines.types import Regex

llama = Llama.from_pretrained(repo_id="org/model-gguf", filename="model.Q4_K_M.gguf")
model = outlines.from_llamacpp(llama, chat_mode=True)
response = model("Give one digit", Regex(r"[0-9]"), max_tokens=8)
```

Checklist:

- Confirm `llama-cpp-python` installed with the intended CPU/GPU build options.
- Verify model file format and chat format.
- Use `max_tokens` for llama.cpp-style generation parameters.
- Do not use batch generation; stream if needed.

## MLX-LM workflow

```python
import mlx_lm
import outlines

mlx_model, tokenizer = mlx_lm.load("mlx-community/SmolLM-135M-Instruct-4bit")
model = outlines.from_mlxlm(mlx_model, tokenizer)
```

Use only on Apple Silicon/macOS with MLX available. On Linux, choose Transformers or a provider/server route.

## vLLM offline workflow

```python
from vllm import LLM, SamplingParams
import outlines

llm = LLM("microsoft/Phi-3-mini-4k-instruct")
model = outlines.from_vllm_offline(llm)
response = model("Give one digit", int, sampling_params=SamplingParams(max_tokens=8))
```

Checklist:

- Confirm GPU, driver, CUDA, torch, and vLLM compatibility before constructing `LLM`.
- Use `SamplingParams` for vLLM-specific generation options.
- Use `from_vllm` instead when connecting to a running vLLM OpenAI-compatible server.

## No-network prerequisite check

Before setup, run:

```bash
python scripts/check_local_model_prereqs.py --targets transformers llamacpp mlxlm vllm-offline --format text
```

This only reports module/device visibility. It does not prove a model can generate.

## Routing structured outputs

After the local model object exists, select the output type in `../../structured-generation/SKILL.md`: 

```python
from pydantic import BaseModel

class Person(BaseModel):
    first_name: str
    last_name: str

raw = model("Extract a person from: Ada Lovelace", Person, max_new_tokens=100)
person = Person.model_validate_json(raw)
```

If the output type fails because of backend support, fix `backend=` or route to the structured-generation troubleshooting reference.
