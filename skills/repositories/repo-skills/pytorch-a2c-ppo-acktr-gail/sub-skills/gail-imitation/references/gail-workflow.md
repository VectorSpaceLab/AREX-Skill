# GAIL workflow in this repo

GAIL support is implemented by `main.py` and `a2c_ppo_acktr.algo.gail`. The workflow is: prepare expert trajectories, convert them to the repo's `.pt` dictionary format, then run PPO with `--gail` so discriminator rewards replace environment rewards during policy updates.

## 1. Prepare expert demonstrations

Upstream notes place external HDF5 expert files under `gail_experts/`; they are not bundled. The documented source command pattern is:

```bash
python gail_experts/convert_to_pytorch.py --h5-file trajs_halfcheetah.h5
```

For safer operation, prefer the bundled helper:

```bash
python sub-skills/gail-imitation/scripts/convert_gail_h5_to_pt.py \
  --h5-file gail_experts/trajs_halfcheetah.h5 \
  --pt-file gail_experts/trajs_halfcheetah.pt
```

See `gail-data-format.md` for required HDF5 keys and tensor shapes.

## 2. Match file naming to `--env-name`

When `--gail` is enabled, `main.py` constructs the expert filename as:

```python
file_name = os.path.join(
    args.gail_experts_dir,
    "trajs_{}.pt".format(args.env_name.split("-")[0].lower()),
)
```

Examples:

| `--env-name` | Expected `.pt` basename |
| --- | --- |
| `HalfCheetah-v2` | `trajs_halfcheetah.pt` |
| `Hopper-v2` | `trajs_hopper.pt` |
| `Walker2d-v2` | `trajs_walker2d.pt` |

Use `--gail-experts-dir` if the file lives outside the default `gail_experts/` directory.

## 3. Use vector-control observations only

The GAIL branch begins with:

```python
assert len(envs.observation_space.shape) == 1
```

So the built-in GAIL path is for vector observations such as MuJoCo/PyBullet-style continuous-control tasks. Atari/image observations are routed to ordinary training guidance instead; do not try to force `--gail` on a stacked image observation without changing the code.

## 4. Discriminator and dataset wiring

`main.py --gail` creates:

```python
discr = gail.Discriminator(
    envs.observation_space.shape[0] + envs.action_space.shape[0],
    100,
    device,
)
expert_dataset = gail.ExpertDataset(
    file_name,
    num_trajectories=4,
    subsample_frequency=20,
)
gail_train_loader = torch.utils.data.DataLoader(
    dataset=expert_dataset,
    batch_size=args.gail_batch_size,
    shuffle=True,
    drop_last=len(expert_dataset) > args.gail_batch_size,
)
```

`Discriminator(input_dim, hidden_dim, device)` is a two-hidden-layer Tanh MLP with a scalar logit output. `input_dim` must equal `state_dim + action_dim`. The default hidden size in `main.py` is `100`.

## 5. How training changes under `--gail`

After the policy collects each rollout, the GAIL branch:

1. Switches the vector normalizer to eval mode after ten updates.
2. Uses `100` discriminator epochs for the first ten policy updates as warm-up.
3. Uses `--gail-epoch` discriminator epochs after warm-up; default is `5`.
4. Calls `Discriminator.update(expert_loader, rollouts, obsfilt)`.
5. Replaces rollout rewards with `Discriminator.predict_reward(state, action, gamma, masks)` before computing returns.

`Discriminator.update` zips expert batches with rollout mini-batches, applies observation filtering to expert states, trains expert-vs-policy logits with binary cross entropy, and adds a gradient penalty. `predict_reward` computes a log-odds-style reward and normalizes returns with `RunningMeanStd`.

## 6. Command pattern

The upstream GAIL example is a long MuJoCo PPO run. Treat it as a launch pattern, not a smoke test:

```bash
python main.py \
  --env-name "HalfCheetah-v2" \
  --algo ppo \
  --use-gae \
  --log-interval 1 \
  --num-steps 2048 \
  --num-processes 1 \
  --lr 3e-4 \
  --entropy-coef 0 \
  --value-loss-coef 0.5 \
  --ppo-epoch 10 \
  --num-mini-batch 32 \
  --gamma 0.99 \
  --gae-lambda 0.95 \
  --num-env-steps 10000000 \
  --use-linear-lr-decay \
  --use-proper-time-limits \
  --gail \
  --gail-experts-dir gail_experts
```

For generic PPO/MuJoCo command construction, seed sweeps, log directories, `--no-cuda`, checkpoint playback, or evaluation intervals, route to `../training-workflows/`. For changing policy, rollout, action, or optimizer internals, route to `../model-components/`.

## 7. Safe verification strategy

Preferred checks for this sub-skill are:

- `python sub-skills/gail-imitation/scripts/convert_gail_h5_to_pt.py --help`
- Convert a tiny local HDF5 fixture containing `obs_B_T_Do`, `a_B_T_Da`, `r_B_T`, and `len_B`.
- Optionally instantiate `ExpertDataset` on the generated `.pt` file when the package and dependencies are importable.

Do not use long training, external data download, simulator installation, or CUDA as required verification for this sub-skill.