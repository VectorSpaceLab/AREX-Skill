# Schedule troubleshooting

Use this file for schedule-specific failures. For checkpoint, dataset, mask, output-directory, or full inpainting errors, route to [inpainting-inference](../../inpainting-inference/). For shared Python/Torch/import/runtime setup problems, start with root [troubleshooting](../../../references/troubleshooting.md).

## Quick triage

1. Can the bundled helper show help?

   ```bash
   python scripts/render_schedule.py --help
   ```

2. Can it validate the current parameters without plotting?

   ```bash
   python scripts/render_schedule.py --config path/to/config.yml --no-plot --json-out schedule_summary.json
   ```

3. Does the JSON summary end with `"end": -1` and show the expected `reverse_denoise_steps` trend?
4. If validation passes but full inference fails, the schedule may not be the failure owner; route to [inpainting-inference](../../inpainting-inference/).

## Symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'matplotlib'` | Plotting requested but `matplotlib` is not installed. | Install `matplotlib`, or rerun with `--no-plot --json-out schedule_summary.json` when only counts are needed. |
| GUI/display error such as `cannot connect to display`, `TclError`, or backend errors | An interactive plotting backend is selected in a headless environment. | Use the bundled helper, which forces a non-interactive backend for plots. If using other plotting code, set `MPLBACKEND=Agg` before running. |
| `jump_length must be >= 1` or source `ValueError: range() arg 3 must not be zero` | `jump_length`, `jump2_length`, or `jump3_length` was set to zero. | Use positive integer jump lengths. A length of `1` is the smallest valid value. |
| `jump_n_sample must be >= 1` or a schedule has no useful jump repeats | Jump visit count is zero or disabled. | Use `jump_n_sample >= 1`; `1` disables the main jump family, while values above `1` add repeated jumps. |
| `n_steplength has no effect if n_sample=1` | The alternate simple helper was requested with `--mode simple --n_sample 1 --n_steplength > 1`. | Set `n_steplength: 1` or increase `n_sample`. This error belongs to the simple helper; normal RePaint inpainting uses `get_schedule_jump(...)`. |
| Assertion mentioning `times[-1]` or the final schedule value | A custom/manual schedule did not end at the expected `-1` sentinel, or arguments led to an invalid generated sequence. | Use the bundled helper rather than editing the list manually. Keep `t_T >= 1`; for simple mode keep `t_0 <= -1`. |
| Assertion mentioning adjacent times such as `(t_last, t_cur)` | Adjacent schedule entries differ by more than one. | Do not manually splice the schedule list. Use `jump_length` and `jump_n_sample` to change jumps while preserving one-step adjacent transitions. |
| Schedule plot is monotonic with no sawtooth jumps | Jumps are disabled or not eligible. | Check `jump_n_sample: 1`, `jump_length >= t_T`, or a very low `start_resampling`. Raise `jump_n_sample`, shorten `jump_length`, or increase `start_resampling` if resampling is intended. |
| Full inference is still slow after changing `jump_length` | `jump_length` changes jump width/frequency but is not the strongest runtime knob. | Compare JSON `reverse_denoise_steps`. Prefer reducing `t_T`, reducing `jump_n_sample`, or lowering `start_resampling` for speed. |
| Full inference fails with timestep/index errors after lowering `t_T` | `schedule_jump_params.t_T` and the effective respaced diffusion length may be inconsistent. | Review `timestep_respacing` in the full config. Repository examples keep `timestep_respacing: '250'` aligned with `t_T: 250`. Route full config execution to [inpainting-inference](../../inpainting-inference/). |
| User expects `diffusion_steps: 1000` to mean 1000 schedule entries | Confusion between base diffusion steps and the RePaint traversal schedule. | Explain that `diffusion_steps` builds the base beta schedule, `timestep_respacing` keeps a smaller effective set, and `t_T` controls the schedule-helper horizon. |
| Rendered schedule changes but full output quality gets worse | Resampling is a quality/harmony mechanism; speed reductions can reduce harmonization with known pixels. | Restore a larger `jump_n_sample`, increase `t_T`, or move `start_resampling` earlier. Final visual quality must be checked by the inpainting workflow. |

## Invalid schedule checklist

Before accepting a user's schedule edit, verify:

- `t_T` is a positive integer.
- `n_sample`, `jump_length`, `jump_n_sample`, `jump2_length`, `jump2_n_sample`, `jump3_length`, and `jump3_n_sample` are all integers `>= 1`.
- `start_resampling` is a non-negative integer when present.
- If using simple mode, `t_0 <= -1` and `n_steplength >= 1`.
- If using simple mode with `n_steplength > 1`, `n_sample > 1`.
- For real RePaint configs, `schedule_jump_params.t_T` is consistent with `timestep_respacing`.

## Recovery commands

Render counts only:

```bash
python scripts/render_schedule.py --config path/to/config.yml --no-plot --json-out schedule_summary.json
```

Render an explicit known-good baseline:

```bash
python scripts/render_schedule.py --t_T 250 --n_sample 1 --jump_length 10 --jump_n_sample 10 --out schedule_baseline.png
```

Test invalid simple-helper behavior intentionally:

```bash
python scripts/render_schedule.py --mode simple --t_T 20 --n_sample 1 --n_steplength 3 --no-plot
```

Expected: non-zero exit with `n_steplength has no effect if n_sample=1`.
