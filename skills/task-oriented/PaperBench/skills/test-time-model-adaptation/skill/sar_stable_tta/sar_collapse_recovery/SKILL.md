---
name: sar_collapse_recovery
description: Use this skill when tracking SAR entropy EMA and deciding whether a model or optimizer reset is required after collapse.
---

# Collapse Recovery

## When To Use
Use this skill for SAR stable test-time adaptation work that needs: Track EMA entropy and trigger reset when SAR detects collapse. Do not use it as a generic ImageNet-C runner or as permission to read the original SAR repository during recovery.

## Inputs
- current reliable entropy, prior EMA, reset threshold, saved state metadata

## Outputs
- updated EMA, reset decision, restored-state flag

## Workflow
1. Read the caller-provided stream, logits, parameter metadata, or entropy trace.
2. Apply the SAR-specific invariant documented in this skill: The method avoids collapse by resetting the model when moving-average entropy becomes suspiciously small.
3. Produce structured numeric evidence for recovery logs.
4. Keep proxy/reduced results explicitly labeled when the full ImageNet-C runtime is unavailable.

## Validation
Run `python scripts/collapse_recovery.py` when the script has a CLI, then run `python -m pytest tests` or the Distiller skill validator with `--run-tests`.

## Limitations
This skill captures a reusable SAR mechanism. It does not contain pretrained weights, ImageNet-C data, or original repository code, and it should be combined with other SAR skills for end-to-end recovery.
