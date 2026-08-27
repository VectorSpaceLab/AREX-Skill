---
name: outlines
description: "Operate the Outlines structured-output library across output
  types, local models, provider integrations, and prompt workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Outlines Repo Skill

Use this repo skill when a task involves Outlines as a Python package for structured outputs from large language models: defining schemas or regex/CFG constraints, wrapping local or hosted models, rendering prompt templates, composing chat/multimodal inputs, and troubleshooting package/provider/runtime behavior.

This skill is self-contained. Do not reopen the source checkout to use it. The source repository was used only as evidence for these bundled routes, references, and scripts.

## Install and Import Check

Base install:

```bash
pip install outlines
```

Optional integrations are installed separately; choose only the backend/provider you need. Examples:

```bash
pip install transformers torch       # local Transformers path
pip install llama-cpp-python         # llama.cpp path
pip install vllm                     # vLLM offline/server client path as appropriate
pip install openai                   # OpenAI, SGLang, vLLM server SDK clients
pip install huggingface_hub          # TGI client
```

Minimal import check:

```python
import outlines
from outlines import Generator, Template
from outlines.inputs import Chat, Image
from outlines.types import JsonSchema, Regex, CFG, Choice
```

Important: in this source revision, `Chat` is imported from `outlines.inputs`, not from the top-level `outlines` namespace.

## Route by Task

| Task signal | Read |
|---|---|
| JSON/Pydantic/dataclass/TypedDict/GenSON output, `Literal`/`Enum`/`Choice`, regex, CFG, `Generator`, backend selection, custom logits processor, parsing generated JSON | [`sub-skills/structured-generation/SKILL.md`](sub-skills/structured-generation/SKILL.md) |
| Local/offline model setup with Transformers, Transformers multimodal, llama.cpp, MLX-LM, vLLM offline, tokenizers, device dtype, CUDA/MPS/VRAM, local batch/stream behavior | [`sub-skills/local-models/SKILL.md`](sub-skills/local-models/SKILL.md) |
| Hosted or server-based providers: OpenAI/Azure, Anthropic, Gemini, Mistral, Ollama, LM Studio, SGLang, TGI, vLLM server, Dottxt; credentials/endpoints; provider exceptions | [`sub-skills/remote-providers/SKILL.md`](sub-skills/remote-providers/SKILL.md) |
| Prompt templates, `Application`, `Chat`, `Image`/`Audio`/`Video`, Jinja filters, cache controls, safe self-consistency/task-loop recipes | [`sub-skills/prompt-workflows/SKILL.md`](sub-skills/prompt-workflows/SKILL.md) |

## Repo-Level References

- [`references/api-overview.md`](references/api-overview.md): package map, public imports, model categories, and high-level call contracts.
- [`references/compatibility.md`](references/compatibility.md): optional dependencies, backend/provider/hardware boundaries, and what is or is not verified by CPU inspection.
- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting install/import, optional dependency, provider, schema, cache, and safety failures.
- [`references/repo-provenance.md`](references/repo-provenance.md): source version and evidence baseline.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json): structured router metadata for managed imports.

## Safe Helper Scripts

- [`scripts/inspect_outlines_api.py`](scripts/inspect_outlines_api.py): read-only import/signature smoke for a local Python environment.
- `sub-skills/structured-generation/scripts/validate_structure.py`: local JSON Schema or regex validator.
- `sub-skills/local-models/scripts/check_local_model_prereqs.py`: no-network optional module/device probe.
- `sub-skills/remote-providers/scripts/check_provider_prereqs.py`: no-network provider SDK/env-var probe with secrets redacted.
- `sub-skills/prompt-workflows/scripts/render_template.py`: local `Template` renderer.

## Operating Rules

1. Keep output-type design separate from model/provider selection. First define the structure, then pick a compatible execution route.
2. Treat Outlines generation outputs as raw strings unless a provider wrapper explicitly returns something else; parse or validate after generation.
3. Do not install broad extras or GPU stacks unless the task explicitly needs that runtime.
4. Do not call provider services, download models, or start long-running servers during planning or static troubleshooting.
5. Never execute model-generated code (`eval`, `exec`, shell) while using this skill. Validate with schemas, regex, parsers, and bounded tests.
6. For remote errors, catch `outlines.exceptions.APIError` subclasses and use `retryable`, `provider`, `status_code`, `request_id`, and `hint` to decide recovery.
7. For local hardware, verify the actual framework/backend runtime before claiming CUDA, MPS, vLLM, or llama.cpp acceleration works.
