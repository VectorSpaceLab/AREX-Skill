# Multimodal Guiders and Dynamic Conditioning

This reference covers the prompt-conditioning side of guidance: `GuiderParameters`, `MultimodalGuider`, and `DynamicConditioning`. For sampler choices, latent construction, decode, tiled sampling, and low-VRAM loader ordering, use `../core-generation/SKILL.md` from the sub-skill index. For expert-only STG/APG/Q8/tricks tuning, use `../advanced-control/SKILL.md`. Backend assumptions are in the root [model and backend requirements](../../../references/model-and-backend-requirements.md).

## `GuiderParameters`

`GuiderParameters` builds a dictionary of per-modality guidance controls. Required inputs:

| Input | Values/defaults from node | Meaning |
| --- | --- | --- |
| `modality` | `VIDEO` or `AUDIO`; default `VIDEO` | Which stream the parameters apply to. |
| `cfg` | default `1.0`, range `0.0` to `100.0` | Classifier-free guidance scale. `1.0` disables the unconditioned branch. |
| `stg` | default `1.0`, range `0.0` to `100.0` | Spatiotemporal skip-guidance perturbation scale. `0.0` disables perturbed prediction for that modality. |
| `perturb_attn` | default `true` | Whether this modality participates in perturbed attention for STG. |
| `rescale` | default `0.7`, range `0.0` to `100.0` | Rescales the guided noise prediction toward the positive prediction's standard deviation. `0.0` disables rescale. |
| `modality_scale` | default `0.0`, range `0.0` to `100.0` | Adds a term comparing normal prediction to a no-cross-modality prediction. Set `1.0` to disable this term. |
| `skip_step` | default `0`, range `0` to `100` | If `0`, no modality-step skipping. Otherwise that modality runs only every `skip_step + 1` steps and reuses the last denoised output on skipped steps. |
| `cross_attn` | default `true` | Allows cross-attention from the other modality on steps that are not skipped. |

Optional input:

- `parameters`: an existing `GUIDER_PARAMETERS` dictionary. Chain this to add the other modality.

Important source-backed guardrail: adding the same `modality` twice raises `ValueError: Modality <name> already exists in parameters`. Build at most one `VIDEO` entry and one `AUDIO` entry.

## `MultimodalGuider`

`MultimodalGuider` turns model, conditioning, and modality parameters into a `GUIDER` for sampler nodes.

Required inputs:

- `model`: the LTX model patcher.
- `positive`: positive `CONDITIONING`.
- `negative`: negative `CONDITIONING`.
- `parameters`: output from one or more chained `GuiderParameters` nodes.
- `skip_blocks`: comma-separated transformer block indices for STG-style block skipping. Empty string means no listed blocks.

Behavior:

- The guider clones the model and patches transformer blocks with STG wrappers.
- It stores positive/negative conditioning internally and exposes a sampler-compatible `GUIDER`.
- It unpacks model predictions into video and audio latent streams, applies each modality's `cfg`, `stg`, `rescale`, and `modality_scale`, then packs them back together.
- If only one modality has custom parameters, the other modality uses neutral defaults from the internal `GuiderParameters` class.
- `cross_attn` controls audio-to-video and video-to-audio cross-attention flags during prediction. Video parameters affect audio-to-video attention; audio parameters affect video-to-audio attention.
- `skip_step` can skip prediction for a modality on intermediate steps. Skipped steps reuse the last denoised output for that modality, so do not use skipping before a previous denoised value exists in an incompatible custom sampler.

A source-backed LTX-2.3 pattern chains an `AUDIO` parameter node into a `VIDEO` parameter node and feeds both to one `MultimodalGuider`; observed values included `skip_blocks` set to `28`, audio `cfg` larger than video `cfg`, and both modalities using nonzero `modality_scale`. Treat those as workflow starting points, not universal defaults.

## Parameter effects in plain language

The guided prediction for each modality is computed from four predictions when needed:

- positive prediction;
- negative/unconditioned prediction, only when `cfg` differs from `1.0`;
- perturbed/STG prediction, only when `stg` differs from `0.0`;
- no-cross-modality prediction, only when `modality_scale` differs from `1.0`.

Then optional rescale adjusts the standard deviation. Practical tuning order:

1. First make sure positive and negative conditioning are correct.
2. Set ordinary `cfg` strength.
3. Only then tune `stg`, `perturb_attn`, and `skip_blocks`.
4. For audio-video workflows, tune `modality_scale` and `cross_attn` if one stream dominates or bleeds into the other.
5. Use `rescale` to temper overstrong guidance artifacts after CFG/STG choices are stable.

If the user asks for deep STG layer-index theory, APG, Q8, PAG/FETA, attention banks, or inverse/flow-edit samplers, route to `../advanced-control/SKILL.md`.

## `DynamicConditioning`

`DynamicConditioning` patches a `MODEL` by installing a denoise-mask function. Required inputs:

- `model`: model to patch.
- `power`: default `1.3`, range `1` to `2`.
- `only_first_frame`: default `true`.

At each denoising step, it finds the current step from sigma values and raises the denoise mask to `power ** step`. With `only_first_frame=true`, it applies this only to the first frame's model channels; otherwise it applies to the full denoise mask. It also updates positive and negative conditioning entries that carry a `denoise_mask` model condition so ComfyUI keeps timestep values consistent.

Use it when a workflow needs the first-frame or mask conditioning effect to change over denoising steps. Place it on the model branch before the patched model reaches the guider/sampler path. Do not use it as a replacement for creating positive/negative text conditioning.

## Common graph patterns

### Video-only text-to-video or image-to-video

1. Produce positive and negative `CONDITIONING` by local Gemma or API path.
2. If using ordinary LTX sampler guidance, connect conditioning to the guider expected by the core workflow.
3. If using `MultimodalGuider`, create a `VIDEO` `GuiderParameters` node and connect it to `MultimodalGuider`.
4. Leave `AUDIO` parameters absent unless the latent/model graph actually has an audio stream.

### Audio-video or text-to-audio-capable model

1. Confirm the selected LTX checkpoint is an audio-video variant and the conditioning path can produce audio-compatible embeddings.
2. Create positive and negative conditioning for the prompt.
3. Chain `GuiderParameters` for `AUDIO` and `VIDEO` exactly once each.
4. Feed the chained parameter dictionary to `MultimodalGuider`.
5. Route audio-only latent setup, audio VAE decode, and speaker-reference token nodes to `../specialized-workflows/SKILL.md`.

### Dynamic first-frame emphasis

1. Build the normal model and conditioning graph first.
2. Insert `DynamicConditioning` on the model branch.
3. Keep `only_first_frame=true` for I2V/keyframe emphasis unless the user explicitly wants every denoise mask modified.
4. Start with `power` near the default and adjust gradually; values above `1` compound over steps.

## Failure signals

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Modality VIDEO already exists in parameters` or same for audio | Duplicate `GuiderParameters` node for one modality | Remove the duplicate or stop chaining the previous dictionary into the duplicate. |
| `skip_blocks` parsing fails | Non-integer token in comma-separated string | Use only integers separated by commas, or leave empty. |
| Audio/video influence feels coupled incorrectly | `cross_attn`, `modality_scale`, or missing modality parameters are inappropriate | Tune one modality at a time; set `modality_scale=1.0` to disable that correction term for comparison. |
| Guidance changes do nothing | The sampler is not using the `GUIDER` produced by `MultimodalGuider`, or conditioning is bypassed upstream | Trace the `GUIDER` output into the sampler and validate positive/negative conditioning first. |
| Dynamic conditioning has no visible effect | No denoise mask exists in the active conditioning/model path, or it is placed after the sampler path | Insert it before the model reaches the guider/sampler; confirm the workflow uses masked/image conditioning. |
