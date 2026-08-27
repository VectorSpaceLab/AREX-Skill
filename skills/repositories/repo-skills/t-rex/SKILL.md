---
name: t-rex
description: "Use the T-Rex2 cloud API wrapper for visual-prompt object
  detection, embeddings, visualization, and the optional Gradio demo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# T-Rex Repo Skill

Use this skill when a task asks for T-Rex2, T-Rex visual prompts, DeepDataSpace T-Rex API calls, generic object detection from text/visual prompts, reusable visual embeddings, detection rendering, or the optional Gradio demo.

T-Rex2 in this repository is a Python cloud API wrapper, not a local model checkpoint or training framework. Live detections require a DeepDataSpace API token and network access; local GPU/accelerator hardware is not required for the selected workflows.

## First checks

1. Confirm that the task really needs T-Rex2's visual prompt cloud API or renderer.
2. Install the package in the user's working environment. For a source checkout or source archive, use a clean Python environment, install runtime dependencies such as `requests`, `Pillow`, `numpy`, `pydantic==2.10.6`, and `gradio==4.44.1`, then install the package. If source metadata build fails on `torch`, read [references/troubleshooting.md](references/troubleshooting.md); this is a setup-time packaging quirk, not a local GPU requirement.
3. If package availability is uncertain, run the bundled offline smoke check from this skill directory:

   ```bash
   python scripts/check_trex_install.py --json
   ```

4. For live cloud calls, confirm the user can provide a token through `--token` or `T_REX_API_TOKEN`; do not log or persist secrets.
5. Before refreshing this skill against a checkout, read [references/repo-provenance.md](references/repo-provenance.md).

## Routes

| User task | Read |
|---|---|
| Build or validate prompt JSON, call `TRex2APIWrapper`, run interactive/generic visual prompt detection, create visual embeddings, or run embedding inference | [sub-skills/cloud-api-workflows/SKILL.md](sub-skills/cloud-api-workflows/SKILL.md) |
| Draw boxes or points, filter detections by score, fix detection JSON, operate/debug the optional Gradio demo, or handle `score.item` visualization errors | [sub-skills/visualization-and-demo/SKILL.md](sub-skills/visualization-and-demo/SKILL.md) |
| Install/import failures, setup-time `torch` failures, Gradio dependency compatibility, token/network boundary, or backend questions | [references/troubleshooting.md](references/troubleshooting.md) |
| Check source commit, package version, evidence paths, or staleness | [references/repo-provenance.md](references/repo-provenance.md) |

## Package and dependency facts

- Public import surface: `from trex import TRex2APIWrapper, visualize`.
- Installed distribution metadata verified as `trex==1.0`; source `trex/version.py` contains `v1.0`.
- Source package metadata pins `pydantic==2.10.6` and `gradio==4.44.1`.
- Source modules import `requests`, `Pillow`, and `numpy`; ensure they are available even when not named in the package requirement file.
- `setup.py` imports `torch.utils.cpp_extension` during source installation. This is a setup-time packaging quirk, not evidence of local GPU inference.
- The optional Gradio demo also uses `gradio-image-prompter` and may need `huggingface_hub<1.0` with Gradio 4.44.1.

## Common operating patterns

- Use `--dry-run` on cloud sub-skill scripts to validate prompt images and JSON without any network call.
- Use rectangle prompts in `[x1, y1, x2, y2]` pixel coordinates and reuse `category_id` for the same object class across references.
- Treat visual embedding files as base64 text strings expected by `TRex2APIWrapper.embedding_inference`, not as model checkpoints.
- Keep raw detection JSON unfiltered when possible; filter only for visualization unless the user asks to discard low-score detections.
- Convert `scores`, `labels`, and `boxes` to NumPy arrays before calling `trex.visualize` directly.

## Non-goals and avoid-when

- Do not use this skill for training T-Rex, DINOv, GroundingDINO, YOLO, SAM, or other local detection models.
- Do not use it when the user needs a fully offline detector with no cloud API token.
- Do not tell future agents to open or run original repo examples or docs. The needed example behavior is distilled into this skill's references and bundled scripts.
- Do not import or export this skill from Creator mode unless a separate verification/import task explicitly asks for it; this run was created with a no-import policy.
