---
name: pipeline-inference
description: "Use LMDeploy pipeline APIs and chat CLI for offline text LLM
  inference, streaming, sessions, generation settings, backend configs, and chat
  templates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipeline Inference

Use this sub-skill when the task is offline text LLM inference through `lmdeploy.pipeline`, `Pipeline`, or `lmdeploy chat`.

## Read First

- `references/api-reference.md` for exact constructors, methods, response fields, and config defaults.
- `references/workflows.md` for copy-ready offline inference patterns, batch prompts, streaming, sessions, LoRA, logits, hidden states, and PPL.
- `references/chat-templates.md` for JSON chat templates, Python registration, prompt-format mismatch diagnosis, and safe inspection.
- `references/troubleshooting.md` for OOM, multiprocessing, missing TurboMind extension, stop-token, model download, and trust boundary failures.
- `scripts/inspect_pipeline_config.py` for no-download inspection of installed API signatures, dataclass defaults, chat-template registry names, and CLI availability.

## Scope

Own these tasks:

- Create an offline text pipeline with `from lmdeploy import pipeline` and `TurbomindEngineConfig` or `PytorchEngineConfig`.
- Run single prompts, batches, OpenAI-style messages, streaming output, and multi-turn chat sessions.
- Tune `GenerationConfig`, `cache_max_entry_count`, `tp`, `session_len`, `max_batch_size`, LoRA adapters, and chat templates for inference.
- Inspect logits, last hidden states, token lengths, finish reasons, and PPL without designing a server.
- Use `lmdeploy chat` for local interactive text inference and CLI smoke checks.

Route elsewhere:

- Multimodal media loading, image/video prompt construction, and VLM-specific formatting: `vision-language`.
- REST/gRPC/OpenAI-compatible servers, proxy, API clients, and API-server auth: `serving-apis`.
- Creating AWQ/GPTQ/SmoothQuant artifacts with `lmdeploy lite`: `quantization`.
- New architecture patches, backend internals, custom kernels, or model support development: `backend-extension`.

## Fast Start

```python
from lmdeploy import GenerationConfig, TurbomindEngineConfig, pipeline

backend_config = TurbomindEngineConfig(cache_max_entry_count=0.6, tp=1)
gen_config = GenerationConfig(max_new_tokens=128, top_p=0.9, temperature=0.7)

with pipeline("org/model-or-local-path", backend_config=backend_config) as pipe:
    responses = pipe(["Explain LMDeploy in one sentence.", "List two use cases."], gen_config=gen_config)
    for response in responses:
        print(response.text)
```

For PyTorch backend, use `PytorchEngineConfig(...)`. When `tp > 1` with PyTorch in a script, wrap pipeline creation in `if __name__ == "__main__":`.

## Validation

Use these checks before recommending or shipping an offline pipeline workflow:

```bash
python sub-skills/pipeline-inference/scripts/inspect_pipeline_config.py --include-cli
lmdeploy chat --help
```

These checks do not download a model. Model execution requires the user’s chosen model weights, backend dependencies, GPU/accelerator memory, and any required `trust_remote_code` decision.
