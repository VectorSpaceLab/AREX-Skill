---
name: test_time_protocol
description: Validate fully test-time adaptation experiments so unlabeled target inputs are the only data used for adaptation updates.
---

# Fully Test-Time Adaptation Protocol

Use this skill when designing or auditing Tent-style adaptation experiments. It is appropriate for corruption robustness, domain adaptation, or proxy recovery runs where a source-trained model adapts during testing. Do not use it to justify domain adaptation that trains jointly on source and target data or any run that uses target labels in the adaptation loss.

## Inputs

- A JSON experiment metadata object with `adaptation_inputs`, `loss_inputs`, `evaluation_inputs`, and `mode` fields.
- Optional `notes` explaining whether the run is online, offline target-only, continual, or episodic.

## Outputs

- A JSON validation report with `ok`, `violations`, and `allowed_adaptation_inputs`.
- A concise protocol summary for recovery source manifests or experiment plans.

## Workflow

1. List all data consumed before and during optimizer steps.
2. Allow target inputs and pretrained model parameters in the adaptation loop.
3. Forbid source examples, source labels, target labels, and evaluation labels in the adaptation loss.
4. Permit labels only in evaluation fields after adaptation.
5. Record whether target batches are online, offline target-only, continual, or episodic.
6. Treat any forbidden adaptation input as a blocking protocol violation.

## Validation

Run `python scripts/protocol_check.py --self-test` or execute the tests with the Distiller skill validator. The self-test covers a valid target-only entropy run and invalid metadata that leaks labels into adaptation.

## Limitations

This skill checks experiment metadata rather than inspecting arbitrary training code. Pair it with command logs, source manifests, and recovery traces for final acceptance.


## Refinement Cycle 2
A label-leakage ablation returned a nonzero status as expected; keep target labels evaluation-only in all recovery metadata.
