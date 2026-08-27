---
name: data-collection
description: "Use Tianshou data carriers, replay buffers, collectors, return
  batches, and collection statistics safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Collection

Use this sub-skill when a task mentions Tianshou `Batch` slicing/merging, `BatchProtocol`, `ReplayBuffer`, `VectorReplayBuffer`, `PrioritizedReplayBuffer`, `HERReplayBuffer`, `Collector.collect`, `AsyncCollector`, n-step return inputs, collection hooks, `CollectStats`, `InfoStats`, `SequenceSummaryStats`, or `MalformedBufferError`.

## Route First

- For trainer loops, epoch orchestration, `Experiment.run`, or how collectors are scheduled during learning, route to `../procedural-training/SKILL.md`.
- For `DummyVectorEnv`, `SubprocVectorEnv`, worker choices, async vectorization, EnvPool, or environment construction details, route to `../envs-and-vectorization/SKILL.md`.
- For offline datasets, offline-only algorithms, imitation-learning workflows, or specialized offline RL choices, route to `../offline-and-specialized-rl/SKILL.md`.

## Read These

- `references/api-reference.md` for object contracts, required keys, buffer variants, stats classes, and key signatures.
- `references/workflows.md` for practical recipes: shaping batches, adding/sampling buffers, collecting by step or episode, hooks, and validation.
- `references/troubleshooting.md` for common shape, null, NaN, malformed-buffer, and collector reset failures.
- `scripts/check_batch_buffer_collector.py` for a safe local smoke check of `Batch`, `ReplayBuffer`, and a minimal collector.

## Fast Checklist

1. Confirm installed imports with `python skills/tianshou/sub-skills/data-collection/scripts/check_batch_buffer_collector.py --help`.
2. Represent data in `Batch` with consistent first dimensions; nested dictionaries become nested `Batch` objects.
3. Add rollout data to buffers with `obs`, `act`, `rew`, `terminated`, `truncated`, `obs_next`, and `info`; `done` is inferred by the buffer.
4. Use `VectorReplayBuffer(total_size, buffer_num)` whenever collecting from multiple vectorized environments.
5. Call `collector.reset()` or use `collector.collect(..., reset_before_collect=True)` before the first collection.
6. Use `n_episode` rather than `n_step` when an episode-level hook writes fields for whole episodes.

## Smoke Check

Run the bundled script after install/import changes or when debugging a data path:

```bash
python skills/tianshou/sub-skills/data-collection/scripts/check_batch_buffer_collector.py
```

Use `--skip-collector` if only `Batch` and `ReplayBuffer` need validation or optional Gymnasium collection dependencies are unavailable.
