# Training and inference CLI details

## Training command anatomy

```bash
protomotions train-agent \
  --robot-name <robot> \
  --simulator <backend> \
  --num-envs <per_gpu_envs> \
  --batch-size <per_gpu_batch> \
  --motion-file <motion_lib_or_motion> \
  --experiment-path <experiment.py> \
  --experiment-name <run> \
  [--ngpu <gpus>] [--nodes <nodes>] [--use-wandb] [--use-slurm] \
  [--training-max-steps <steps> | --training-max-iterations <iters>] \
  [--overrides key=value ...]
```

Use `--create-config-only` to generate `resolved_configs*.pt` and sidecars without training. This is the preferred first check for new experiment files or checkpoint migrations.

## Inference command anatomy

```bash
protomotions inference-agent \
  --checkpoint <checkpoint> \
  --simulator <backend> \
  [--num-envs <n>] [--headless] [--full-eval] \
  [--motion-file <override_motion>] [--scenes-file <override_scenes>] \
  [--command-source target=keyboard] \
  [--overrides key=value ...]
```

`--full-eval` is safer for servers because it exits after evaluating the motion set. Interactive inference without `--full-eval` usually runs until interrupted.

## Override format

`--overrides` supports scalar config paths:

```bash
--overrides "agent.num_mini_epochs=4" "env.max_episode_length=500"
```

Supported top-level config namespaces include `env`, `simulator`, `robot`, `agent`, `terrain`, `motion_lib`, and `scene_lib`. Complex values such as lists, nested dataclasses, or custom objects should be expressed in an experiment Python file.

## W&B and metrics

With `--use-wandb`, common metrics include:

- `Eval/gt_err`: unbiased position tracking error, lower is better.
- `Eval/success_rate`: motion completion rate.
- `Train/episode_reward`: can fluctuate when prioritized sampling focuses on hard motions.
- `Train/clip_frac`: keep around or below 0.3 for stable PPO updates; lower LR if consistently high.
- actor/critic gradient norms: watch for spikes.

## Bounded validation

For a code or config change, prefer this order:

1. import/package smoke;
2. `protomotions train-agent --help` and `protomotions inference-agent --help`;
3. `--create-config-only` with a tiny or user-provided motion path;
4. headless full-eval with a small env count;
5. full training only after backend and data are verified.
