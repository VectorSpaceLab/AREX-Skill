---
name: assets-and-models
description: "Manage Stable Diffusion WebUI checkpoints, VAEs, embeddings,
  hypernetworks, Lora/extra networks, upscalers, model paths, refresh endpoints,
  metadata, and asset troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Assets and Models

Use this sub-skill when the task is about placing, discovering, refreshing, validating, or diagnosing WebUI model assets rather than generating images or changing launch/security policy.

## Route Here For

- Checkpoint, VAE, embedding, hypernetwork, Lora/LyCORIS, and upscaler directory questions.
- Custom `--data-dir`, `--models-dir`, `--ckpt-dir`, `--vae-dir`, `--embeddings-dir`, `--hypernetwork-dir`, `--lora-dir`, or upscaler model-path flag issues.
- API/UI refresh and list questions for checkpoints, VAE, Lora, embeddings, hypernetworks, and upscalers.
- Safetensors metadata, checkpoint hashes, Lora hashes, missing asset cards, incompatible extra networks, or upscaler fallback diagnostics.

## Fast Decisions

- Prefer `.safetensors` for checkpoints, VAEs, and Lora when possible; `.ckpt`/`.pt` are supported in several places but may rely on pickle loading.
- Default model root is `models/` under `--data-dir`; `--models-dir` replaces that root, while `--ckpt-dir`, `--vae-dir`, `--lora-dir`, and upscaler path flags add or override specific searches.
- Refresh after placing files: use the relevant UI refresh button or API endpoint from [model-and-asset-layout.md](references/model-and-asset-layout.md).
- Lora prompt syntax is `<lora:name:weight>` with optional text-encoder, UNet, and dynamic-dimension overrides; see [extra-networks-and-lora.md](references/extra-networks-and-lora.md).
- When diagnosing without loading models, run [validate_asset_layout.py](scripts/validate_asset_layout.py) against the intended data/models directories first.

## Runtime References

- [Model and asset layout](references/model-and-asset-layout.md) lists default directories, launch flags, recognized suffixes, API endpoints, hashes, metadata, VAE resolution, and upscaler directories.
- [Extra networks and Lora](references/extra-networks-and-lora.md) covers Lora/LyCORIS discovery, prompt forms, aliases, hashes, metadata, and incompatibility signals.
- [Troubleshooting](references/troubleshooting.md) gives concrete triage paths for missing checkpoints, VAE discovery, hash mismatch, unsafe formats, Lora visibility, and upscaler fallback.
- [Layout validator script](scripts/validate_asset_layout.py) safely checks directory layout and recognized file suffixes with no WebUI imports and no model loading.

## Boundaries

- For txt2img/img2img payload fields, generation API schemas, or switching checkpoints during generation, route to `api-automation`.
- For launch-flag selection, networking, API exposure, authentication, or extension security, route to `launch-and-config`.
- For creating/training embeddings, hypernetworks, or checkpoints, route to `training-and-postprocessing`.
- For implementing or debugging extension code internals, route to `extension-scripting`.
