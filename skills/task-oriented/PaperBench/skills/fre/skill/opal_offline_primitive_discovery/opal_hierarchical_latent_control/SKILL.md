---
name: opal_hierarchical_latent_control
description: Relabel downstream data with OPAL primitive latents and evaluate high-level latent control over temporally extended actions.
---

# OPAL Hierarchical Latent Control

## When To Use
Use this skill after primitive latents and decoder parameters are available. It tests the OPAL downstream interface: a high-level policy chooses a latent every `c` steps and the low-level primitive decoder supplies primitive actions.

## Inputs
- Segment JSON and primitive objective output with latent assignments and decoder prototypes.
- A sparse proxy goal or reward-labeled downstream data.
- Primitive horizon `c`.

## Outputs
- Latent-labeled high-level dataset summary.
- Rollout trace with latent decisions and decoded primitive actions.
- Success rate and effective horizon.

## Workflow
1. Relabel each segment using encoder/assignment output.
2. Build a high-level action table in latent space.
3. Select latents that move toward the goal while staying among learned primitive labels.
4. Decode each latent for `c` primitive steps.
5. Report success and compare latent decisions with primitive action count.

## Validation
Run:

```bash
python tests/test_hierarchical_control.py
```

## Limitations
The bundled controller is deterministic and intended for reduced proxy recovery. Full offline RL algorithms such as CQL must be integrated separately when available.
