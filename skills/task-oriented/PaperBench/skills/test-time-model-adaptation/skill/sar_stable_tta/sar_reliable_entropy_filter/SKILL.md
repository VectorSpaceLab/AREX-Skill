---
name: sar_reliable_entropy_filter
description: Use this skill when implementing SAR reliable entropy minimization, entropy-margin filtering, or proxy checks for selected samples.
---

# Reliable Entropy Filter

## When To Use
Use this skill for SAR stable test-time adaptation work that needs: Compute softmax entropy and select reliable samples below the SAR entropy margin. Do not use it as a generic ImageNet-C runner or as permission to read the original SAR repository during recovery.

## Inputs
- logits, class count, optional margin

## Outputs
- per-sample entropy values, selected indices, mean reliable entropy

## Workflow
1. Read the caller-provided stream, logits, parameter metadata, or entropy trace.
2. Apply the SAR-specific invariant documented in this skill: Entropy is a practical proxy for excluding samples with large noisy gradients during online adaptation.
3. Produce structured numeric evidence for recovery logs.
4. Keep proxy/reduced results explicitly labeled when the full ImageNet-C runtime is unavailable.

## Validation
Run `python scripts/reliable_entropy_filter.py` when the script has a CLI, then run `python -m pytest tests` or the Distiller skill validator with `--run-tests`.

## Limitations
This skill captures a reusable SAR mechanism. It does not contain pretrained weights, ImageNet-C data, or original repository code, and it should be combined with other SAR skills for end-to-end recovery.
