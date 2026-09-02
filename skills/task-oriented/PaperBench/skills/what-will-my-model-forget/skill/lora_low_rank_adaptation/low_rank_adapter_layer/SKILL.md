---
name: low_rank_adapter_layer
description: Construct LoRA low-rank linear adapters and verify merged inference equivalence without relying on the original implementation repository.
---

# Low-Rank Adapter Layer

Use this skill when implementing or validating the LoRA layer mechanism from the paper. It is appropriate for linear, embedding-like, or projection-style weights where a frozen base matrix receives a trainable low-rank update. Do not use it to claim full benchmark recovery by itself; it only validates the adapter layer contract.

## Inputs
- Frozen base weight matrix `W0` with shape output by input.
- Rank `r`, alpha scale, LoRA matrix `A` with shape rank by input, and `B` with shape output by rank.
- One or more input vectors for forward checks.

## Outputs
- Dynamic prediction `W0 x + (alpha/r) B A x`.
- Merged weight `W0 + (alpha/r) B A` and numerical merge-equivalence evidence.
- Trainable parameter count `r * (input + output)`.

## Workflow
1. Keep the base weight immutable and represent adaptation only through `A` and `B`.
2. Scale the low-rank branch by `alpha / r` when rank is positive.
3. Initialize or test `B = 0` to confirm the initial model exactly matches the frozen pretrained model.
4. For inference validation, merge the low-rank delta into the base weight and compare merged and dynamic predictions.
5. Report rank, parameter count, and maximum absolute prediction difference as explicit mechanism evidence.

## Validation
Run `python scripts/lora_math.py --input <fixture.json>` or the included tests. The tests check zero-branch identity, trainable-parameter counting, and merged inference equivalence.

## Limitations
This skill uses deterministic matrix arithmetic and does not load PyTorch, Transformers, pretrained checkpoints, or the original LoRA repository.
