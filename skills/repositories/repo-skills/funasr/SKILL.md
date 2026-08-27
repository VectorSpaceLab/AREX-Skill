---
name: funasr
description: "Router for FunASR speech workflows: local transcription,
  subtitles, services, vLLM, normalization, and training/export."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# FunASR

Use this root skill to route FunASR requests. Start here when the user asks for speech transcription, subtitles, model choice, service deployment, LLM-ASR routing, punctuation cleanup, manifests, or training/export guidance.

## Start here

- Package provenance and staleness check: [references/repo-provenance.md](references/repo-provenance.md)
- Router metadata for repo-skills-router: [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
- Package commands and entry points: [references/cli-reference.md](references/cli-reference.md)
- Public API shapes and input/output forms: [references/api-reference.md](references/api-reference.md)
- Model-family choice guide: [references/model-overview.md](references/model-overview.md)
- Cross-skill workflow map: [references/workflows.md](references/workflows.md)
- Shared input/output schemas: [references/data-formats.md](references/data-formats.md)
- Cross-cutting failure recovery: [references/troubleshooting.md](references/troubleshooting.md)
- Safe environment smoke helper: [scripts/check_funasr_env.py](scripts/check_funasr_env.py)

## Route map

| Need | Go to |
|---|---|
| Plain transcription, batch ASR, subtitles, audio decoding, hotwords, timestamps, or common non-LLM model choice | [sub-skills/python-asr-pipelines/SKILL.md](sub-skills/python-asr-pipelines/SKILL.md) |
| Punctuation cleanup, inverse text normalization, or text normalization | [sub-skills/text-normalization/SKILL.md](sub-skills/text-normalization/SKILL.md) |
| OpenAI-compatible HTTP API, realtime WebSocket, MCP, browser/client integration, or edge/runtime guidance | [sub-skills/serving-and-runtime/SKILL.md](sub-skills/serving-and-runtime/SKILL.md) |
| Fun-ASR-Nano, Fun-ASR-MLT-Nano, GLM-ASR-Nano, Qwen3-ASR, or `AutoModelVLLM` | [sub-skills/llm-asr-and-vllm/SKILL.md](sub-skills/llm-asr-and-vllm/SKILL.md) |
| Training data prep, manifests, distributed config, export, or local inference after export | [sub-skills/training-data-and-export/SKILL.md](sub-skills/training-data-and-export/SKILL.md) |

## What this root skill owns

- The first decision about which FunASR workflow to use.
- Quick package inspection and safe help/version checks.
- The common vocabulary for ASR, VAD, punctuation, speaker labels, hotwords, subtitles, service deployment, and manifests.
- Cross-cutting troubleshooting that applies before a user narrows to a sub-skill.

## How to start safely

1. Run `python scripts/check_funasr_env.py --check-cli --check-torch` to confirm the package and entry points are visible in the current environment.
2. Use `import funasr` as the minimal package import check.
3. Remember that `import funasr` may work before PyTorch is installed, but `from funasr import AutoModel` needs a compatible `torch` build.
4. If the request names a model family, use [references/model-overview.md](references/model-overview.md) before choosing a route.

## Where to read next

- Transcription and subtitles: `python-asr-pipelines`
- Optional punctuation cleanup or ITN/TN: `text-normalization`
- HTTP/WebSocket/MCP/runtime deployment: `serving-and-runtime`
- Nano/GLM/Qwen3/vLLM backend choice: `llm-asr-and-vllm`
- Training and export: `training-data-and-export`

## Do not do here

- Do not bury service, model-family, normalization, or training guidance inside this router.
- Do not tell users to open the original source checkout from runtime instructions.
- Do not claim GPU, vLLM, or Pynini support from the root skill alone; route to the owning sub-skill and its references.

## Quick model instincts

- CPU-friendly first try: `SenseVoiceSmall`
- Mandarin production and subtitles: `paraformer-zh`
- GPU-heavy LLM-ASR / batch throughput: `Fun-ASR-Nano` or `GLM-ASR-Nano` through `llm-asr-and-vllm`
- Server or client integration: `serving-and-runtime`

## Cross-cutting checks

- Use [references/troubleshooting.md](references/troubleshooting.md) for install/import, hub, device, and download issues.
- Use the sub-skill troubleshooting pages for workflow-specific failures.
- Keep review-only outputs in `skills/tests/funasr/`, not inside the runtime skill tree.
