---
name: reverse_sampling_posterior
description: Compute DDPM predicted x0 and reverse posterior statistics from predicted epsilon.
---

# reverse_sampling_posterior

Use this skill when a recovery or implementation needs the DDPM mechanism from Ho et al. rather than a generic denoising routine.

## Inputs
Provide explicit numeric arrays or scalar fixtures, beta schedule parameters, timestep ids, and any predictor parameters required by the module. Inputs must not come from the original source repository during recovery.

## Outputs
Return deterministic JSON-serializable numeric evidence: coefficients, sampled noisy values, losses, posterior statistics, or recovery traces depending on the module.

## Workflow
1. Validate schedule length, beta range, shapes, and timestep bounds.
2. Execute the module's DDPM equation directly with deterministic fixtures when possible.
3. Record enough intermediate values for downstream recovery checks.
4. Keep full-result claims separate from reduced/proxy evidence.

## Validation
Run `python -m pytest tests` or `python scripts/ddpm_utils.py` from this skill directory. The bundled tests use only the Python standard library.

## Limitations
This skill captures the transferable paper mechanism and small deterministic tests. It does not include the original TensorFlow model, cloud data pipeline, or pretrained CIFAR-10 checkpoints.
