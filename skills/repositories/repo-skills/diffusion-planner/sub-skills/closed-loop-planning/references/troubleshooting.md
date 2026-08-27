# Closed-loop troubleshooting

## Triage order

Classify the failure before changing the model:

1. **Command/parser/import phase:** Python import, script path, Hydra group,
   missing override, or invalid JSON. Re-run the bundled helper and a direct
   import in the prepared environment.
2. **Planner initialization phase:** checkpoint deserialization, EMA/model
   wrapper, `module.` prefix, architecture, device, or normalizer mismatch.
3. **Scenario-builder phase:** DB/map roots, map version, scenario mapping,
   filter tokens, split/builder pairing, or external nuPlan data.
4. **Worker/simulation phase:** Ray resources, GPU fraction, process visibility,
   reactive-agent setup, observation history, or simulation output.
5. **Visualization phase:** missing `.nuboard`, incorrect result path, or
   notebook/Hydra environment.

Do not diagnose a blocked external dataset as a planner code regression.

## Common symptoms and actions

### `Could not load 'planner=diffusion_planner'` or `scenario_filter=...`

The package config groups are not on Hydra's search path. Include the package
entries (not filesystem paths):

```text
pkg://diffusion_planner.config.scenario_filter
pkg://diffusion_planner.config
pkg://nuplan.planning.script.config.common
pkg://nuplan.planning.script.experiments
```

Also confirm the installed checkout/package exposes the `diffusion_planner`
package and that the command is run with the intended environment. Use
`HYDRA_FULL_ERROR=1` to retain the nested exception.

### `FileNotFoundError` for `args.json` or `model.pth`

The planner paths are resolved by the process running Hydra, not by this skill.
Use absolute paths while debugging. Confirm both files are from the same
release and that the current user can read them. Run:

```bash
python scripts/check_closed_loop_config.py \
  --args-file "$ARGS_FILE" --checkpoint "$CKPT_FILE" \
  --split "$SPLIT" --challenge "$CHALLENGE" --builder auto
```

No real artifacts are included in this repository, so a missing file here is
an expected external prerequisite until the user supplies one.

### `KeyError: 'ema_state_dict'`, missing/unexpected state-dict keys

`enable_ema=true` expects `ema_state_dict`. Set `enable_ema=false` only when
the artifact is a non-EMA checkpoint, and check whether it is wrapped under
`model`. The loader strips a leading `module.` from keys but does not repair
arbitrary prefixes or architecture differences. Use the matching `args.json`
and checkpoint release; do not fix this by ignoring missing keys.

### `Config` fails while opening or normalizing JSON

`Config` reads the file immediately and expects usable `state_normalizer` and
`observation_normalizer` mappings containing means/stds. A training manifest,
empty JSON object, or hand-written partial config is not an inference config.
The helper checks required architecture keys and normalizer shapes before a
run, but only the actual `Config`/model load proves tensor compatibility.

### `AssertionError: device cuda ...` or CUDA unavailable

Use `device=cpu` only for a limited import/construction investigation. The
repository's released YAML defaults to CUDA, and full diffusion inference may
be too slow or unsupported on CPU. Check the selected visible devices, torch
build, driver, and `--check-cuda`; do not claim native simulation from a CPU
parser smoke.

### Scenario builder opens no scenarios

Check all of the following:

- `NUPLAN_DATA_ROOT` contains the database layout expected by the selected
  `nuplan` or `nuplan_challenge` config.
- `NUPLAN_MAPS_ROOT` contains the configured map database/version.
- the filter's explicit tokens belong to the selected DB and use the expected
  token representation;
- `log_names`, `map_names`, scenario types, timestamp threshold, and invalid
  goal settings are not filtering everything;
- `val14-collision` was not accidentally treated as the ordinary `val14`
  split, and its builder was chosen deliberately.

`test14-random` is bounded at 20 scenarios per listed type in this checkout;
`test14-hard` uses explicit hard-case tokens and no per-type cap. `val14` uses
its explicit token/type list and validation log split. These settings are not
interchangeable.

### Ray hangs, oversubscribes, or workers fail before planning

Lower `worker.threads_per_node` and
`number_of_gpus_allocated_per_simulation`, use a single visible GPU, or use a
sequential/single-machine worker for a tiny debugging run if supported by the
nuPlan config. `distributed_mode='SINGLE_NODE'` does not mean every resource
value is safe. Inspect Ray worker logs under the experiment output. A worker
failure can hide a planner import or checkpoint exception; preserve the first
nested traceback.

### Planner computes a trajectory but later fails in transform/output

Check that `future_trajectory_sampling.num_poses` and `time_horizon` agree with
the checkpoint's `future_len` and that the model output is the expected
`prediction` tensor with final channels representing x/y and heading-vector
components. The adapter currently selects `[0, 0]`; an unexpected candidate
layout or wrong batch shape is not silently handled.

### NuBoard shows no run

Confirm the simulation completed and wrote `.nuboard` metadata under the result
folder. Set the notebook's `RESULT_FOLDER` to the experiment output, replace
its relative devkit config path with the installed NuBoard config location,
and select the same scenario builder used for simulation. NuBoard cannot
visualize a path that contains only logs without serialized simulation output.
Notebook execution is optional and is not an inference test.

## Evidence and limits

The inspection environment successfully imported the planner/model/config
modules and nuPlan 1.2.2 `run_simulation`, `NuPlanScenarioBuilder`, and
`TrajectorySampling`. It had no real dataset, maps, or checkpoint, so builder
enumeration, `initialize()` against trained weights, Ray execution, trajectory
quality, and NuBoard loading remain unverified external workflows.
