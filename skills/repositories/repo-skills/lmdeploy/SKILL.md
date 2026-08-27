---
name: lmdeploy
description: "Use LMDeploy to run offline LLM/VLM inference, serve
  OpenAI-compatible APIs, quantize models, tune PyTorch/TurboMind backends, and
  extend model support."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LMDeploy Repo Skill

Use this skill when a task mentions LMDeploy, `lmdeploy.pipeline`, `lmdeploy serve`, `lmdeploy lite`, TurboMind, PyTorchEngine, VLM media prompts, OpenAI-compatible model serving, or adding support for a new LMDeploy model/backend.

## Before You Start

- Read `references/repo-provenance.md` when checking whether this skill matches a current LMDeploy checkout.
- Read `references/model-and-backend-overview.md` when choosing between TurboMind, PyTorch, serving, VLM, quantization, or model-extension routes.
- Read `references/troubleshooting.md` for install/import, CUDA/TurboMind, optional dependency, and runtime triage shared across workflows.
- Run `python scripts/check_lmdeploy_environment.py --include-cli` for a no-model diagnostic of imports, package version, CLI help, torch/CUDA visibility, and optional dependency gaps.

## Minimal Install and Import Check

For normal use, prefer a packaged install in an isolated Python environment:

```bash
pip install lmdeploy
python - <<'PY'
import lmdeploy
from lmdeploy import GenerationConfig, PytorchEngineConfig, TurbomindEngineConfig, pipeline
print(lmdeploy.__version__)
print(GenerationConfig(max_new_tokens=1))
print(PytorchEngineConfig.__name__, TurbomindEngineConfig.__name__, pipeline)
PY
```

For source checkouts, `DISABLE_TURBOMIND=1 pip install -e .` avoids compiling the TurboMind extension when the task only needs Python API inspection or PyTorch backend work. Full TurboMind source builds need CUDA/toolchain compatibility; see `backend-extension` and root troubleshooting before rebuilding.

## Route Map

| User task | Read |
| --- | --- |
| Use `lmdeploy.pipeline`, `Pipeline.infer`, streaming, chat sessions, `GenerationConfig`, chat templates, LoRA adapters, `lmdeploy chat` | `sub-skills/pipeline-inference/SKILL.md` |
| Launch `lmdeploy serve api_server`, proxy multiple servers, call OpenAI/Responses/Anthropic endpoints, configure Codex or Claude Code clients | `sub-skills/serving-apis/SKILL.md` |
| Build VLM prompts with images/video/audio/time-series, `load_image`, OpenAI multimodal content blocks, `VisionConfig`, media URL/base64 checks | `sub-skills/vision-language/SKILL.md` |
| Plan AWQ/GPTQ/SmoothQuant/KV quantization, `lmdeploy lite` commands, Qwen3 recipes, quantized artifact handoff | `sub-skills/quantization/SKILL.md` |
| Tune PyTorch/TurboMind backend config, debug `_turbomind`/NCCL/CUDA issues, inspect module maps, add new PyTorch model support | `sub-skills/backend-extension/SKILL.md` |

## Common Decisions

- **Backend**: use TurboMind for optimized deployment when compatible wheels/extensions and GPU support are available; use PyTorch backend for Python-first development, new-model work, or features documented as PyTorch-only.
- **Memory**: reduce `cache_max_entry_count`, `session_len`, batch size, or tensor parallel assumptions before treating OOM as a model bug.
- **Serving**: set `--model-name` explicitly when downstream clients need a stable ID; use `--api-keys` and matching `Authorization: Bearer ...` headers when authentication is enabled.
- **VLM**: keep media payload construction in `vision-language`; server/client transport still belongs to `serving-apis`.
- **Quantized models**: create artifacts in `quantization`, then route offline loading to `pipeline-inference` or service loading to `serving-apis`.
- **Repo edits**: follow the current checkout’s contributor/test guidance, then run focused tests before broad suites.

## Safe Validation Ladder

1. `python scripts/check_lmdeploy_environment.py --include-cli` for package and CLI sanity.
2. The owning sub-skill helper, such as `python sub-skills/quantization/scripts/plan_quantization_command.py --help`.
3. CLI `--help` for the exact workflow (`lmdeploy chat --help`, `lmdeploy serve api_server --help`, or `lmdeploy lite auto_awq --help`).
4. A no-download API/config/media check from the owning sub-skill.
5. Native tests or real model execution only when the user has the model weights, hardware, optional dependencies, network/credentials, and time budget.

## Do Not

- Do not tell future agents to run original repository scripts or docs as runtime dependencies; use this skill’s bundled references/scripts instead.
- Do not start model downloads, long quantization, GPU benchmarks, server daemons, or native test suites unless the user has approved the resources and prerequisites.
- Do not expose local environment prefixes, Python executable paths, API keys, tokens, or machine-specific cache paths in public guidance.
