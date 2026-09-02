---
name: sar_wild_stream_protocol
description: Use this skill when a recovery or experiment needs to construct SAR-style dynamic wild-world test streams with mixed domains, small batches, and label imbalance.
---

# Wild Stream Protocol

## When To Use
Use this skill for SAR stable test-time adaptation work that needs: Represent dynamic wild-world test streams and reduced proxy streams for SAR-style TTA. Do not use it as a generic ImageNet-C runner or as permission to read the original SAR repository during recovery.

## Inputs
- corruption/domain names, label ordering policy, batch size, sample logits/features

## Outputs
- ordered stream metadata and resource provenance

## Workflow
1. Read the caller-provided stream, logits, parameter metadata, or entropy trace.
2. Apply the SAR-specific invariant documented in this skill: SAR is motivated by mixed shifts, small batches, and online imbalanced label streams rather than iid test batches.
3. Produce structured numeric evidence for recovery logs.
4. Keep proxy/reduced results explicitly labeled when the full ImageNet-C runtime is unavailable.

## Validation
Run `python scripts/wild_stream_protocol.py` when the script has a CLI, then run `python -m pytest tests` or the Distiller skill validator with `--run-tests`.

## Limitations
This skill captures a reusable SAR mechanism. It does not contain pretrained weights, ImageNet-C data, or original repository code, and it should be combined with other SAR skills for end-to-end recovery.
