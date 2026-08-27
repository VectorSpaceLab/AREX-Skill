---
name: funclip
description: "Guide FunClip ASR video/audio clipping, LLM-assisted clipping
  providers, and release packaging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FunClip repo skill

Use this skill when the task names FunClip or asks for ASR-driven video/audio
clipping, transcript timestamp clipping, speaker clipping, subtitle generation,
LLM-assisted highlight selection, or FunClip release packaging.

FunClip is a checkout-oriented Python application. Prefer the documented script
entry points (`python funclip/launch.py` and `python funclip/videoclipper.py`)
instead of assuming a packaged console entry point exists.

## Start here

1. Read [references/installation-and-runtime.md](references/installation-and-runtime.md)
   before installing, launching, or debugging optional media/model/provider
   dependencies.
2. Run [scripts/check_environment.py](scripts/check_environment.py) with
   `--repo-root <funclip-checkout>` when you need a no-network import,
   requirement, model-selection, and launch-policy smoke check.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for
   cross-cutting install/import, model-download, optional-provider, media-binary,
   and repo-maintenance routing failures.
4. Read [references/repo-provenance.md](references/repo-provenance.md) before
   deciding whether this skill is stale for a checkout.

## Sub-skill routes

| User task | Go to | Why |
| --- | --- | --- |
| Launch the Gradio app, choose Paraformer/Fun-ASR-Nano/SenseVoice, bind a remote server, run CLI stage 1/2, clip by transcript text or speaker, generate SRT/subtitle overlays, or debug no-match behavior | [clip-workflows](sub-skills/clip-workflows/SKILL.md) | Owns the ASR, media, subtitle, CLI, and `VideoClipper` workflows. |
| Configure GPT/Qwen/DeepSeek/AtlasCloud/MiniMax/LiteLLM/g4f/TwelveLabs Pegasus, fix API-key/base-url/model-prefix errors, or make LLM output parseable by AI Clip | [llm-providers](sub-skills/llm-providers/SKILL.md) | Owns provider routing, prompt format, timestamp normalization, and no-live-call route smoke tests. |
| Build FunClip release archives, regenerate `SHA256SUMS`, align `VERSION`/README/release notes, inspect release workflow failures, or validate issue/PR templates | [release-packaging](sub-skills/release-packaging/SKILL.md) | Owns versioned source archives, checksums, GitHub release contracts, and maintainer validation. |

## Minimal install and smoke check

From a FunClip checkout, install the declared runtime dependencies:

```bash
python -m pip install -r requirements.txt
```

For a no-network local smoke check after installation, run the bundled helper
from the generated skill tree:

```bash
python scripts/check_environment.py --repo-root <funclip-checkout> --check-binaries
```

That helper verifies the requirements markers, imports core modules with the
checkout's `funclip/` directory on `sys.path`, checks launch kwargs, and uses a
fake AutoModel to verify model selection without downloading weights.

## Important boundaries

- Model weights are not bundled with FunClip. First real recognition may need
  network access or a pre-populated model cache.
- Live provider calls need provider-specific API keys and are not checked by the
  deterministic smoke scripts.
- Full video clipping and subtitle burn-in can require ffmpeg, ImageMagick, and
  a usable font.
- `--listen` binds all interfaces but does not create a public Gradio link;
  add `--share` only when that is intended.
- For programmatic use from a checkout, add the checkout's `funclip/` directory
  to `sys.path` before importing `launch`, `videoclipper`, or `llm.*` helpers,
  because the source files use top-level imports.

## Verification anchors

Useful native candidates for a current checkout include:

- `tests/test_model_selection.py`, `tests/test_duplicate_text_matching.py`,
  `tests/test_recognition_result_compat.py`, `tests/test_gradio_runtime_compat.py`,
  and `tests/test_funasr_requirement.py` for ASR/clip workflows.
- `tests/test_openai_api.py`, `tests/test_minimax_api.py`,
  `tests/test_litellm_api.py`, `tests/test_twelvelabs_pegasus.py`, and
  `tests/test_minimax_launch_integration.py` for LLM provider routing.
- `tests/test_release_contract.py` and `tests/test_github_templates.py` for
  release packaging and maintainer templates.

Run native tests only after choosing the relevant workflow and preparing the
matching optional dependencies. The bundled smoke scripts are safer first checks
because they avoid model downloads, credentials, and long media processing.
