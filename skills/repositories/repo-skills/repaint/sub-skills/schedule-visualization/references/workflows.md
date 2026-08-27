# Schedule visualization workflows

Use these workflows to render schedules, compare schedule variants, and prepare schedule edits before handing a full inpainting run to the inference sub-skill.

Prefer running the helper in a scratch directory or passing explicit `--out` / `--json-out` paths so the generated plot and summary stay outside the skill tree. If you are operating from the generated RePaint skill root instead, prefix script paths with `sub-skills/schedule-visualization/`.

## 1. Render the repository-default schedule

```bash
python scripts/render_schedule.py
```

Default behavior:

- Uses `mode=jump`.
- Uses `t_T=250`, `n_sample=1`, `jump_length=10`, `jump_n_sample=10`.
- Uses source defaults for optional `jump2_*`, `jump3_*`, and `start_resampling`.
- Writes `schedule_jump_tT250_jl10_jn10.png` and `schedule_jump_tT250_jl10_jn10.json` in the current directory unless you override them with explicit output paths.
- Prints a summary with transition counts and schedule previews.

Expected baseline summary for these parameters: 4,570 transitions, 2,410 reverse denoise steps, and 2,160 forward undo steps.

## 2. Render from a RePaint-style config file

If a user has a YAML config with a `schedule_jump_params` block, render it directly:

```bash
python scripts/render_schedule.py --config path/to/config.yml --out current_schedule.png
```

The helper reads only `schedule_jump_params`. It does not validate datasets, masks, checkpoints, or run inpainting. For those config and asset questions, route to [inpainting-inference](../../inpainting-inference/).

Useful no-GUI/no-plot variant:

```bash
python scripts/render_schedule.py --config path/to/config.yml --no-plot --json-out current_schedule.json
```

Use this when the user only needs schedule counts or when `matplotlib` is unavailable.

## 3. Compare two or more schedule candidates

Render each candidate to JSON and compare `reverse_denoise_steps` first; that count is the closest schedule-level proxy for model-call cost.

```bash
python scripts/render_schedule.py \
  --t_T 250 --n_sample 1 --jump_length 10 --jump_n_sample 10 \
  --no-plot --json-out schedule_250_jn10.json

python scripts/render_schedule.py \
  --t_T 250 --n_sample 1 --jump_length 10 --jump_n_sample 5 \
  --no-plot --json-out schedule_250_jn5.json

python scripts/render_schedule.py \
  --t_T 150 --n_sample 1 --jump_length 10 --jump_n_sample 5 \
  --start_resampling 100 \
  --no-plot --json-out schedule_150_jn5_sr100.json
```

Decision rule:

1. If `reverse_denoise_steps` barely changes, the full run may not speed up much.
2. If `forward_undo_steps` drops but `reverse_denoise_steps` remains high, the plot is less oscillatory but model-call cost may still be high.
3. If both counts drop sharply, expect faster inference but check image quality through the inpainting workflow.

## 4. Answer: "reduce inference time without changing the model"

Use this sequence:

1. Render the current config and record `reverse_denoise_steps`.
2. Try reducing `jump_n_sample` first, for example `10 -> 5 -> 1`. Setting `jump_n_sample: 1` disables the main jump family.
3. If more speed is needed, reduce `t_T`, for example `250 -> 150` or `250 -> 100`. In the full config, review `timestep_respacing` at the same time; the repository examples keep `timestep_respacing: '250'` aligned with `schedule_jump_params.t_T: 250`.
4. If the user wants to preserve late-stage harmonization but skip early resampling, set `start_resampling` to a smaller time such as `100` or `50` and compare counts.
5. Keep `n_sample: 1` unless there is a deliberate reason to add local one-step resampling.
6. Do not promise equivalent quality. Explain that resampling is intended to improve harmony between generated and known regions, so speed cuts can reduce harmonization.

Example faster candidate to inspect:

```bash
python scripts/render_schedule.py \
  --t_T 150 \
  --n_sample 1 \
  --jump_length 10 \
  --jump_n_sample 5 \
  --start_resampling 100 \
  --out faster_candidate.png \
  --json-out faster_candidate.json
```

After choosing a candidate, route the user to [inpainting-inference](../../inpainting-inference/) to edit and run the full RePaint config.

## 5. Explain jump schedule shape to a user

Use the plot plus these talking points:

- A monotonic downward line means plain reverse diffusion.
- Upward segments are RePaint undo/forward-noising jumps.
- Repeated sawtooth patterns indicate resampling: the sampler revisits nearby diffusion times to harmonize generated content with known pixels.
- Lower `t` means later, less noisy reverse-diffusion stages.
- Setting `start_resampling` lower delays the sawtooth pattern until later in the reverse process.

## 6. Validate a suspect schedule without plotting

Use `--no-plot` to run validation and get counts:

```bash
python scripts/render_schedule.py \
  --t_T 250 \
  --n_sample 1 \
  --jump_length 0 \
  --jump_n_sample 10 \
  --no-plot
```

Expected signal: the helper exits non-zero and reports that `jump_length` must be `>= 1`. Fix parameter ranges before changing model or asset settings.

## 7. Inspect the alternate simple helper

The RePaint inpainting loop uses `get_schedule_jump(...)`, but the source also contains a simpler `get_schedule(...)` helper with `n_steplength`. The bundled renderer exposes it for debugging source-level schedule questions:

```bash
python scripts/render_schedule.py \
  --mode simple \
  --t_T 20 \
  --t_0 -1 \
  --n_sample 2 \
  --n_steplength 3 \
  --out simple_schedule.png
```

Invalid example:

```bash
python scripts/render_schedule.py --mode simple --t_T 20 --n_sample 1 --n_steplength 3 --no-plot
```

Expected signal: `n_steplength has no effect if n_sample=1`. Either set `n_steplength: 1` or increase `n_sample`.

## Validation before handoff

Before sending a schedule edit to the inpainting workflow:

- The helper exits with code `0`.
- The summary has `end: -1` and no validation notes marked as errors.
- `t_T` is aligned with the intended `timestep_respacing` in the full config.
- `reverse_denoise_steps` reflects the intended speed/quality tradeoff.
- Any data, checkpoint, mask, output, or full-run question has been routed to [inpainting-inference](../../inpainting-inference/).
