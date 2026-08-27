---
name: janus
description: "Routes Janus, Janus-Pro, and JanusFlow workflows for multimodal
  understanding, text-to-image generation, and demo or service adaptation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Janus

Use this skill for the DeepSeek Janus family:

- **Janus / Janus-Pro** multimodal understanding and autoregressive text-to-image generation.
- **JanusFlow** understanding and rectified-flow text-to-image generation.
- **Demo/service adaptation** for Gradio, FastAPI, and client workflows.

Start here when the task names Janus, Janus-Pro, JanusFlow, image question answering, OCR/formula conversion, text-to-image generation, or a local demo/server.

## Quick install

Read [`references/installation-and-models.md`](references/installation-and-models.md) for the verified install variants and model-family notes. The usual starting point is:

```bash
pip install -e .
```

Use one of the extra installs only when the task needs it:

- `pip install -e .[gradio]` for the Gradio demos.
- `pip install diffusers[torch]` or another compatible diffusers build for JanusFlow generation.

If import behavior is unclear, run [`scripts/check_janus_environment.py`](scripts/check_janus_environment.py) from any working directory.

## Routes

- [`sub-skills/multimodal-understanding/SKILL.md`](sub-skills/multimodal-understanding/SKILL.md) — image+question prompts, image loading, processor batchification, and answer generation.
- [`sub-skills/image-generation/SKILL.md`](sub-skills/image-generation/SKILL.md) — Janus / Janus-Pro autoregressive image generation.
- [`sub-skills/janusflow-workflows/SKILL.md`](sub-skills/janusflow-workflows/SKILL.md) — JanusFlow understanding and rectified-flow image generation.
- [`sub-skills/demos-and-serving/SKILL.md`](sub-skills/demos-and-serving/SKILL.md) — Gradio demos, FastAPI endpoints, and client adaptation.

## Minimal verification

When you only need to confirm that the package is importable and the public APIs are visible, use the environment check script first, then inspect the relevant sub-skill:

1. Import the package and confirm the installed distribution.
2. Verify the route-specific classes or helpers you need.
3. Choose the sub-skill that matches the user request instead of guessing from file names.

## What this skill covers

- Prompt formatting and image placeholder handling.
- `janus.utils.io.load_pil_images` for file-path and `data:image/...` inputs.
- `VLMImageProcessor`, `VLChatProcessor`, and `MultiModalityCausalLM` for Janus / Janus-Pro understanding.
- Janus generation loops that use classifier-free guidance and VQ decoding.
- JanusFlow's rectified-flow generation path, including its diffusers/VAE dependency.
- Gradio and FastAPI demo adaptation without depending on the original checkout.

## What this skill does not do

- It does not run the large model downloads or demos automatically.
- It does not tell future agents to open source-checkout files.
- It does not replace route-specific troubleshooting; read the nearest sub-skill reference when something fails.

## Provenance

Read [`references/repo-provenance.md`](references/repo-provenance.md) before using this skill on a different checkout or before refreshing it.
