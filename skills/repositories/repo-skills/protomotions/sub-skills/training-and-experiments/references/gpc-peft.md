# GPC and PEFT workflow

GPC trains a discrete latent prior from a motion tracker, then adapts that prior to task skills with parameter-efficient fine-tuning.

## Stages

1. **Tracker**: train a motion tracker with an FSQ bottleneck. The encoder maps target poses to FSQ codes; the quantizer creates token indices; the decoder maps tokens back to actions.
2. **Prior**: train the autoregressive discrete prior from frozen tracker-derived expert rollouts and context observations.
3. **SFT**: bootstrap a task adapter with supervised fine-tuning, using tracker-provided target tokens and task observations.
4. **RLFT**: fine-tune the adapter with PPO/task rewards, optionally with AMP rewards.
5. **Inference**: load the correct inference checkpoint role and run through the same resolved-config lifecycle.

## PEFT config contract

The actor shape is centered on `DiscretePriorPEFTActorConfig`:

- `actor.in_keys` declares task observations used to build PEFT conditioning.
- `actor.peft.model` consumes those keys and writes `actor.peft.condition_key`.
- The frozen prior's context keys are discovered from the prior checkpoint at runtime.
- Legacy fields such as `task_conditioning_keys`, actor-level target/terrain context keys, or old `actor.mu` submodule paths should not be used for current PEFT configs.

## Checkpoint roles

| Artifact | Role | Caution |
| --- | --- | --- |
| Tracker checkpoint | Supplies FSQ encoder/decoder timing and tokens for prior/SFT | Must expose the expected FSQ bottleneck. |
| Prior `last.ckpt` or prior inference artifact | Frozen base prior for SFT/RLFT | PEFT loads the whole prior model, not an old actor submodule. |
| SFT/RLFT `last.ckpt` | Resume or warm-start | Contains optimizer/training state and full PEFT model. |
| SFT/RLFT `inference_last.ckpt` | Inference/share | Do not use as training resume state. |

## KL and sampling

During RLFT, the PEFT agent pins an anchor from the checkpoint-loaded adapter/prior at fit start. With `kl_coeff > 0`, active adapter logits are regularized against the anchor. With `sampling_mode="prior_constraint"`, rollouts sample from the active adapter while constraining support to the anchor prior's top-p nucleus.

## Debugging route

- If prior loading fails, check whether the supplied checkpoint is a full model artifact.
- If SFT/RLFT observations mismatch, inspect `actor.in_keys`, `condition_key`, and the task observation component.
- If resume behaves unexpectedly, remember it loads the checkpoint state first, then pins the anchor from the loaded state.
