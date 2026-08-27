# RePaint schedule reference

This reference explains the schedule logic owned by this sub-skill. It is distilled from the repository README, `guided_diffusion/scheduler.py`, `guided_diffusion/gaussian_diffusion.py`, and the example YAML configs.

## What the schedule is

RePaint inpainting uses a list of diffusion times rather than a plain monotonic countdown. The list is generated from `schedule_jump_params` and then consumed as adjacent time pairs in the sampling loop.

For a RePaint config, the relevant block is:

```yaml
timestep_respacing: '250'
schedule_jump_params:
  t_T: 250
  n_sample: 1
  jump_length: 10
  jump_n_sample: 10
  # optional helper defaults if omitted:
  # jump2_length: 1
  # jump2_n_sample: 1
  # jump3_length: 1
  # jump3_n_sample: 1
  # start_resampling: 100000000
```

All example configs in this repository use `t_T: 250`, `n_sample: 1`, `jump_length: 10`, and `jump_n_sample: 10`. The optional `start_resampling` key is omitted in those configs, so the helper default makes resampling eligible immediately.

## Schedule entries and sampler behavior

`get_schedule_jump(...)` returns a list named `ts` in the source. For `t_T=250`, the first entries look like a high-to-low countdown and the list ends with `-1` as a sentinel. A verified default schedule begins at `249`, ends at `-1`, and contains both downward and upward transitions.

The diffusion loop zips the schedule into adjacent pairs:

```text
(t_last, t_cur) for each pair in zip(times[:-1], times[1:])
```

Then it applies this rule:

- If `t_cur < t_last`, the sampler performs a reverse denoise step with `p_sample(...)`. This is the expensive model-call path and yields an intermediate output.
- Otherwise, the sampler performs an undo/forward diffusion step with `undo(...)`. This adds noise to move from a less noisy state back to a more noisy state before denoising again.

The final `-1` entry is a sentinel used to make the last pair `0 -> -1`; the model is called at `t=0`, not at `t=-1`.

## Important distinction: diffusion steps, respacing, jumps

Do not collapse these terms:

- `diffusion_steps` configures the base beta schedule used to build the diffusion process. The example configs set it to `1000`.
- `timestep_respacing` selects the effective number of retained diffusion timesteps. The example configs set it to `'250'`.
- `schedule_jump_params.t_T` controls the schedule-helper horizon. It should match the effective respaced process for normal RePaint configs; the examples set `t_T: 250`.
- `jump_length` and `jump_n_sample` add resampling jumps inside that horizon. They do not change the trained model checkpoint.

When reducing `t_T` for speed, also review `timestep_respacing`; keeping `timestep_respacing: '250'` while using a much smaller `t_T` changes only the traversal schedule, while setting both to the same smaller value changes the effective sampler horizon more consistently.

## Parameter guide

| Parameter | Source role | Practical range | Tuning effect |
| --- | --- | --- | --- |
| `t_T` | Horizon for the jump schedule. `get_schedule_jump` starts at `t_T - 1` and ends at `-1`. | Positive integer; examples use `250`. Keep no larger than the effective respaced diffusion length. | Main speed knob. Lower values reduce the base countdown and usually reduce model calls, but remove more noise per retained step and may lower quality. |
| `n_sample` | One-step local resampling count at eligible timesteps before jump families are considered. | Integer `>= 1`; examples use `1`. | Values above `1` add short up/down resampling at many timesteps. Keep at `1` unless intentionally experimenting, because it can expand the loop substantially. |
| `jump_length` | Number of forward/undo time increments in the main jump family. | Integer `>= 1`; examples use `10`. If `jump_length >= t_T`, the main jump family has no jump locations. | Changes the temporal width and frequency of resampling jumps. It is not as direct a runtime knob as `t_T` or `jump_n_sample`; compare helper summaries before assuming it speeds up inference. |
| `jump_n_sample` | Number of visits per main jump location; the source stores `jump_n_sample - 1` remaining jumps. | Integer `>= 1`; examples use `10`. | Main resampling-quality knob. Lower values reduce repeated denoising/undo cycles and speed inference; `1` disables the main jump family. Higher values can improve harmony between known and generated regions but costs more steps. |
| `jump2_length`, `jump2_n_sample` | Optional nested jump family reset after a main jump. | Integers `>= 1`; source defaults are `1` and `1`, making it inert. | Advanced experimentation only. Increasing `jump2_n_sample` adds a second jump family. |
| `jump3_length`, `jump3_n_sample` | Optional third nested jump family reset after jump2 or main jumps. | Integers `>= 1`; source defaults are `1` and `1`, making it inert. | Advanced experimentation only. Increasing `jump3_n_sample` adds another nested jump family. |
| `start_resampling` | Threshold that delays resampling until the reverse process has reached a lower diffusion time. | Non-negative integer. Omitted source default is a very large value, effectively allowing resampling from the beginning. For `t_T=250`, `250` also makes all normal locations eligible. | Speed/quality knob from the README. Smaller values skip early high-noise resampling and begin jumps only once `t <= start_resampling` (or `t <= start_resampling - jump_length` for the main jump family). |

## Interpreting summary counts

The bundled helper reports:

- `entries`: number of schedule time entries.
- `transitions`: number of adjacent pairs consumed by the sampler.
- `reverse_denoise_steps`: count of downward transitions. These correspond to model-call denoising steps in the sampling loop.
- `forward_undo_steps`: count of upward transitions. These call the undo/forward-noising path and create the oscillating schedule.
- `start`, `end`, `min`, `max`: quick validation of the produced schedule.

For the repository's default schedule parameters (`t_T=250`, `n_sample=1`, `jump_length=10`, `jump_n_sample=10`), live inspection produced 4,571 entries, 4,570 transitions, 2,410 reverse denoise steps, and 2,160 forward undo steps. Use those counts as a baseline when proposing speed changes.

## Speed and quality tradeoffs

The README gives three practical ways to speed up inference without changing the model:

1. Reduce `t_T`.
2. Reduce `jump_n_sample`.
3. Delay resampling by setting `start_resampling`.

Use them in that order for ordinary requests. Always render and compare schedules before running full inpainting. The best schedule depends on masks and images, so this sub-skill can explain expected tradeoffs and validate schedule shape, but final image quality must be checked through the inpainting workflow.

## When to route away

If the user asks where to put images, masks, checkpoints, output directories, or how to run the full inpainting workflow, route to [inpainting-inference](../../inpainting-inference/). If the failure is a general import, Python, Torch, or install problem rather than a schedule-specific argument or plot problem, use root [troubleshooting](../../../references/troubleshooting.md).
