---
name: opal_primitive_autoencoding_objective
description: Train or check an OPAL-style primitive autoencoding objective with reconstruction loss and KL-style prior matching.
---

# OPAL Primitive Autoencoding Objective

## When To Use
Use this skill when a recovery needs to learn latent primitive summaries from fixed-horizon offline segments. It is appropriate for full neural training or a declared reduced proxy that preserves reconstruction, latent assignment, and prior matching.

## Inputs
- Segment JSON produced by `opal_offline_segment_protocol`.
- Number of latent primitives for reduced recovery.
- Beta/KL weight and update count.

## Outputs
- Reconstruction loss before and after updates.
- Prior/KL-style penalty before and after updates.
- Segment latent assignments.
- Decoder prototype parameters before and after updates.

## Workflow
1. Load fixed-horizon state-action segments.
2. Infer a latent assignment from each segment's action pattern.
3. Decode actions from latent-conditioned prototype parameters.
4. Compute mean squared reconstruction loss and a prior-matching penalty from initial state to latent assignment.
5. Apply real parameter updates to decoder prototypes.
6. Report latent separation and optimizer/update evidence.

## Validation
Run:

```bash
python tests/test_primitive_objective.py
```

## Limitations
The bundled script is a reduced deterministic proxy, not a full neural beta-VAE. It must be labeled as reduced recovery when used as primary experiment evidence.
