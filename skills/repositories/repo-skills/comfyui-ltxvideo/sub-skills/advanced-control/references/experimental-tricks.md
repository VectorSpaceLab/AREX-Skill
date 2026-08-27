# Experimental Tricks and Utility Nodes

Related routes: [root backend requirements](../../../references/model-and-backend-requirements.md) · [specialized-workflows](../../specialized-workflows/SKILL.md) · [core-generation](../../core-generation/SKILL.md)

Everything in this reference is optional, brittle, and expert-only. Prefer the simpler sibling skills unless the user explicitly wants these behaviors.

## Model patchers and latent anchors

- `ModifyLTXModel` injects the modified LTX model classes used by the trick stack. Use it only when a downstream trick node requires the patched model behavior.
- `AddLatentGuide` inserts an image latent into a latent stream at a chosen index and strength. Use it when the user wants reference-frame anchoring rather than ordinary prompt conditioning.

## Attention bank and override tools

- `LTXAttentionBank` creates an attention bank with a save-step budget and a block map.
- `LTXPrepareAttnInjections` converts that bank into an injection plan. `query`, `key`, and `value` decide which tensors are replaced. `inject_steps` must not exceed saved steps. Optional `blocks` narrows the bank to specific blocks.
- `LTXAttentioOverride` builds a block set for RF-edit style helpers. The spelling is intentionally odd in the node name.
- `LTXAttnOverride` builds the layer set consumed by `LTXPerturbedAttention`.

Use the bank/override tools only when the user is explicitly trying to carry attention across a forward/backward pass or to target specific layers.

## PAG and FETA

- `LTXPerturbedAttention` applies perturbed attention or a blurred surrogate depending on the selected mode. `scale`, `rescale`, and `cfg` are the main knobs; `attn_override` selects the layers.
- `LTXFetaEnhance` sets `feta_weight` and the chosen attention layers for FETA scoring.

These are not normal quality-fixing tools. They are for users who already know they want perturbed-attention or FETA behavior.

## Flow-edit, inverse model prediction, and RF samplers

- `LTXFlowEditCFGGuider` separates source and target conditioning and lets them use different CFG values.
- `LTXFlowEditSampler` skips early steps and optionally refines the last steps.
- `LTXForwardModelSamplingPred` and `LTXReverseModelSamplingPred` patch the model sampling convention for forward/reverse prediction experiments.
- `LTXRFForwardODESampler` and `LTXRFReverseODESampler` implement the controlled forward/reverse ODE samplers used for RF-inverse style edits. They accept linear, increasing, or decreasing gamma/eta trends, and they can also carry attention-bank injection state.

Important caveat: the source tree also contains lower-level RF-edit helpers, but the live node map exposes the exported `LTXRF*` nodes. Route by the exported live nodes unless you are debugging the source implementation itself.

## Latent/stat normalization

- `LTXVAdainLatent` matches latent channel statistics to a reference latent.
- `LTXVStatNormLatent` normalizes a latent toward a target mean and standard deviation using a percentile window.
- `LTXVPerStepAdainPatcher` and `LTXVPerStepStatNormPatcher` apply the same ideas gradually through post-CFG hooks.

Rules of thumb:

- `per_frame=True` only makes sense when the reference latent has the same frame structure, or one frame that can be repeated.
- If the target has more frames than the reference in per-frame mode, the node should be treated as a shape mismatch, not as a model bug.
- Use the per-step patchers when you want a gradual bias instead of a one-shot latent rewrite.

## Decoder noise and utility nodes

- `Set VAE Decoder Noise` sets decoder timestep, noise scale, and seed on the VAE object.
- `LTXFloatToInt` is a glue node for rounding values into integer inputs.
- `ImageToCPU` is a simple tensor move helper for CPU-side inspection or downstream CPU-only nodes.

## Utility support modules

The trick stack also relies on small support helpers that are not standalone routing targets:

- attention bank container
- FETA score helper
- latent wrapper helper
- class-name helper
- noise helpers used by the reversible sampler math

## When not to use this reference

- If the user only wants a normal graph or sampler choice, route to the sibling generation skill.
- If the user only wants prompt or guider setup, route to the conditioning skill.
- If the user only wants an IC-LoRA workflow recipe, route to the specialized-workflows skill unless the question is specifically about advanced attention or control behavior.
