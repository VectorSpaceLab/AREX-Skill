---
name: robustness_benchmark_protocol
description: Validate clean and shifted robustness benchmark protocols with class-overlap and metric-gap contracts.
---

# Robustness Benchmark Protocol

Use this skill when an experiment needs an ImageNet-R-style robustness protocol: a clean control split, a shifted split, a shared label set, and an explicit metric direction. Do not use it to claim full ImageNet reproduction; it only validates benchmark structure and computes gap semantics.

## Inputs
- Clean examples as dictionaries with `id`, `label`, and optional features.
- Shifted examples with the same label vocabulary.
- Metric name and direction: `lower_is_better` for error or `higher_is_better` for accuracy.

## Outputs
- A benchmark specification with clean classes, shifted classes, overlap status, and metric direction.
- A gap value computed as shifted minus clean for error metrics or clean minus shifted for accuracy metrics.

## Workflow
1. Load or construct clean and shifted example lists.
2. Verify that the shifted labels are a subset of the clean labels.
3. Record the shift type and class-overlap evidence.
4. Compute clean/shifted metric gaps using direction-aware semantics.
5. Reject protocols that hide class mismatch or metric direction.

## Validation
Run `python tests/test_protocol.py` or validate the tree with the Distiller skill validator.

## Limitations
This skill validates protocol mechanics. It does not download ImageNet-R, train models, or certify that a proxy dataset is equivalent to the paper benchmark.
