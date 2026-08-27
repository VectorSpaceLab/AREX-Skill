# ASAP troubleshooting

Use this page for cross-cutting ASAP failures that are not specific to motion retargeting or deployment.

## 1. Wrong invocation style

### Symptom

```text
ModuleNotFoundError: No module named 'utils.config_utils'
```

or

```text
ModuleNotFoundError: No module named 'humanoidverse'
```

### Recovery

- Run from the repository root.
- Use script form:

  ```bash
  python humanoidverse/train_agent.py --help
  python humanoidverse/eval_agent.py --help
  ```

- Do not use `python -m humanoidverse.train_agent` in this checkout.

## 2. Hydra override mistakes

### Symptom

```text
Could not override 'headless'.
To append to your config use +headless=True
```

### Recovery

- In training, `headless` already exists in `base.yaml`.
- In evaluation, use `+headless=True` and `+num_envs=1` if you need to add those keys before the checkpoint config is merged.
- Use the command builder or `--help` output to confirm group names.

## 3. Backend package missing

### Symptom

```text
ModuleNotFoundError: No module named 'isaacgym'
```

or `omni`, `genesis`, or `mujoco` import errors.

### Recovery

- Read [`install-and-backends.md`](install-and-backends.md).
- Install the backend package for the chosen Hydra `+simulator=<choice>`.
- If you only need the command text, use the training/evaluation builder or `--cfg job` instead of launching the simulator.

## 4. Checkpoint config loading

### Symptom

`eval_agent.py` logs that it cannot find a training config next to the checkpoint.

### Recovery

- Keep `config.yaml` next to each checkpoint directory.
- For detached checkpoints, supply the full matching Hydra override set.
- If you are using `PPODeltaA`, keep the frozen policy checkpoint and its config together as well.

## 5. Evaluation loops forever

### Symptom

Evaluation export finishes, but the process keeps running.

### Recovery

- This is expected: `eval_agent.py` exports ONNX and then calls an infinite evaluation loop.
- Stop the process after the export log if you only need the model artifact.

## Cross-links

- Root router: [`../SKILL.md`](../SKILL.md)
- Training and evaluation: [`../sub-skills/training-and-evaluation/SKILL.md`](../sub-skills/training-and-evaluation/SKILL.md)
- Motion retargeting: [`../sub-skills/motion-retargeting/SKILL.md`](../sub-skills/motion-retargeting/SKILL.md)
- Sim2real deployment: [`../sub-skills/sim2real-deployment/SKILL.md`](../sub-skills/sim2real-deployment/SKILL.md)
