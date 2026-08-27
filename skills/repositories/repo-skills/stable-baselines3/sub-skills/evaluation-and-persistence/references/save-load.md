# Save, Load, and Parameter Transfer

## Standard model save/load

SB3 algorithms save to a `.zip` archive and load through the algorithm class, not by mutating an existing instance:

```python
from stable_baselines3 import PPO

model = PPO("MlpPolicy", "CartPole-v1", verbose=1)
model.learn(100_000)
model.save("ppo_cartpole.zip")

del model
model = PPO.load("ppo_cartpole.zip", env="CartPole-v1", device="auto")
obs, info = model.get_env().reset()
action, state = model.predict(obs, deterministic=True)
```

Operational notes:

- `load()` creates a new model object. It does not update an already-created model in place.
- Pass `env=` when you want to continue training, evaluate with `model.get_env()`, or bind a loaded model to a new environment.
- Use `force_reset=True` when changing envs after loading so stale last observations are discarded; use `force_reset=False` only when intentionally preserving current env state.
- `device="auto"` maps to CUDA when available and otherwise CPU. Use `device="cpu"` for portable inference/debugging.
- `predict(obs, deterministic=True)` should reproduce deterministic saved actions after load when inputs and wrappers match.

## SB3 zip structure

A saved SB3 model archive contains JSON metadata plus PyTorch state dictionaries. Typical entries are:

- `data`: JSON class/algorithm parameters such as spaces, schedules, and configuration. Non-JSON objects are cloudpickled and base64-encoded with type metadata.
- `policy.pth`: PyTorch policy state dictionary.
- `*.optimizer.pth`: optimizer state dictionaries.
- `pytorch_variables.pth`: additional PyTorch variables, when needed by the algorithm.
- `_stable_baselines3_version`: SB3 version used to save.
- `system_info.txt`: OS, Python, package, and hardware info from the saving machine.

Inspect without loading arbitrary model code:

```python
import zipfile

with zipfile.ZipFile("model.zip") as archive:
    print(archive.namelist())
    print(archive.read("_stable_baselines3_version").decode())
    print(archive.read("system_info.txt").decode()[:1000])
```

Do not hand-edit the archive unless you are doing controlled recovery; prefer `custom_objects` for broken serialized objects.

## Loading around custom object mismatches

If loading fails because a pickled schedule, function, custom policy component, learning-rate object, or env-related object cannot be deserialized, pass replacements through `custom_objects`:

```python
from stable_baselines3 import PPO

model = PPO.load(
    "old_model.zip",
    env="CartPole-v1",
    custom_objects={
        "learning_rate": 3e-4,
        "clip_range": 0.2,
    },
    print_system_info=True,
    device="cpu",
)
```

Rules:

- Keys must match saved top-level data keys; unknown keys are ignored rather than added to the model.
- `custom_objects` prevents deserialization of the matching saved object and substitutes your replacement.
- `print_system_info=True` prints saved/current environment info to compare Python, SB3, PyTorch, OS, and device differences.
- Prefer CPU loading first when diagnosing portability, then move back to CUDA after the model loads.

## Replay buffer persistence

Off-policy algorithms such as `DQN`, `SAC`, `TD3`, and `DDPG` may need replay buffer persistence to resume learning behavior:

```python
model.save("sac_model.zip")
model.save_replay_buffer("sac_replay_buffer.pkl")

model = SAC.load("sac_model.zip", env="Pendulum-v1")
model.load_replay_buffer("sac_replay_buffer.pkl")
model.learn(100_000, reset_num_timesteps=False)
```

`CheckpointCallback(save_replay_buffer=True)` writes replay buffer sidecars automatically when the model has a replay buffer.

## VecNormalize persistence

Models trained with `VecNormalize` require saved normalization statistics for meaningful evaluation and continued training:

```python
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

train_env = VecNormalize(DummyVecEnv([lambda: make_env()]))
model.learn(100_000)
model.save("model.zip")
train_env.save("vecnormalize.pkl")

base_eval_env = DummyVecEnv([lambda: make_env()])
eval_env = VecNormalize.load("vecnormalize.pkl", base_eval_env)
eval_env.training = False
eval_env.norm_reward = False
model = PPO.load("model.zip", env=eval_env)
```

Best practices:

- Save `VecNormalize` sidecars together with model checkpoints.
- Set `training=False` for evaluation so running statistics stop changing.
- Set `norm_reward=False` for evaluation if you want original reward scale.
- Ensure train and eval env wrappers match; `EvalCallback` synchronizes normalization when both sides are compatible.

## Parameter transfer with get_parameters/set_parameters

Use `get_parameters()` and `set_parameters()` for weight transfer, partial loading, or controlled experiments:

```python
source_params = source_model.get_parameters()
target_model.set_parameters(source_params, exact_match=False)
```

Behavior validated by SB3 tests:

- `get_parameters()` returns nested state dictionaries keyed by object names such as policy and optimizers.
- `set_parameters(params, exact_match=True)` requires all expected objects and tensors to match; missing entries raise errors.
- `set_parameters(params, exact_match=False)` allows partial object/tensor updates, useful when transferring only compatible modules.
- Invalid object names raise `ValueError` even with `exact_match=False`.
- Optimizer state can have custom layouts; skip or handle it separately unless resuming exact training.

## Continuing training after load

For clean continuation:

```python
model = PPO.load("checkpoint.zip", env=train_env, device="auto")
model.learn(total_timesteps=200_000, reset_num_timesteps=False)
```

Checklist:

- Recreate or load the same wrapper stack, especially `Monitor`, image wrappers, frame stacks, and `VecNormalize`.
- Load replay buffers for off-policy algorithms if continued sample distribution matters.
- Keep `reset_num_timesteps=False` to maintain logging/timestep continuity.
- Use the same `tb_log_name` for continuous TensorBoard curves.
- Verify deterministic predictions on a fixed observation before and after moving artifacts.
