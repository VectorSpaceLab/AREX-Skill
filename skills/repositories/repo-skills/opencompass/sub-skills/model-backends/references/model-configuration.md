# Model Configuration

OpenCompass model configs are Python dictionaries in a `models = [...]` list. The `type` value names the backend wrapper class; wrapper-constructor arguments live beside common OpenCompass runtime fields such as `abbr`, `max_out_len`, `batch_size`, and `run_cfg`.

## HuggingFace Models

Use HuggingFace wrappers when the model can be loaded through Transformers-style `from_pretrained()` APIs.

```python
from opencompass.models import HuggingFaceCausalLM

models = [
    dict(
        type=HuggingFaceCausalLM,
        abbr='llama-7b-local',
        path='huggyllama/llama-7b',
        tokenizer_path='huggyllama/llama-7b',
        tokenizer_kwargs=dict(
            padding_side='left',
            truncation_side='left',
            trust_remote_code=True,
        ),
        model_kwargs=dict(
            device_map='auto',
            trust_remote_code=True,
            torch_dtype='auto',
        ),
        max_seq_len=2048,
        max_out_len=100,
        batch_size=8,
        batch_padding=False,
        run_cfg=dict(num_gpus=1),
    )
]
```

Key fields:

- `type`: commonly `HuggingFaceCausalLM` for `AutoModelForCausalLM`, `HuggingFace` for generic `AutoModel`, or `HuggingFacewithChatTemplate` for chat-template-aware models.
- `path`: HuggingFace repo id or model directory.
- `tokenizer_path`: optional tokenizer repo/directory; defaults to `path` for most HF wrappers.
- `tokenizer_kwargs`: forwarded to `AutoTokenizer.from_pretrained()`. Common values include `padding_side='left'`, `truncation_side='left'`, and `trust_remote_code=True`.
- `model_kwargs`: forwarded to model loading. Common values include `device_map='auto'`, `trust_remote_code=True`, and `torch_dtype='auto'`, `'torch.float16'`, or `'torch.bfloat16'` depending on hardware/backend support.
- `max_seq_len`: maximum input/context length used by OpenCompass and the wrapper.
- `max_out_len`: generation token budget passed during inference.
- `batch_size`: OpenCompass inference batch size. Lower it first for memory pressure.
- `batch_padding`: `False` evaluates samples individually inside a batch; `True` pads and batches together when the model/tokenizer safely supports it.
- `pad_token_id`: set this explicitly when tokenizer loading reports no pad token and EOS fallback is not acceptable.
- `run_cfg`: scheduler resource request, usually `dict(num_gpus=1)` for local GPU models and `dict(num_gpus=0)` for external APIs.

## CLI HF Flags to Config Fields

The `opencompass` CLI exposes HuggingFace model flags for quick one-off runs. Convert them into reusable configs before sharing or debugging complex evaluations:

| CLI intent | Config field |
| --- | --- |
| model id/path | `path` |
| tokenizer id/path | `tokenizer_path` |
| max sequence length | `max_seq_len` |
| max output tokens | `max_out_len` |
| batch size | `batch_size` |
| model loading kwargs | `model_kwargs` |
| tokenizer loading kwargs | `tokenizer_kwargs` |
| GPU count/resource need | `run_cfg=dict(num_gpus=...)` |

Example conversion with left padding and explicit resources:

```python
from opencompass.models import HuggingFaceCausalLM

models = [
    dict(
        type=HuggingFaceCausalLM,
        abbr='qwen-chat-hf',
        path='Qwen/Qwen-7B-Chat',
        tokenizer_path='Qwen/Qwen-7B-Chat',
        tokenizer_kwargs=dict(padding_side='left', truncation_side='left', trust_remote_code=True),
        model_kwargs=dict(device_map='auto', trust_remote_code=True, torch_dtype='auto'),
        max_seq_len=4096,
        max_out_len=512,
        batch_size=4,
        batch_padding=False,
        run_cfg=dict(num_gpus=1),
    )
]
```

## Chat Template Models

Use `HuggingFacewithChatTemplate` or backend-specific chat-template wrappers when the tokenizer's `apply_chat_template()` behavior is required. Keep backend setup here, but route detailed prompt/template design to the prompt-and-inference sub-skill.

```python
from opencompass.models import HuggingFacewithChatTemplate

models = [
    dict(
        type=HuggingFacewithChatTemplate,
        abbr='llama3-8b-instruct-hf',
        path='meta-llama/Meta-Llama-3-8B-Instruct',
        tokenizer_kwargs=dict(trust_remote_code=True),
        model_kwargs=dict(device_map='auto', trust_remote_code=True, torch_dtype='auto'),
        max_seq_len=8192,
        max_out_len=1024,
        batch_size=8,
        stop_words=['<|end_of_text|>', '<|eot_id|>'],
        run_cfg=dict(num_gpus=1),
    )
]
```

## Custom Model Extension Route

Use a custom wrapper when the model cannot be expressed as an existing HF/API/accelerated backend.

- API-like services should inherit `BaseAPIModel`, set `is_api = True`, and implement `generate()` and `get_token_len()`.
- Local/third-party models should inherit `BaseModel` and implement `generate()`, `get_ppl()` when discriminative evaluation is needed, and `get_token_len()`.
- Place the wrapper in importable project code and reference it in config with `type=YourModelClass`; do not encode large implementation logic inside config files.
- Preserve common fields (`abbr`, `max_out_len`, `batch_size`, `run_cfg`) so OpenCompass runners and summarizers behave consistently.

Minimal API-wrapper shape:

```python
from opencompass.models.base_api import BaseAPIModel

class MyModelAPI(BaseAPIModel):
    is_api = True

    def generate(self, inputs, max_out_len=512):
        ...

    def get_token_len(self, prompt: str) -> int:
        ...
```

Minimal local-wrapper shape:

```python
from opencompass.models.base import BaseModel

class MyModel(BaseModel):
    def generate(self, inputs, max_out_len=512):
        ...

    def get_ppl(self, inputs, mask_length=None):
        ...

    def get_token_len(self, prompt: str) -> int:
        ...
```

## Resource and Batch Sizing

- Use `run_cfg=dict(num_gpus=0)` for remote API calls that do not need local GPU allocation.
- Use `run_cfg=dict(num_gpus=1)` or higher for local HF, vLLM, and LMDeploy runs; add `num_procs` only when the runner configuration expects multiple worker processes.
- Reduce `batch_size` before changing model semantics when CUDA memory fails.
- Keep `max_seq_len + max_out_len` within the backend's real context/session length.
- Prefer left padding/truncation for decoder-only generation models unless the model documentation says otherwise.

## Inspection Caveat

A lightweight inspection environment can prove OpenCompass imports, config parsing, and metadata, but it does not prove real model execution. Real HF inference also depends on compatible Transformers/Torch versions, hardware, model weights, optional extras, and enough memory.
