---
name: bootstrapped-texture
description: "Plan DreamCraft3D texture boosting with Zero123++ multiviews,
  DreamBooth LoRA, and model artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Bootstrapped Texture

Use this sub-skill when a DreamCraft3D task involves optional texture boosting, Janus/multiview consistency mitigation, Zero123++ image-to-multiview generation, DreamBooth/LoRA personalization, Stable Diffusion BSD guidance, or model artifact planning.

## Read first

- Read [references/dreambooth-and-multiview.md](references/dreambooth-and-multiview.md) for the optional multiview-to-DreamBooth workflow and how LoRA weights plug back into staged generation.
- Read [references/model-artifacts.md](references/model-artifacts.md) for Stable Zero123, DeepFloyd IF, Stable Diffusion, Omnidata, and local cache/checkpoint expectations.
- Read [references/troubleshooting.md](references/troubleshooting.md) when the optional branch fails because of Janus artifacts, `local_files_only`, hard-coded GPU ids, xformers/bitsandbytes, OOM, or invalid multiview images.
- Use [scripts/plan_texture_boosting.py](scripts/plan_texture_boosting.py) to produce a non-mutating prerequisite report and suggested commands. It does not download, generate images, or train LoRA.

## When to use this sub-skill

Use it for requests like:

- "The stage-1 result has the Janus problem; should I train a custom prior?"
- "Plan the Zero123++ multiview and DreamBooth LoRA branch."
- "Where should Stable Zero123 or Omnidata checkpoints live?"
- "How do I pass LoRA weights into a DreamCraft3D launch command?"
- "Why does `img_to_mv.py` fail on `cuda:1` or local model cache?"

## Safe protocol

1. First make the core pipeline route explicit with `generation-pipeline`. Texture boosting is optional and expensive.
2. Check whether the failure is actually an image/sidecar issue before starting multiview generation.
3. Plan model artifacts and device ids. The source multiview helper uses `local_files_only=True` and hard-codes `cuda:1`, so future agents should adapt the command/device carefully.
4. Only run Zero123++ generation or DreamBooth/LoRA training after the user approves GPU time, model downloads/cache use, and output locations.

## Quick planner

```bash
python <skill-dir>/sub-skills/bootstrapped-texture/scripts/plan_texture_boosting.py \
  --image-path load/images/mushroom_log_rgba.png \
  --prompt "a photo of mushroom" \
  --instance-dir .cache/temp \
  --lora-output-dir .cache/if_dreambooth_mushroom
```

Use `--json` for structured output.

## Route elsewhere

- Core staged command chain and checkpoint handoff: `generation-pipeline`.
- Preprocessed image sidecars: `image-preparation`.
- Exporting meshes or summarizing outputs: `export-and-evaluation`.
- Docker, Gradio, and broad dependency triage: `interfaces-and-monitoring`.
