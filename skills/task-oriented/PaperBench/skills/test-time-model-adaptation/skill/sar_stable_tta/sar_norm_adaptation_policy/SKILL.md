---
name: sar_norm_adaptation_policy
description: Use this skill when selecting trainable parameters for SAR-style test-time adaptation while freezing non-normalization model weights.
---

# Norm Adaptation Policy

## When To Use
Use this skill for SAR stable test-time adaptation work that needs: Configure a model or parameter set so test-time adaptation updates only normalization affine parameters. Do not use it as a generic ImageNet-C runner or as permission to read the original SAR repository during recovery.

## Inputs
- model parameter metadata or small proxy parameter dict

## Outputs
- trainable parameter selection and frozen parameter report

## Workflow
1. Read the caller-provided stream, logits, parameter metadata, or entropy trace.
2. Apply the SAR-specific invariant documented in this skill: Stable wild TTA requires batch-agnostic normalization and restricted affine adaptation instead of full model updates.
3. Produce structured numeric evidence for recovery logs.
4. Keep proxy/reduced results explicitly labeled when the full ImageNet-C runtime is unavailable.

## Validation
Run `python scripts/norm_adaptation_policy.py` when the script has a CLI, then run `python -m pytest tests` or the Distiller skill validator with `--run-tests`.

## Limitations
This skill captures a reusable SAR mechanism. It does not contain pretrained weights, ImageNet-C data, or original repository code, and it should be combined with other SAR skills for end-to-end recovery.
