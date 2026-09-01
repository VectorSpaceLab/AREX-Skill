---
name: online_stream_memory
description: Build bounded online continual-learning streams, replay memories, and forgetting ledgers for MIR-style experiments.
---

# Online Stream and Replay Memory

Use this skill when implementing or checking an online continual-learning experiment in the style of Maximally Interfered Retrieval. It is appropriate for bounded recovery runs, deterministic proxy experiments, and tests of replay-memory behavior. Do not use it to score MIR interference; that belongs to the virtual-update interference skill.

## Inputs
- Stream examples with `features`, `label`, `task_id`, and stable `example_id` fields.
- Memory capacity and candidate subset size.
- Optional seed for deterministic candidate sampling and replacement.
- Task-checkpoint accuracy values when computing forgetting.

## Outputs
- A bounded `ReplayMemory` state.
- Candidate replay examples sampled from current memory.
- A forgetting summary with per-task best, final, and forgetting values.

## Workflow
1. Initialize `ReplayMemory` with a fixed capacity and seed.
2. Before each online update, call `candidates(candidate_count)` to expose a bounded subset of stored examples.
3. After the model update, call `add_many(incoming_examples)` so memory changes after replay selection.
4. Record task accuracies after task boundaries or final evaluation.
5. Call `compute_forgetting(history)` to report average forgetting across tasks.

## Validation
Run `python -m pytest tests` or validate the skill tree with `validate_skill_tree.py --run-tests`. The tests use only the Python standard library and deterministic data.

## Limitations
The helper implements deterministic bounded replacement suitable for recovery and smoke tests. It preserves the online memory contract but is not a full high-throughput dataloader or framework-specific replay buffer.
