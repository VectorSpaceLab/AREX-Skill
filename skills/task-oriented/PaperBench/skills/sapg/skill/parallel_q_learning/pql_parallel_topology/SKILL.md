---
name: pql_parallel_topology
description: Build and validate the process topology for Parallel Q-Learning with actors, replay, policy learning, and value learning.
---

# PQL Parallel Topology

Use this skill when implementing or auditing a Parallel Q-Learning style recovery or experiment. It is appropriate when an off-policy learner should exploit many parallel simulation actors and separate data collection from policy and value updates. Do not use it for purely on-policy rollouts where learner updates must consume only the latest trajectories.

## Inputs

- `num_envs`: positive integer count of parallel actors or environments.
- `replay_capacity`: positive integer replay capacity.
- `actor_steps_per_tick`: positive integer rollout work per actor tick.
- `policy_updates_per_tick` and `value_updates_per_tick`: non-negative update counts.
- `sync_interval`: positive integer policy synchronization cadence.

## Outputs

- A topology JSON object with process roles, dataflow edges, and invariants.
- Validation errors when the configuration cannot exercise the PQL mechanism.

## Workflow

1. Create an actor role that writes transition batches to replay.
2. Create a replay role that stores off-policy transitions independently of the latest policy.
3. Create a value learner role that samples replay and updates Q estimates.
4. Create a policy learner role that improves actions using the value learner's Q estimates.
5. Add synchronization edges from policy learner to actors and value learner to policy learner.
6. Validate that the topology contains all required PQL roles before using it as recovery evidence.

## Validation

Run:

```bash
python scripts/topology.py --num-envs 8 --replay-capacity 64 --actor-steps-per-tick 2 --policy-updates-per-tick 1 --value-updates-per-tick 2 --sync-interval 4
python tests/test_topology.py
```

## Limitations

This skill defines the topology and invariants; it does not run an RL optimizer by itself. Pair it with a recovery harness or training skill for executable results.
