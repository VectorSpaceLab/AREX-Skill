# Inference and Deployment Workflows

This reference gives self-contained recipes for `swift infer`, `swift deploy`, `swift app`, and Python/OpenAI-compatible clients. Replace model ids, ports, adapter names, and resource limits with values that fit the target machine.

## Install and capability check

A minimal install should expose the `swift` console script. Optional accelerated serving backends are separate dependency surfaces and may be absent in a lightweight inspection environment.

```bash
pip install ms-swift -U
swift infer --help
swift deploy --help
swift app --help
```

Install backend extras only when the machine and model support them. Typical examples include vLLM, SGLang, LMDeploy, or evaluation extras such as `pip install ms-swift[eval] -U` when using evaluation integrations.

## Interactive `swift infer`

Use `transformers` first when model support is uncertain because it is the broadest Swift backend.

```bash
CUDA_VISIBLE_DEVICES=0 swift infer \
  --model Qwen/Qwen2.5-7B-Instruct \
  --infer_backend transformers \
  --stream true \
  --max_new_tokens 2048
```

Interactive commands accepted by the CLI include:

- `multi-line`: enter multi-line mode; finish input with `#`.
- `single-line`: return to one-line input.
- `reset-system`: reset system prompt/history.
- `clear`: clear conversation history when the template supports multi-round chat.
- `quit` or `exit`: leave the session.

## LoRA inference

For direct LoRA inference, pass one or more adapter paths with `--adapters`. Swift-trained adapters usually contain an `args.json`; Swift can recover base model/template settings from it.

```bash
CUDA_VISIBLE_DEVICES=0 swift infer \
  --model Qwen/Qwen2.5-7B-Instruct \
  --adapters ./my-lora-checkpoint \
  --infer_backend transformers \
  --stream true \
  --temperature 0 \
  --max_new_tokens 2048
```

Use `--merge_lora true` when you want Swift to merge the adapter into model weights before inference. Prefer merge for accelerated backends when dynamic adapter loading is unsupported or unstable for the target model/backend. Prefer unmerged adapters when using `transformers` or when vLLM dynamic LoRA serving is intentionally configured.

## Dataset and batch inference

Dataset inference starts when `--val_dataset` or `--dataset` is provided. For batch work, avoid streaming and set result output explicitly.

```bash
CUDA_VISIBLE_DEVICES=0 swift infer \
  --model Qwen/Qwen2.5-7B-Instruct \
  --infer_backend transformers \
  --val_dataset AI-ModelScope/alpaca-gpt4-data-zh \
  --stream false \
  --max_batch_size 8 \
  --write_batch_size 1000 \
  --result_path ./infer_results.jsonl \
  --max_new_tokens 512
```

Notes:

- `transformers` supports `--max_batch_size`; accelerated engines batch internally and expose backend-specific parallel flags.
- Swift auto-creates a result path when a validation/evaluation dataset is present and no `--result_path` is supplied.
- `--metric acc` or `--metric rouge` can score dataset inference when labels are present.
- `--stream true` is for interactive/streaming display and can prevent normal saved result/logprob behavior.

## Logprobs and result saving

For persisted log probabilities, use non-streaming inference with a result path.

```bash
swift infer \
  --model Qwen/Qwen2.5-7B-Instruct \
  --infer_backend transformers \
  --val_dataset AI-ModelScope/alpaca-gpt4-data-zh#32 \
  --stream false \
  --logprobs true \
  --top_logprobs 5 \
  --result_path ./logprob_results.jsonl
```

Deployment has a server-side `--max_logprobs` cap. Client requests that ask for `top_logprobs` above that cap fail with a bad request.

## Multimodal CLI inference

Multimodal prompts use tags such as `<image>`, `<video>`, and `<audio>` in text-form requests. The number of tags must match the number of media inputs supplied interactively or in `InferRequest` fields.

```bash
CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
VIDEO_MAX_PIXELS=50176 \
FPS_MAX_FRAMES=12 \
swift infer \
  --model Qwen/Qwen2.5-VL-3B-Instruct \
  --infer_backend transformers \
  --stream true \
  --max_new_tokens 1024
```

Example prompt text:

```text
<image><image>What is different between these two images?
```

Then provide two local image paths or URLs when prompted. For vLLM multimodal models, also consider `--vllm_limit_mm_per_prompt '{"image": 5, "video": 2}'`.

## Accelerated inference CLI

Use accelerated backends only after checking model support and installing the backend.

```bash
CUDA_VISIBLE_DEVICES=0 swift infer \
  --model Qwen/Qwen2.5-7B-Instruct \
  --infer_backend vllm \
  --vllm_gpu_memory_utilization 0.9 \
  --vllm_max_model_len 8192 \
  --vllm_max_num_seqs 64 \
  --max_new_tokens 1024
```

```bash
CUDA_VISIBLE_DEVICES=0,1 swift infer \
  --model Qwen/Qwen3-8B \
  --infer_backend sglang \
  --sglang_tp_size 2 \
  --sglang_context_length 8192 \
  --max_new_tokens 1024
```

```bash
CUDA_VISIBLE_DEVICES=0 swift infer \
  --model OpenGVLab/InternVL2_5-1B \
  --infer_backend lmdeploy \
  --lmdeploy_tp 1 \
  --lmdeploy_vision_batch_size 8 \
  --max_new_tokens 1024
```

## OpenAI-compatible `swift deploy`

Start a local server:

```bash
CUDA_VISIBLE_DEVICES=0 swift deploy \
  --model Qwen/Qwen2.5-7B-Instruct \
  --infer_backend vllm \
  --host 127.0.0.1 \
  --port 8000 \
  --served_model_name Qwen2.5-7B-Instruct \
  --max_new_tokens 2048
```

Query it with curl:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "What should I do if I cannot sleep?"}],
    "max_tokens": 256,
    "temperature": 0
  }'
```

Health and model discovery:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/models
```

If `--api_key` is set on the server, clients must pass `Authorization: Bearer <key>`.

## Multimodal OpenAI-compatible request

OpenAI-style multimodal messages are accepted by the deployment endpoint.

```json
{
  "model": "Qwen2.5-VL-3B-Instruct",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "./cat.png"},
        {"type": "image", "image": "./animal.png"},
        {"type": "text", "text": "What differs between these images?"}
      ]
    }
  ],
  "max_tokens": 256,
  "temperature": 0
}
```

Some clients use `image_url` with `{ "url": "..." }`; Swift normalizes common OpenAI-compatible multimodal shapes into `InferRequest` objects.

## Python OpenAI client

```python
from openai import OpenAI

client = OpenAI(api_key="EMPTY", base_url="http://127.0.0.1:8000/v1")
model = client.models.list().data[0].id
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Who are you?"}],
    max_tokens=128,
    temperature=0,
)
print(response.choices[0].message.content)
```

For streaming:

```python
stream = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Count to five."}],
    stream=True,
    temperature=0,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

## Swift Python client

```python
from swift.infer_engine import InferClient, InferRequest, RequestConfig

engine = InferClient(host="127.0.0.1", port=8000, api_key="EMPTY")
model = engine.models[0]
request = InferRequest(messages=[{"role": "user", "content": "Who are you?"}])
config = RequestConfig(max_tokens=128, temperature=0)
response = engine.infer([request], config, model=model)[0]
print(response.choices[0].message.content)
```

## Direct Python engines

Direct Python engines are useful for custom applications that do not need an HTTP server.

```python
from swift.infer_engine import InferRequest, RequestConfig, TransformersEngine

engine = TransformersEngine("Qwen/Qwen2.5-0.5B-Instruct", max_batch_size=2)
config = RequestConfig(max_tokens=128, temperature=0)
requests = [
    InferRequest(messages=[{"role": "user", "content": "Who are you?"}]),
    InferRequest(messages=[{"role": "user", "content": "Where is Hangzhou?"}]),
]
responses = engine.infer(requests, config)
for response in responses:
    print(response.choices[0].message.content)
```

Engine class selection:

```python
from swift.infer_engine import LmdeployEngine, SglangEngine, TransformersEngine, VllmEngine

engine = TransformersEngine("model-id", max_batch_size=4)
# engine = VllmEngine("model-id", max_model_len=8192, limit_mm_per_prompt={"image": 5})
# engine = SglangEngine("model-id", tp_size=2, context_length=8192)
# engine = LmdeployEngine("model-id", tp=1, vision_batch_size=8)
```

## Multiple LoRA serving

`swift deploy` supports named adapter mappings. Model discovery returns the base served model plus adapter names.

```bash
CUDA_VISIBLE_DEVICES=0 swift deploy \
  --host 127.0.0.1 \
  --port 8000 \
  --infer_backend vllm \
  --model Qwen/Qwen2.5-7B-Instruct \
  --adapters lora1=./adapter-a lora2=./adapter-b \
  --served_model_name base-model
```

Client-side choose `model="lora1"`, `model="lora2"`, or `model="base-model"`. Dynamic vLLM LoRA serving requires vLLM support for LoRA and compatible adapter rank; Swift passes `enable_lora`, `max_loras`, and `max_lora_rank` based on adapters and `--vllm_max_lora_rank`.

## `swift app` inference UI

Launch a local app that self-deploys a model:

```bash
CUDA_VISIBLE_DEVICES=0 swift app \
  --model Qwen/Qwen2.5-7B-Instruct \
  --infer_backend vllm \
  --stream true \
  --max_new_tokens 2048 \
  --studio_title My-Swift-App \
  --lang en
```

Launch a UI against an already deployed OpenAI-compatible service:

```bash
swift app \
  --model Qwen2.5-7B-Instruct \
  --base_url http://127.0.0.1:8000/v1 \
  --stream true \
  --max_new_tokens 2048 \
  --lang en
```

For multimodal app deployments, set media limits and pass `--is_multimodal true` if auto-detection cannot infer it.

```bash
CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
VIDEO_MAX_PIXELS=50176 \
FPS_MAX_FRAMES=12 \
swift app \
  --model Qwen/Qwen2.5-VL-3B-Instruct \
  --infer_backend vllm \
  --vllm_max_model_len 8192 \
  --vllm_limit_mm_per_prompt '{"image": 5, "video": 2}' \
  --is_multimodal true \
  --stream true \
  --lang en
```

## LoRA-to-serving decision recipe

When converting a trained LoRA checkpoint into serving:

1. Inspect whether the adapter contains Swift metadata such as `args.json`; if it does, Swift can often infer base model and template settings from `--adapters`.
2. Choose `transformers` for highest compatibility, QLoRA, or debugging.
3. Choose `vllm` for throughput only if the base model and adapter rank are supported and dynamic LoRA is acceptable.
4. Use `--merge_lora true` or an export/merge workflow when using SGLang/LMDeploy, when QLoRA is involved, or when a backend rejects dynamic adapters.
5. For multi-adapter serving, keep adapters unmerged and name them with `name=path` under vLLM; verify `/v1/models` returns all expected names.
6. Smoke-test the base model and each adapter model name with a deterministic low-token chat request.
