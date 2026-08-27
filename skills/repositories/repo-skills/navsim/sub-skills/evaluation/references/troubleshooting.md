# Evaluation troubleshooting

Use this reference as a stop-and-recover table. Do not turn a warning into a
score by deleting rows, suppressing exceptions, or reusing an unrelated cache.

## Install, import, and optional backend dependencies

| Symptom | Likely cause | Recovery / stop condition |
|---|---|---|
| `ModuleNotFoundError: navsim` | Package is not installed or the active interpreter differs from the one used for setup | Activate the intended Python 3.9+ environment, run an import smoke and `pip check`, then invoke runners as `python -m navsim...`; stop if import still fails |
| Missing `nuplan` or Hydra/OmegaConf symbols | nuPlan devkit or its compatible dependency set is absent/mismatched | Install the repository's compatible package set in the active environment; do not mix arbitrary nuPlan versions; rerun import checks |
| CUDA initialization error or no GPU | Torch/CUDA wheel and host driver do not agree, or GPU is unavailable | Verify `torch.cuda.is_available()` and the selected backend. Use CPU only for a supported smoke/config inspection; do not claim benchmark parity after a backend fallback |
| Ray import/worker startup failure | Ray is unavailable or cluster settings are invalid | Use `worker=sequential` or `worker=single_machine_thread_pool` for a bounded diagnostic; for metric caching never enable Ray built-in distributed mode |
| IDM fails while log replay imports | Reactive IDM additionally needs map access and compatible nuPlan map APIs | Validate `NUPLAN_MAPS_ROOT`, map version/map name, and nuPlan compatibility. Switch to log replay only for an explicitly different protocol, not as a silent repair |
| Constant-velocity traffic works but score is implausible | It is a debugging-only background policy and does not model interactions | Label the run as debugging and repeat with the intended policy before drawing conclusions |

## Data, maps, cache, and split validation

| Symptom | Likely cause | Recovery / stop condition |
|---|---|---|
| Scene loader finds zero tokens | `OPENSCENE_DATA_ROOT`, log path, split, or scene filter is wrong | Inspect resolved `navsim_log_path` and `train_test_split`; ensure the selected log annotations exist; stop before workers start |
| Map lookup/key error during caching or IDM | `NUPLAN_MAPS_ROOT` is unset, points at the wrong map release, or the cache's map metadata differs | Set and validate the map root/version; rebuild affected cache entries; do not substitute a map from another release |
| Missing metric cache token warnings | Cache was generated for another split/filter or caching was incomplete | Compare scene-loader tokens and cache metadata. Cache the exact split with the same roots and wait for zero unexplained failures |
| Unused metric cache token warnings | Cache is broader than the current split/filter | This is usually safe for a deliberate shared cache but must be recorded; for reproducibility prefer a split-specific cache. Do not infer that every cache token was evaluated |
| Standard run needs synthetic files | A two-stage split was selected without synthetic sensor/scenes roots | Provide both synthetic roots for the selected split or switch to a genuine log-only split; do not create empty placeholders |
| Cache exists but scoring fails to deserialize | Incomplete/corrupt compressed pickle or incompatible package objects | Check the cache metadata and file integrity; rebuild with `force_feature_computation=true` in a new/isolated cache path |
| Cache run reports failures but exits | Per-scenario cache processing can continue after failures | Treat the failure count as a failed precondition. Inspect the first traceback, repair data/map/config, then recache affected data |
| Cache and scorer sample different horizons | Cache proposal sampling, scorer/simulator sampling, and agent output declarations diverge | Align `num_poses`, interval, and 4 s horizon; rebuild cache when the cache sampling changes; stop on any sampler assertion |

## Configuration and CLI/API misuse

| Symptom | Likely cause | Recovery / stop condition |
|---|---|---|
| Hydra says an override is not found | Wrong group/key spelling or a config group was used as a scalar | Use exact names such as `train_test_split=...`, `agent=...`, `worker=...`, `scorer.config...`; inspect resolved config before running |
| `experiment_name` or `submission_file_path` is missing | Required value remains `???` | Supply it explicitly; never let a placeholder resolve to a prior experiment |
| `simulator.proposal_sampling == scorer.proposal_sampling` assertion | Custom config instantiated different sampling objects | Use the shared `proposal_sampling` composition or set both nested values identically; stop rather than removing the assertion |
| `Trajectory` assertion about dimensions or number of poses | Agent returned global coordinates, wrong `(N,3)` shape, or declared sampling not equal to rows | Return local rear-axle `(x,y,heading)` poses and an accurate `TrajectorySampling`; route agent implementation to the agents skill |
| `IndexError`/bad interpolation near trajectory end | Output is shorter than the configured horizon or has irregular declared times | Produce the full horizon at a consistent sampling and rerun a synthetic trajectory-contract check before evaluation |
| `TypeError` from policy constructor | A custom policy was instantiated without the future trajectory sampling argument | Match the policy constructor contract and ensure its output length is `num_poses + 1` including the current frame where required |
| `agent.requires_scene` path fails | The configured agent expects privileged Scene input but the selected loader/input does not provide it | Use an agent whose sensor/input contract matches the evaluation route, or fix the agent configuration; do not grant privileged data silently |
| Submission scorer rejects pickle | Missing `first_stage_predictions`/`second_stage_predictions`, wrong mapping nesting, or more than one seed | Validate the local pickle schema; current scorer supports exactly one seed per stage and exact token/cache coverage |
| Output CSV lacks final score | Scoring failed before aggregation or caller read `pdm_score` instead of final `score` | Inspect logs, `valid`, summary rows, and aggregation fallback; rerun only after the root cause is fixed |

## Workflow-specific failures

### Metric caching

- `metric_cache_path` must not be null. Confirm it is writable before starting.
- The cache builder uses map-relative preprocessing and interpolated detection
  tracks; a cache generated without maps is not a partial substitute.
- `force_feature_computation=true` overwrites existing entries. Use a new
  diagnostic cache or record the overwrite decision.
- A cache metadata file with only a subset of the selected tokens is not a
  successful cache, even if the process exit code is zero.

### One-stage scoring

- Select `traffic_agents=non_reactive` or `reactive` explicitly when comparing
  policies. The default is non-reactive; a policy change changes metric inputs.
- The one-stage runner infers adjacent original frames for EC. Sparse or
  misordered timestamps can leave EC undefined; inspect the adjacency mapping
  and the `two_frame_extended_comfort` column.
- A failed agent produces an empty/default result row with `valid=false`.
  Resolve the first agent traceback before interpreting averages.

### Two-stage scoring and submission scoring

- Stage-two mappings are configuration data. If no mappings match loaded tokens,
  combined aggregation cannot represent the intended pseudo closed loop.
- Gaussian endpoint weights can underflow for distant follow-up scenes; the
  implementation falls back to uniform weights. This is a diagnostic signal,
  not proof that the mapping is correct.
- Missing/unused cache token warnings, failed stage rows, NaN EC, or an invalid
  pseudo-closed-loop flag are stop conditions for a claimed two-stage result.
- The aggregator expects adjacent-frame intervals below 0.55 s and aligns
  overlaps by the configured sampling interval. A sampling mismatch can make
  the comfort overlap invalid even when individual stage scores exist.
- `run_pdm_score_from_submission` currently rejects multi-seed pickles and uses
  reactive traffic for both stages. Do not infer support for multiple seeds from
  a pickle that happens to contain them.

## Synthetic difficult cases

Use data-free fixtures for verification:

1. **Cache split mismatch:** mock a scene-token set for `navhard_two_stage` and
   a cache-token set for `navtest`, then assert that the diagnostic reports
   missing and unused tokens and refuses a ready-to-run status. Do not touch a
   real cache.
2. **Trajectory sampling mismatch:** construct a synthetic `Trajectory` with
   eight poses declared at 0.5 s and a scorer/simulator request of 40 poses at
   0.1 s. Assert that the contract check flags the mismatch or insufficient
   horizon rather than silently labeling the result valid.
