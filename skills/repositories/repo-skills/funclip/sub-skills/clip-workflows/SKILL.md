---
name: clip-workflows
description: "Use FunClip's ASR, text/speaker clipping, subtitle generation,
  model selection, and Gradio/CLI launch flows safely while routing provider and
  release work elsewhere."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# clip-workflows

Use this sub-skill when the task is about launching FunClip, choosing the ASR backend, running recognition then clipping, generating subtitles, or diagnosing text/speaker matching problems.

## What this covers

- Gradio launch and deployment flags: `--port`, `--listen`, `--share`.
- CLI stage 1/2 recognition and clipping workflows.
- `VideoClipper` core methods and state handling.
- Subtitle/time helpers, offsets, repeated text matching, and speaker diarization.
- Model selection for Paraformer, Fun-ASR-Nano, SenseVoice, and English Paraformer mode.
- Output directory behavior and subtitle file generation.

## Start here

1. Read [references/workflows.md](references/workflows.md) for Gradio, CLI, and programmatic recipes.
2. Read [references/cli-reference.md](references/cli-reference.md) for exact flags and stage 1/2 command patterns.
3. Read [references/api-reference.md](references/api-reference.md) for `create_asr_model`, `build_launch_kwargs`, `VideoClipper`, `runner`, and the subtitle helpers.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when clipping returns no matches, subtitles fail, or launch options do not behave as expected.
5. Run [scripts/clip_cli_smoke.py](scripts/clip_cli_smoke.py) with `--repo-root` to exercise the no-network matching path from any cwd.

## Route elsewhere

- API-key, provider, prompt, and LLM routing details belong in sibling [../llm-providers/](../llm-providers/).
- Release archives, checksum packaging, and publication steps belong in sibling [../release-packaging/](../release-packaging/).
- Do not use this sub-skill for live model download validation or media encoding verification unless the current run explicitly executes those paths.

## Operational notes

- Keep user-facing examples self-contained: use user-provided media paths, not repository fixture paths.
- Treat the bundled smoke script as the deterministic check for text matching and no-match behavior; it avoids model downloads and real media files.
- When a user needs clip-by-text, clip-by-speaker, subtitle overlay, or launch help, stay in this sub-skill instead of reopening the source repository.
