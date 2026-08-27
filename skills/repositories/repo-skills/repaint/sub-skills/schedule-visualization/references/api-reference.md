# Schedule API and helper reference

This file records the schedule APIs and bundled helper contract for the schedule-visualization sub-skill. It is self-contained so future agents do not need to reopen the source repository.

## Source schedule helpers

### `get_schedule_jump(...)`

Live-inspected signature:

```python
get_schedule_jump(
    t_T,
    n_sample,
    jump_length,
    jump_n_sample,
    jump2_length=1,
    jump2_n_sample=1,
    jump3_length=1,
    jump3_n_sample=1,
    start_resampling=100000000,
)
```

Behavior:

- Returns a Python `list[int]` of visited diffusion times.
- For the example `t_T=250`, the list starts at `249` and ends at `-1`.
- Adjacent entries differ by exactly `1` according to the source `_check_times(...)` assertion.
- Downward transitions are reverse denoise steps in `GaussianDiffusion.p_sample_loop_progressive(...)`.
- Upward transitions are undo/forward-noising steps in the same loop.
- `jump_n_sample - 1` is stored internally as the number of remaining jumps for each jump location.
- `start_resampling` gates the local resampling and jump families; lower values delay or disable parts of the resampling schedule.

The inpainting loop calls this helper as:

```python
times = get_schedule_jump(**conf.schedule_jump_params)
time_pairs = zip(times[:-1], times[1:])
```

Then it routes each pair by comparing `t_cur` with `t_last`.

### `get_schedule(...)`

Live-inspected source signature:

```python
get_schedule(t_T, t_0, n_sample, n_steplength, debug=0)
```

Behavior:

- This is an alternate/simple schedule helper, not the helper called by the RePaint inpainting loop.
- It returns a Python `list[int]` and validates it with `_check_times(...)`.
- If `n_steplength > 1` while `n_sample == 1`, it raises:

```text
RuntimeError: n_steplength has no effect if n_sample=1
```

Use the bundled helper's `--mode simple` only for source-level schedule questions or synthetic usability checks involving `n_steplength`.

### `_check_times(...)` invariants

The source validation checks these invariants:

- The first pair must go downward: `times[0] > times[1]`.
- The last entry must be `-1`.
- Every adjacent pair must differ by exactly `1`.
- Every time value must be within the supplied lower/upper bounds.

The bundled helper adds friendlier pre-validation for common invalid CLI values before these assertions are reached.

## Bundled `render_schedule.py` CLI

Script path from this sub-skill directory:

```bash
python scripts/render_schedule.py --help
```

Primary options:

| Option | Default | Meaning |
| --- | --- | --- |
| `--mode {jump,simple}` | `jump` | Use RePaint's jump schedule or the alternate simple helper. |
| `--config PATH` | none | Read a RePaint-style YAML config and extract `schedule_jump_params`. Only valid with jump mode. |
| `--t_T INT` | `250` | Schedule horizon. For jump mode, the first schedule time is `t_T - 1`. |
| `--n_sample INT` | `1` | Local resampling count. |
| `--jump_length INT` | `10` | Main jump length for jump mode. |
| `--jump_n_sample INT` | `10` | Main jump visit count for jump mode. |
| `--jump2_length INT`, `--jump2_n_sample INT` | `1`, `1` | Optional second jump family. |
| `--jump3_length INT`, `--jump3_n_sample INT` | `1`, `1` | Optional third jump family. |
| `--start_resampling INT` | `100000000` | Threshold controlling when resampling becomes eligible. |
| `--t_0 INT` | `-1` | Lower bound for simple mode. Keep `<= -1` because the schedule ends with `-1`. |
| `--n_steplength INT` | `1` | Step length for simple mode. |
| `--out PATH` | auto-generated PNG name | Plot output path. Parent directories are created. |
| `--json-out PATH` | plot stem with `.json` | Summary JSON output path. Parent directories are created. |
| `--csv-out PATH` | none | Optional CSV dump with `index,t` rows. |
| `--no-plot` | false | Validate and summarize without importing `matplotlib`. |
| `--no-json` | false | Skip JSON output. |
| `--preview-count INT` | `12` | Number of first/last times included in the printed and JSON previews. |
| `--print-times` | false | Print the full schedule list as JSON to stdout. Use carefully for large schedules. |

Default output names:

- Jump mode: `schedule_jump_tT250_jl10_jn10.png` and `schedule_jump_tT250_jl10_jn10.json` for the default parameters.
- Simple mode: `schedule_simple_tT250_ns1_sl1.png` and `schedule_simple_tT250_ns1_sl1.json` for the default simple parameters.
- If you pass `--out custom.png` and omit `--json-out`, the helper writes `custom.json` next to the plot.

Summary fields:

| Field | Meaning |
| --- | --- |
| `parameters` | Effective parameters after applying config values and CLI overrides. |
| `entries` | Number of entries in the schedule time list. |
| `transitions` | Number of adjacent pairs consumed by the sampler. |
| `reverse_denoise_steps` | Count of downward transitions; for jump mode these are model-call denoise steps. |
| `forward_undo_steps` | Count of upward transitions; these are undo/forward-noising steps. |
| `start`, `end`, `min`, `max` | Shape sanity checks. Expected jump-mode `end` is `-1`. |
| `preview.first`, `preview.last` | First and last schedule entries for fast inspection. |
| `notes` | Non-fatal warnings such as disabled jump families or delayed resampling. |

## Source-to-bundled-helper mapping

| Source artifact | Bundled artifact | Change made | Why |
| --- | --- | --- | --- |
| `guided_diffusion/scheduler.py` | `scripts/render_schedule.py` | Copied/adapted schedule generation logic into a self-contained CLI helper. | Future agents can render schedules without relying on the original checkout. |
| Source `_plot_times(...)` / `get_schedule_jump_test(...)` | `scripts/render_schedule.py` plotting path | Replaced interactive `plt.show()` and fixed `./schedule.png` output with explicit headless PNG output. | Safe in non-GUI agent environments and predictable for verification. |
| Source helper assertions | Friendly CLI validation plus preserved invariant checks | Added parameter-range checks and clearer error messages before running the schedule. | Better usability for invalid schedule combinations. |

The helper intentionally does not run model inference, load checkpoints, inspect datasets, or import the RePaint package. Those tasks belong to [inpainting-inference](../../inpainting-inference/) or root troubleshooting.
