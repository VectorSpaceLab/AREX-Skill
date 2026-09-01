---
name: lora_merge_latency
description: Merge LoRA low-rank factors into a dense weight and verify deployment-equivalent inference.
---

# LoRA Merge Latency

Use this skill when deploying or validating LoRA without extra inference latency. It consumes a base weight and trained factors and emits a merged dense matrix plus equivalence checks.

## Inputs
`W0`, `A`, `B`, `alpha`, and test inputs.

## Outputs
Merged weight `W`, unmerged-vs-merged maximum error, and optional restored base weight.

## Workflow
Compute `W = W0 + (alpha/r) BA`, run the ordinary dense layer, compare it with the unmerged LoRA forward pass, and record a tight numerical tolerance.

## Validation
Run the included tests or validate the skill tree with tests.

## Limitations
Merging one adapter at a time is appropriate for single-task batches; mixed adapters may require unmerged dynamic routing.
