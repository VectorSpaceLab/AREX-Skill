# Model and Backend Matrix

## Model family choices

| Need | Prefer | Notes |
| --- | --- | --- |
| Multi-turn assistant behavior | `Qwen-*-Chat` | Provides Qwen-specific `chat`/`chat_stream` behavior and alignment. |
| Text continuation or scoring-like generation | `Qwen-*` base model | Use `generate`; do not expect chat alignment. |
| Lower VRAM inference | `*-Int4` or `*-Int8` checkpoint | Requires compatible AutoGPTQ/Transformers/PyTorch/CUDA stack. |
| Hosted API without local weights | DashScope models such as `qwen-turbo`/`qwen-plus` | Requires account, network, and API key. |
| ModelScope download path | `qwen/Qwen-*` | Use ModelScope snapshot only when network/storage is approved. |

## Backend decisions

| Backend | Best for | Required checks | Common pitfalls |
| --- | --- | --- | --- |
| CPU | Compatibility checks, very small/debug generation | `device_map="cpu"`; enough RAM | Very slow; some half-precision paths fail on CPU. |
| Single CUDA GPU | Normal local generation for smaller Qwen checkpoints | torch CUDA visible; enough VRAM; precision supported | OOM, FlashAttention mismatch, checkpoint shards missing. |
| Multiple CUDA GPUs | Larger checkpoints or high-memory contexts | `device_map="auto"` or serving tensor parallelism | Native Transformers pipeline parallelism can be inefficient. |
| vLLM | Serving throughput and tensor parallel deployment | Compatible vLLM wheel, CUDA, checkpoint support | dtype/compute-capability mismatch; service topology errors. |
| Docker | Reproducible demo/API/fine-tune environment | Docker daemon, NVIDIA container toolkit, checkpoint mount | Image pulls, missing `config.json`, host-driver mismatch. |
| DashScope | Cloud inference without local model ops | API key, service access | Credentials, rate limits, service/model difference. |
| Ascend/DCU | Vendor accelerator deployments | Vendor device, driver, image/toolkit | No portable CPU substitute. |

## Precision and quantization

- BF16 is the repository's preferred mixed precision when supported by hardware.
- FP16 is useful for older GPUs and Q-LoRA/Int4 deployment paths.
- Int4/Int8 checkpoints improve memory footprint but shift compatibility risk to AutoGPTQ, CUDA, PyTorch, Transformers, Optimum, and PEFT versions.
- Quantized KV cache can reduce memory for larger batch or generation lengths, but it conflicts with FlashAttention in the documented Qwen path.
- Missing `*.cpp` or `*.cu` files after saving a quantized or fine-tuned checkpoint can break KV-cache kernels; copy the necessary checkpoint-side support files when the workflow needs that feature.

## Long-context planning

Historical Qwen long-context behavior depends on model-specific config options and model size. Verify the loaded config rather than assuming a prompt window. For long input tasks:

1. Inspect max window and generation config from the checkpoint.
2. Confirm whether dynamic NTK, LogN attention, or window attention is enabled by that checkpoint/config.
3. Budget memory for prompt length plus generated tokens, not just context length.
4. Prefer vLLM or a carefully tested backend for production long-context serving.

## What not to claim from a smoke check

A successful import of `torch`, `transformers`, or `tiktoken` proves only that dependencies import. A tiny CUDA tensor proves only that torch sees CUDA. Neither proves Qwen checkpoint loading, remote-code compatibility, generation quality, vLLM serving, training, quantization, benchmark reproduction, or Docker runtime.
