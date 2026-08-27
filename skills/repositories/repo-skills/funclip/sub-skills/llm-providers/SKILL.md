---
name: llm-providers
description: "Configure transcript-based and video-understanding LLM clipping
  routes, provider prefixes, API keys, prompt format, and timestamp
  normalization for FunClip."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# LLM Providers

Use this sub-skill when the user needs to choose, configure, or debug a FunClip LLM backend.

## Handles

- `funclip/launch.py` `llm_inference` routing for transcript-based and video-understanding models.
- `funclip/llm/openai_api.py`, `qwen_api.py`, `litellm_api.py`, `g4f_openai_api.py`, and `twelvelabs_api.py`.
- The default prompt shape in `funclip/llm/demo_prompt.py`.
- The timestamp format expected by `funclip/utils/trans_utils.py::extract_timestamps`.
- AI Clip handoff: producing parseable `LLM Clipper Result` text for the clip-workflows sub-skill.

## Route elsewhere

- Transcript/video/audio state, clip execution, subtitle burn-in, offsets, and clip output files -> `../clip-workflows/SKILL.md`.
- Release archives, version packaging, and publishing -> `../release-packaging/SKILL.md`.

## Start here

- Read `references/providers.md` for the provider table and key/env rules.
- Read `references/prompt-format.md` for parseable `N. [HH:MM:SS,mmm-HH:MM:SS,mmm] text` output.
- Read `references/troubleshooting.md` for auth, import, timeout, and timestamp failures.
- Run `scripts/provider_route_smoke.py --repo-root <repo-root>` to check prefix stripping and Pegasus normalization without API calls.

## Natural requests this covers

- Set up GPT, Qwen, DeepSeek, AtlasCloud, MiniMax, LiteLLM, g4f, or TwelveLabs Pegasus for LLM clipping.
- Diagnose missing API keys, wrong model prefixes, empty model names, or region/base-URL mismatches.
- Make LLM output parseable by AI Clip.
- Normalize Pegasus decimal-second timestamps into SRT form.
- Decide when Pegasus needs an uploaded video instead of transcript-only input.
