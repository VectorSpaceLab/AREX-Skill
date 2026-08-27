# Dreamer and ED2-Dreamer Workflows

Use this reference for tasks about Dreamer, ED2-Dreamer, latent imagination, world-model construction, DMControl visual control, log plotting, and ED2 dynamics decomposition.

## Family summary

Dreamer learns a compact latent world model from observations/actions, imagines trajectories in latent space, and learns actor/value behavior by backpropagating through imagined rollouts. AI-Optimizer includes a Vanilla Dreamer implementation and an ED2-Dreamer variant that exposes environment dynamics decomposition controls.

| Variant | Runtime framework | Core idea | Typical command shape |
|---|---|---|---|
| Vanilla Dreamer | TensorFlow 2.2-era code | Latent world model + actor/value learning by imagination | `python3 dreamer.py --logdir ./logdir/dmc_walker_walk/dreamer/1 --task dmc_walker_walk` |
| ED2-Dreamer | TensorFlow 2.1-era code | Dreamer plus environment dynamics decomposition | `python -u dreamer.py --logdir ./logdir/dmc_humanoid_walk/ED2_Dreamer --task dmc_humanoid_walk --model_num ED2_Dreamer --steps 5100000 --separate_schema ED2 --gpu_id 0` |

Both workflows require dm_control and a compatible rendering stack for visual-control tasks. Treat a full run as expensive and hardware-sensitive.

## Vanilla Dreamer recipe

Dependency family documented by the README:

```bash
pip3 install --user tensorflow-gpu==2.2.0
pip3 install --user tensorflow_probability
pip3 install --user git+git://github.com/deepmind/dm_control.git
pip3 install --user pandas
pip3 install --user matplotlib
```

Training command recipe:

```bash
python3 dreamer.py --logdir ./logdir/dmc_walker_walk/dreamer/1 --task dmc_walker_walk
```

Plotting command recipe:

```bash
python3 plotting.py --indir ./logdir --outdir ./plots --xaxis step --yaxis test/return --bins 3e4
```

TensorBoard recipe:

```bash
tensorboard --logdir ./logdir
```

### Vanilla Dreamer config knobs

The training script builds CLI flags from a `define_config()` dictionary. Useful knobs include:

| Area | Flags/defaults | Use |
|---|---|---|
| General | `--logdir .`, `--seed 0`, `--steps 5e6`, `--eval_every 1e4`, `--log_every 1e3`, `--precision 16` | Run identity, total environment steps, logging cadence, numerical precision. |
| Environment | `--task dmc_walker_walk`, `--envs 1`, `--parallel none`, `--action_repeat 2`, `--time_limit 1000`, `--prefill 5000` | DMControl task selection and interaction schedule. |
| Model | `--deter_size 200`, `--stoch_size 30`, `--num_units 400`, `--cnn_depth 32`, `--pcont False`, `--free_nats 3.0` | Latent state and network capacity. |
| Training | `--batch_size 50`, `--batch_length 50`, `--train_every 1000`, `--train_steps 100`, `--pretrain 100`, learning-rate flags | Dataset sequence length and update cadence. |
| Behavior | `--discount 0.99`, `--disclam 0.95`, `--horizon 15`, `--expl additive_gaussian`, `--expl_amount 0.3` | Actor/value imagination horizon and exploration. |

## ED2-Dreamer recipe

Dependency family documented by the ED2 README:

```bash
pip3 install --user tensorflow-gpu==2.1.0
pip3 install --user tensorflow_probability
pip3 install --user git+git://github.com/deepmind/dm_control.git
pip3 install --user pandas
pip3 install --user matplotlib
```

The provided launcher loops over GPU ids and writes background logs. For safer single-run construction, use a direct command rather than launching the loop:

```bash
python -u dreamer.py --logdir ./logdir/dmc_humanoid_walk/ED2_Dreamer --task dmc_humanoid_walk --model_num ED2_Dreamer --steps 5100000 --separate_schema ED2 --gpu_id 0
```

To run the integrated baseline path from the same code, use:

```bash
python -u dreamer.py --logdir ./logdir/dmc_humanoid_walk/Dreamer --task dmc_humanoid_walk --model_num Dreamer --steps 5100000 --separate_schema Vanilla --gpu_id 0
```

The ED2 config extends the Vanilla Dreamer knobs with:

| Flag | Default/source evidence | Use |
|---|---|---|
| `--gpu_id` | `0` | Select GPU id used by the ED2 script. |
| `--model_num` | `None` | Select vanilla versus ED2 model variant; README recipes use `Dreamer` or `ED2_Dreamer`. |
| `--separate_schema` | `None` | Select decomposition schema; README recipes use `Vanilla` or `ED2`. |
| `--buffer_size` | `10000000` | Replay/data buffer size in ED2 code. |
| `--log_images` | `False` in ED2 code | ED2 disables image logging by default. |

## Plotting and result inspection

Vanilla Dreamer includes a plotting script with these user-facing flags:

| Flag | Required/default | Meaning |
|---|---|---|
| `--indir` | required, one or more paths | Input log directories. |
| `--outdir` | required | Plot output directory. If `--subdir True`, it appends the first input stem. |
| `--xaxis`, `--yaxis` | required | Scalar keys, such as `step` and `test/return`. |
| `--tasks`, `--methods`, `--baselines` | regex lists | Filter runs. |
| `--bins` | `0` | Aggregate x-axis bin width. README example uses `3e4`. |
| `--aggregate` | `std` | Aggregation style. |
| `--labels`, `--colors` | even-length lists | Rename labels or colors. |

The plotting script parses booleans as literal `True`/`False` strings, not lowercase `true`/`false`.

## Task and modification guidance

- DMControl tasks in Dreamer commands use `dmc_<domain>_<task>` naming, such as `dmc_walker_walk` or `dmc_humanoid_walk` in the README recipes.
- For quick static or tiny-runtime validation, reduce `--steps`, `--eval_every`, `--prefill`, `--batch_size`, and logging; do not infer paper-quality results from small runs.
- To compare Vanilla Dreamer and ED2-Dreamer, keep `--task`, `--steps`, seeds, and logdir conventions consistent while only changing `--model_num` and `--separate_schema`.
- To change model capacity, adjust deterministic/stochastic state sizes, unit counts, CNN depth, and free-nats/kl settings before changing algorithm semantics.
- The implementation files separate model, wrapper, tool, and algorithm concerns; modifications should preserve config-driven flags so command recipes remain reproducible.

## Known Dreamer omissions

- No DMControl install, rendering, CUDA, or long training verification is included in this skill.
- ED2's provided launcher can start multiple background jobs; do not use it without explicit resource approval.
- TensorFlow 2.1/2.2 era GPU wheels may not install cleanly on modern Python/CUDA stacks. See troubleshooting before preparing an environment.
