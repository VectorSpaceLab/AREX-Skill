---
name: tensor_api_buffer_contract
description: Validate direct state action observation and reward buffer contracts for Isaac Gym style pipelines.
---

# Tensor API Buffer Contract

Use this skill when checking whether a reduced or real recovery preserves Isaac Gym's direct tensor-buffer idea. The skill validates named state, action, observation, reward, and reset buffers, their shapes, and whether a claimed direct path includes forbidden CPU staging.

## Inputs
- Buffer descriptors with `name`, `role`, `shape`, `producer`, `consumer`, and `direct` fields.
- Expected environment count for the leading batch dimension.

## Outputs
- A report with `ok`, `errors`, `direct_flow_ok`, and `roles_present`.

## Workflow
1. Collect descriptors for physics state, policy action, observation, reward, and reset buffers.
2. Verify each descriptor has a leading batch dimension matching the environment count.
3. Reject missing producer/consumer ownership or `direct=False` when direct flow is claimed.
4. Save the report as recovery evidence or use it as a cross-check from a harness.

## Validation
Run `python tests/test_buffer_contract.py` or validate the skill tree with tests enabled.

## Limitations
This deterministic checker verifies the contract. It cannot prove CUDA pointer aliasing without a real GPU tensor runtime.

## Edge-Case Refinement
A negative check must fail when a descriptor uses the wrong leading environment dimension or marks a buffer as non-direct, because such staging would violate the paper Tensor API mechanism.
