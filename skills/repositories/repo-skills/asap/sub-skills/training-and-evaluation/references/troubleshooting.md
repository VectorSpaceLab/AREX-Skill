# Training and evaluation troubleshooting

Fix failures in this order: command shape, config selection, repository-relative paths, backend packages, checkpoint/config loading, and finally runtime evaluation quirks.

## 1. Wrong invocation style or working directory

### Symptom

```text
ModuleNotFoundError: No module named 'utils.config_utils'
```

or

```text
ModuleNotFoundError: No module named 'humanoidverse'
```

### Cause

The entry points are written as scripts that assume the repository root and the `humanoidverse/` script directory layout. `train_agent.py` imports `utils.config_utils` relative to the script directory, so `python -m humanoidverse.train_agent` is the wrong form here.

### Recovery

1. Run from the ASAP repository root.
2. Use script form, not module form:

   ```bash
   python humanoidverse/train_agent.py --help
   python humanoidverse/eval_agent.py --help
   ```

3. If you need a command builder, run the bundled safe builder from the repo root:

   ```bash
   python sub-skills/training-and-evaluation/scripts/build_training_command.py --repo-root <asap-checkout> --workflow motion-tracking --cfg-job
   ```

## 2. Hydra override errors

### Symptom

```text
Could not override 'headless'.
To append to your config use +headless=True
Key 'headless' is not in struct
```

### Cause

`base_eval.yaml` does not define `headless` or `num_envs`. Evaluation often needs these values only after the checkpoint config is merged back in.

### Recovery

- For eval-only overrides, use `+headless=True` and `+num_envs=1`.
- For training, use plain `headless=True` or `headless=False` because `base.yaml` already defines the key.
- If Hydra group names are wrong, consult `python humanoidverse/train_agent.py --help` or this skill's [`references/api-reference.md`](api-reference.md).

### Symptom

```text
Could not override 'simulator'
```

### Cause

The `+simulator=<choice>` group must match a config file under `humanoidverse/config/simulator/`.

### Recovery

Use one of the verified choices:

- `+simulator=isaacgym`
- `+simulator=isaacsim`
- `+simulator=genesis`
- `+simulator=mujoco`

## 3. Backend package missing

### Symptom

```text
ModuleNotFoundError: No module named 'isaacgym'
```

or

```text
ModuleNotFoundError: No module named 'omni'
```

or

```text
ModuleNotFoundError: No module named 'genesis'
```

or

```text
ModuleNotFoundError: No module named 'mujoco'
```

### Cause

The Hydra config selected a simulator whose Python package is not installed in the current environment.

### Recovery

1. Match the package to the backend:
   - IsaacGym: install IsaacGym Preview 4 Python API.
   - IsaacSim: install IsaacSim/IsaacLab and make sure `omni.isaac.lab` imports.
   - Genesis: install `genesis-world`.
   - MuJoCo: install `mujoco` and only use it where the repo has been adapted for it.
2. Re-run the help command or composition-only check before a long train.
3. If you only need the command text, use the builder and stop before execution.

## 4. Checkpoint/config loading failures in `eval_agent.py`

### Symptom

```text
Could not find config path: <...>/config.yaml
```

or the evaluation run starts with missing fields that should have come from the training config.

### Cause

`eval_agent.py` tries to load the training `config.yaml` next to the checkpoint, then one directory above it. If neither exists, the script falls back to the bare eval config, which may not carry the observation schema or simulator settings that the checkpoint expects.

### Recovery

1. Keep `config.yaml` next to every saved checkpoint directory.
2. If you only have a detached `.pt`, either reconstruct the training config from the same Hydra overrides or copy the matching `config.yaml` into the checkpoint directory.
3. Re-run with `+checkpoint=<path>` and, when needed, the matching `+exp`, `+robot`, `+obs`, `+rewards`, `+terrain`, and `+simulator` groups.

### Special case: PPODeltaA

`PPODeltaA` needs `algo.config.policy_checkpoint` to find a second config for the frozen policy. If that config is missing, `policy_config` is never constructed and the closed-loop finetune path can fail during initialization.

Recovery:

- Keep the frozen policy checkpoint and its `config.yaml` together.
- Pass the delta-policy path via `algo.config.policy_checkpoint=...` and the finetuned policy via `checkpoint=...`.

## 5. Motion file mismatch

### Symptom

```text
KeyError: 'action'
```

or the delta-action trainer runs but the loaded motion library has no open-loop action.

### Cause

`DeltaA_OpenLoop` and the motion library expect the motion file to contain an `action` key when the workflow needs motion-file actions. Standard retargeted motion files usually do not contain this key.

### Recovery

1. Use a motion file that already includes `action` arrays for open-loop delta-action training.
2. If you are only doing motion tracking, the standard retargeted `.pkl` is fine.
3. For action-bearing evaluation dumps, use `+opt=record` with `env.config.save_motion=True`.

## 6. Evaluation export behavior surprises

### Symptom

You expected an export-only run, but `eval_agent.py` keeps running.

### Cause

The script always sets `EXPORT_ONNX=True` and then calls `algo.evaluate_policy()`, which loops forever.

### Recovery

1. Watch for the export log:

   ```text
   Exported policy as onnx to: <checkpoint_dir>/exported/model_<N>.onnx
   ```

2. Stop the process manually after export if you only need the ONNX file.
3. If you need a short evaluation artifact, use a runtime timeout or a manual interrupt after export.

## 7. Key-listener thread warning during eval

### Symptom

A background-thread traceback mentions `keyboard` or the key listener does nothing.

### Cause

`eval_agent.py` starts a daemon thread that calls `keyboard.Listener`, but the import for `keyboard` is commented out in this checkout. The main evaluation/export path still runs, but the key listener is not reliable as written.

### Recovery

- Ignore the thread error if you only need ONNX export or a non-interactive visual run.
- If you need key-driven eval controls, patch the local checkout or run a branch where the `pynput.keyboard` import has been restored.

## 8. `train_agent.py` launches the wrong backend or uses the wrong simulator package

### Symptom

Training starts but the backend is not the one you intended, or the runtime errors mention a different simulator package.

### Cause

The script looks at `config.simulator._target_`, which is selected by the Hydra group `+simulator=<choice>`. Setting `sim_type` alone is not the important selection.

### Recovery

- Change the Hydra group, not only `sim_type`.
- Verify the chosen backend with `--help` or `--cfg job` before a long training run.

## 9. Relative path confusion for motions and checkpoints

### Symptom

A motion file or checkpoint path that exists in one shell seems to disappear in another.

### Cause

The scripts restore `os.chdir(hydra.utils.get_original_cwd())`. Relative paths are therefore resolved from the directory where the command was launched.

### Recovery

- Launch from the ASAP repository root.
- Prefer repository-relative paths such as `humanoidverse/data/motions/...` and `logs/...`.
- For detached paths, use absolute paths and `--require-existing-paths` in the builder if you want an early failure.
