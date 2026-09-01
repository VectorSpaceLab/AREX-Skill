---
name: sar_sharpness_aware_update
description: Use this skill when implementing the SAM-like sharpness-aware two-step update used by SAR recovery experiments.
---

# Sharpness-Aware Update

## When To Use
Use this skill for SAR stable test-time adaptation work that needs: Run a two-step SAM-style update around reliable entropy minimization. Do not use it as a generic ImageNet-C runner or as permission to read the original SAR repository during recovery.

## Inputs
- trainable parameters, gradients or differentiable proxy model, reliable samples

## Outputs
- perturbation norm, first-step parameters, second-step updated parameters, loss trace

## Workflow
1. Read the caller-provided stream, logits, parameter metadata, or entropy trace.
2. Apply the SAR-specific invariant documented in this skill: SAR optimizes both entropy and entropy sharpness by minimizing entropy after an adversarial weight perturbation.
3. Produce structured numeric evidence for recovery logs.
4. Keep proxy/reduced results explicitly labeled when the full ImageNet-C runtime is unavailable.

## Validation
Run `python scripts/sharpness_aware_update.py` when the script has a CLI, then run `python -m pytest tests` or the Distiller skill validator with `--run-tests`.

## Limitations
This skill captures a reusable SAR mechanism. It does not contain pretrained weights, ImageNet-C data, or original repository code, and it should be combined with other SAR skills for end-to-end recovery.
