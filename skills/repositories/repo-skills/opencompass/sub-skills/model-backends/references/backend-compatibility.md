# Backend Compatibility

OpenCompass supports default Transformers inference, direct accelerated wrappers, and service/API wrappers. Choose the smallest backend change that matches the task: config-only acceleration for existing HF models, direct accelerated model configs for tuned local runs, or API/service wrappers when inference is hosted elsewhere.

## Backend Selection Matrix

| Need | Backend route | Main config or CLI fields | Optional dependency boundary |
| --- | --- | --- | --- |
| Generic local HF model | `HuggingFace`, `HuggingFaceCausalLM`, `HuggingFacewithChatTemplate` | `path`, `tokenizer_kwargs`, `model_kwargs`, `batch_size`, `run_cfg` | Transformers + compatible Torch |
| One-click acceleration of HF config | CLI `--accelerator vllm` or `--accelerator lmdeploy` | keep HF config, launch with accelerator | install vLLM or LMDeploy separately |
| Direct vLLM config | `VLLM` or `VLLMwithChatTemplate` | `path`, `model_kwargs`, `generation_kwargs`, `max_seq_len`, `batch_size` | vLLM and its Torch/CUDA constraints |
| Direct LMDeploy config | `TurboMindModel` or chat-template variant | `path`, `backend`, `engine_config`, `gen_config`, `max_seq_len`, `batch_size` | LMDeploy and CUDA/backend constraints |
| Hosted OpenAI-compatible service | `OpenAISDK` | `openai_api_base`, `path`, `key`, `tokenizer_path`, `query_per_second`, `retry` | `openai` package, service reachable |
| LMDeploy API server | `TurboMindAPIModel` or `OpenAISDK` against `/v1` | `api_addr` or `openai_api_base`, `path`, `batch_size`, `run_cfg` | LMDeploy server already running |
| LightLLM service | `LightllmAPI` | service URL/ports and API model config | LightLLM server already running |

## CLI Accelerator Flag

OpenCompass CLI exposes `--accelerator {vllm,lmdeploy,None}`. This is useful when an existing HuggingFace config should be tried with an accelerated backend without rewriting the model config.

```bash
opencompass path/to/eval_config.py --accelerator vllm
opencompass path/to/eval_config.py --accelerator lmdeploy
```

Use this route only when:

- The original model config is HF-like and compatible with automatic conversion.
- The selected accelerator is installed in the execution environment.
- Hardware, CUDA, Torch, and model architecture are supported by that accelerator.

Do not treat `--accelerator` as proof that every HF parameter maps perfectly. If conversion fails, create an explicit backend config.

## Direct vLLM Config

```python
from opencompass.models import VLLM

models = [
    dict(
        type=VLLM,
        abbr='qwen-vllm',
        path='Qwen/Qwen1.5-7B-Chat',
        model_kwargs=dict(
            trust_remote_code=True,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
        ),
        generation_kwargs=dict(temperature=0, do_sample=False),
        max_seq_len=4096,
        max_out_len=512,
        batch_size=32,
        run_cfg=dict(num_gpus=1),
    )
]
```

Notes:

- `VLLM` defaults include `trust_remote_code=True` in OpenCompass, but make it explicit when sharing configs.
- `generation_kwargs` are merged into vLLM sampling parameters; OpenCompass removes `do_sample` in the classic `VLLM` wrapper, so use deterministic sampling settings that the wrapper/backend accepts.
- `lora_path` is supported by the vLLM wrapper path, but requires a vLLM installation with LoRA support.
- vLLM dependency constraints can be strict; resolve Torch/CUDA/vLLM compatibility before blaming OpenCompass config syntax.

## Direct LMDeploy Config

```python
from opencompass.models import TurboMindModelwithChatTemplate

models = [
    dict(
        type=TurboMindModelwithChatTemplate,
        abbr='internlm2-chat-lmdeploy',
        path='internlm/internlm2-chat-7b',
        backend='turbomind',
        engine_config=dict(tp=1, session_len=7168),
        gen_config=dict(do_sample=False),
        max_seq_len=7168,
        max_out_len=1024,
        batch_size=5000,
        run_cfg=dict(num_gpus=1),
    )
]
```

Notes:

- `backend` may be `turbomind` or `pytorch`; LMDeploy can fall back depending on model support.
- `engine_config` is filtered against LMDeploy engine config classes, so misspelled keys may be ignored or fail later depending on version.
- `gen_config` is filtered against LMDeploy `GenerationConfig` fields.
- Keep `session_len`, `max_seq_len`, and expected prompt/output lengths aligned.

## Service-Based Acceleration

Hosted services decouple OpenCompass runners from local model loading. They are best when the model server is managed separately or multiple evaluations share the same service.

OpenAI-compatible LMDeploy/vLLM service via `OpenAISDK`:

```python
from opencompass.models import OpenAISDK

api_meta_template = dict(
    round=[
        dict(role='HUMAN', api_role='HUMAN'),
        dict(role='BOT', api_role='BOT', generate=True),
    ],
    reserved_roles=[dict(role='SYSTEM', api_role='SYSTEM')],
)

models = [
    dict(
        type=OpenAISDK,
        abbr='llama3-lmdeploy-api',
        key='EMPTY',
        openai_api_base='http://127.0.0.1:23333/v1',
        path='Meta-Llama-3-8B-Instruct',
        tokenizer_path='meta-llama/Meta-Llama-3.1-8B-Instruct',
        meta_template=api_meta_template,
        query_per_second=1,
        retry=3,
        rpm_verbose=True,
        max_seq_len=4096,
        max_out_len=1024,
        temperature=0.01,
        batch_size=8,
        run_cfg=dict(num_gpus=0),
    )
]
```

LMDeploy native API wrapper:

```python
from opencompass.models.turbomind_api import TurboMindAPIModel

models = [
    dict(
        type=TurboMindAPIModel,
        abbr='internlm-turbomind-api',
        api_addr='http://127.0.0.1:23333',
        max_seq_len=2048,
        max_out_len=100,
        batch_size=8,
        run_cfg=dict(num_gpus=0, num_procs=1),
    )
]
```

For remote services, `run_cfg.num_gpus` describes OpenCompass worker resource needs, not the server's GPU allocation. Use `0` unless the evaluation process itself needs local GPUs.

## Optional Extras and Installation

The OpenCompass base package can import without optional accelerator/API extras. Backend execution may require additional packages:

- API wrappers commonly need provider SDKs such as `openai`, `anthropic`, or provider-specific clients.
- vLLM configs need `vllm` and its compatible Torch/CUDA stack.
- LMDeploy configs need `lmdeploy` and compatible CUDA/backend packages.
- LightLLM service usage requires a separately installed/running LightLLM server and compatible Transformers stack.

Keep skill guidance credential-safe: mention required environment variables and placeholders, but do not embed real keys.
