---
name: sample_factory_async_topology
description: Design and validate Sample Factory-style asynchronous rollout, policy, and learner topology with policy-lag estimates.
---

# Sample Factory Asynchronous Topology

Use this skill when designing or auditing a Sample Factory-style APPO training harness where environment simulation, policy inference, and learning should be separated into asynchronous components.

Do not use it to claim real throughput without a wall-clock benchmark. It provides topology contracts and deterministic estimates.

## Inputs
- Number of rollout workers, policy workers, and learners.
- Number of environments per rollout worker.
- Trajectory length and learner batch size.
- Optional component responsibility map.

## Outputs
- Component roles for rollout workers, policy workers, and learner.
- Queue contracts for observation requests, action replies, completed trajectories, and policy updates.
- Produced samples per rollout iteration.
- Policy-lag pressure estimate.

## Workflow
1. Keep rollout workers environment-only: they step environments and write transition fields.
2. Keep policy workers stateless: they batch observation-buffer indices and return action-buffer indices.
3. Keep the learner as the only component that consumes completed trajectories and updates trainable parameters for a policy.
4. Use compact queue messages that carry buffer indices, not serialized observations or trajectories.
5. Estimate lag pressure as `max(0, produced_samples / learner_batch_size - 1)`.
6. Reject designs where rollout workers compute gradients or policy workers modify rewards/returns.

## Validation
Run:

```bash
python scripts/topology_contract.py --rollout-workers 2 --policy-workers 1 --learners 1 --envs-per-worker 4 --trajectory-length 8 --learner-batch-size 32
python tests/test_topology_contract.py
```

## Limitations
The estimate abstracts away real IPC, GPU scheduling, and environment variance. Use it as mechanism guidance before running real profiling.
