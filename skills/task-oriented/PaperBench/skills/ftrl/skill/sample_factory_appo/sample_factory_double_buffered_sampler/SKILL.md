---
name: sample_factory_double_buffered_sampler
description: Model Sample Factory double-buffered environment sampling and compare idle-time estimates against synchronous sampling.
---

# Sample Factory Double-Buffered Sampler

Use this skill when a recovery or implementation needs to preserve Sample Factory's sampler mechanism: split a rollout worker's environments into two alternating groups so policy inference for one group overlaps environment stepping for the other.

Do not use it as a wall-clock profiler; it is a deterministic mechanism model.

## Inputs
- Even number of environments per rollout worker `k`.
- Average inference time per action batch.
- Average environment step time per environment.
- Number of schedule iterations.

## Outputs
- Front/back environment groups.
- Alternating active and pending groups.
- Synchronous and double-buffered idle-time estimates.
- Idle-time reduction ratio.
- Minimum half-buffer size recommendation.

## Workflow
1. Validate that `k` is positive and even.
2. Split environment ids into two equal buffers.
3. Alternate active/pending buffers at every schedule step.
4. Estimate synchronous idle time as `max(0, inference_time - k * env_step_time)`.
5. Estimate double-buffered idle time as `max(0, inference_time - (k / 2) * env_step_time)`.
6. Treat a positive reduction ratio as mechanism evidence, not proof of real FPS.

## Validation
Run:

```bash
python scripts/double_buffered_sampler.py --envs-per-worker 4 --inference-time 3 --env-step-time 1 --iterations 4
python tests/test_double_buffered_sampler.py
```

## Limitations
The model assumes fixed timing and no queue contention. Real recovery should record whether it is a reduced/proxy experiment.
