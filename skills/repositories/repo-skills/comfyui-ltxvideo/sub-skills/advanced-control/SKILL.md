---
name: advanced-control
description: "Route expert agents to STG/APG, Q8/VAE patching, latent
  normalization, decoder-noise control, attention and flow-edit tricks,
  PAG/FETA, RF samplers, inverse prediction, and utility nodes."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Advanced Control

Use this sub-skill for expert-only control over LTX model internals. It is the right place for advanced guider tuning, optional Q8 paths, latent/stat normalization, decoder-noise tweaks, attention-bank/override behavior, flow-edit, PAG/FETA, RF forward/reverse samplers, inverse-model sampling, and small utility nodes.

## Route here
- STG/APG block skipping, sigma scheduling, preset selection, or expert guider parameters.
- Q8 patching, Q8 LoRA loading, or VAE patch support.
- Latent/stat normalization or decode-noise control.
- Attention bank / override, flow-edit, PAG, FETA, RF inverse/ODE samplers, or model-sampling prediction patching.
- Small helper nodes such as float-to-int or image-to-CPU conversions.

## Route elsewhere
- Normal T2V/I2V/V2V graph assembly, sampler choice, or decode ordering -> [core-generation](../core-generation/SKILL.md)
- Prompt, Gemma, conditioning, or generic guider setup -> [prompt-conditioning](../prompt-conditioning/SKILL.md)
- IC-LoRA recipes, motion-track, HDR, audio, masks, or upscaler workflows -> [specialized-workflows](../specialized-workflows/SKILL.md)

## Reference set
- Root install/backend notes -> [model-and-backend-requirements](../../references/model-and-backend-requirements.md)
- STG/APG guide -> [stg-apg-guiders](references/stg-apg-guiders.md)
- Q8 and patch order -> [q8-and-patches](references/q8-and-patches.md)
- Experimental tricks and utility helpers -> [experimental-tricks](references/experimental-tricks.md)
- Troubleshooting -> [troubleshooting](references/troubleshooting.md)
- Safe Q8 preflight -> [q8_preflight.py](scripts/q8_preflight.py)

## Rules of thumb
1. If the task is only about choosing a basic graph or prompt route, hand off to the sibling skill instead of staying here.
2. If the task only asks for ordinary `cfg`, `rescale`, or guider plumbing, check prompt-conditioning first unless the user explicitly asks for expert STG/APG behavior.
3. Treat Q8 and trick nodes as optional and experimental. Do not imply native execution proof unless the environment and a real run actually show it.
4. Prefer the smallest control surface that solves the problem; avoid patching internals when a standard guider is enough.

## Evidence surface
- Live-node categories inspected: `lightricks/LTXV`, `ltxtricks`, and `ltxtricks/attn`.
- Source-inspected families: STG/APG, Q8 patching, VAE patching, latent/stat normalization, decoder noise, flow-edit, attention bank/override, PAG/FETA, RF samplers, inverse model prediction, and utility nodes.
- This sub-skill is route-verified and self-contained; it does not claim a native run for every advanced combination.
