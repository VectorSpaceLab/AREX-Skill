# Installation and Environment Guidance

Petals local package health, remote swarm health, model access, and accelerator readiness are separate checks.

## Install and import

Use an isolated Python environment. The source snapshot for this skill declares Python `>=3.8` and pins `transformers==4.43.1` in package metadata.

```bash
python -m pip install petals
python - <<'PY'
import sys
import petals
from petals import AutoDistributedModelForCausalLM, RemoteSequential
print("petals", petals.__version__)
print("bitsandbytes eager import", "bitsandbytes" in sys.modules)
PY
```

A healthy base import should not import `bitsandbytes` unless a quantization or adapter path asks for it.

## Dependency surfaces

Base package dependencies include PyTorch, Transformers, Hivemind, Hugging Face Hub, Tokenizers, Accelerate, Tensor Parallel, SentencePiece, PEFT, Safetensors, Speedtest CLI, and support libraries. Development tests require extra pytest packages and a live private swarm for many distributed cases. Do not install broad dev or notebook dependencies unless the user is maintaining the package, running native tests, or executing prompt-tuning notebooks.

## Backend expectations

| Workflow | Local backend needed | Extra external requirement |
| --- | --- | --- |
| Import/API/CLI parser checks | CPU is enough | none |
| Client generation against public swarm | CPU client can work | public DHT peers, hosted blocks, model/tokenizer access, network |
| Private CPU smoke swarm | CPU is enough for tiny wiring checks | background DHT/server processes and model downloads/cache |
| Production server hosting | usually GPU or other accelerator | port/reachability, disk cache, model weights, stable network |
| Quantized server blocks (`int8`, `nf4`) | compatible bitsandbytes + backend stack | matching torch/CUDA/ROCm/MPS support |
| PEFT adapter preloading | PEFT + safetensors + usually bitsandbytes path | adapter repository access and server-side verification |
| Prompt tuning | client CPU can hold prompts; GPU often used for speed/AMP | remote servers, datasets, model access, optional W&B |

A CPU import is not evidence for production GPU serving or quantized adapter execution. A GPU host is not required for client-only code that connects to remote servers.

## Hugging Face access and caches

Petals may need accepted model terms for gated Llama-family models, an existing login session or token, enough cache disk space, and model identifiers whose architecture is supported by Petals. Do not put tokens into generated code, logs, or reusable skill files.

For servers, set cache and disk cap when disk is limited:

```bash
python -m petals.cli.run_server MODEL_ID --cache_dir PETALS_CACHE_DIR --max_disk_space 50GB
```

## Optional bitsandbytes and CUDA caution

Some modern PyTorch/CUDA resolver combinations can import Torch and allocate CUDA tensors successfully while pinned `bitsandbytes` fails because it lacks a matching binary or expects older Triton APIs. When this happens, avoid quantization with `--quant_type none` until the stack is repaired, match Torch/CUDA/Triton/bitsandbytes intentionally, and do not mark adapter or quantized server workflows as verified from a base import alone.

## What safe checks prove

Passing import and parser checks proves local package metadata, imports, public symbols, and CLI parser modules are usable. It does not prove public swarm reachability, model hosting, large downloads, firewall/DHT operation, quantization, adapters, notebook training, or production throughput.
