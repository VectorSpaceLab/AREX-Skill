---
name: sequential_replay_protocol
description: Model P3O iteration ordering by appending current rollouts before bounded sequential replay mini-batch updates.
---

# Sequential Replay Protocol

Use this skill to preserve Algorithm 1 ordering: collect current trajectories, update on-policy, then sample replay updates. Do not use it as a simulator or environment wrapper.

## Inputs
- Existing replay buffer records.
- Fresh rollout records with stored behavior policy probabilities.
- Maximum buffer size and replay update count.

## Outputs
- Updated replay buffer.
- Ordered update trace showing on-policy before off-policy replay.
- Replay mini-batches with source ids.

## Workflow
1. Append fresh rollouts and trim the buffer to the configured maximum size.
2. Emit the fresh rollout ids as the on-policy update batch.
3. Select replay mini-batches deterministically for bounded recovery or via a supplied sampler in larger runs.
4. Record trace entries so analysis can verify policy-on then policy-off execution.

## Source Boundary
Use this skill with the paper, module documents, generated artifacts, and ordinary package documentation. Do not read or depend on the original P3O repository.

## Validation
Run `python scripts/<script>.py --self-test` or `python -m pytest tests` from the skill directory. The bundled tests use only the Python standard library.

