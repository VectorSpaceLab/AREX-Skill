# RL integration and bounded evaluation

This reference covers HighwayEnv as a reinforcement-learning benchmark or simulation target. It assumes environment creation already works. For environment selection and Gymnasium lifecycle details, use the simulation sub-skill. For observation/action/reward choices, use the observations-actions-rewards sub-skill.

## Dependency boundary

The `highway-env` package provides the Gymnasium environments and core simulation dependencies. It does not install training frameworks such as Stable-Baselines3, Torch, rl-agents, or old baselines/HER packages by default. Treat all RL libraries as optional project dependencies and verify them separately before writing training code.

A no-RL smoke path is always available:

```bash
python scripts/random_policy_rollout.py --env-id highway-v0 --episodes 1 --max-steps 20
```

Run this before launching long training to prove that reset, stepping, termination, rewards, crash reporting, and optional `rgb_array` rendering are working.

## Gymnasium loop contract for policies

Use the current Gymnasium reset/step signatures:

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)

env = gym.make("highway-fast-v0")
obs, info = env.reset(seed=0)
terminated = truncated = False
steps = 0
max_steps = 200
while not (terminated or truncated) and steps < max_steps:
    action = env.action_space.sample()  # replace with policy action
    obs, reward, terminated, truncated, info = env.step(action)
    steps += 1
env.close()
```

Always keep a step cap around smoke tests, evaluations, and custom policy loops. Avoid `while True` evaluation loops unless an external runner imposes an explicit timeout.

## Stable-Baselines3 compatibility caution

Some older HighwayEnv notebooks and scripts were written when Stable-Baselines3 support for Gymnasium was incomplete and may mention compatibility with old `highway-env` releases. For current HighwayEnv, prefer current Gymnasium signatures and verify that your Stable-Baselines3 version supports Gymnasium environments. If an SB3 run fails with reset returning a tuple, step returning five values, or wrapper/API errors, resolve the version mismatch before changing the environment.

## Minimal SB3 DQN skeleton

Use this only after the no-RL random rollout succeeds and `stable_baselines3` imports. The hyperparameters are a compact skeleton based on common HighwayEnv DQN examples; tune them for the task rather than treating them as guaranteed-good defaults.

```python
import gymnasium as gym
import highway_env
from stable_baselines3 import DQN

gym.register_envs(highway_env)

env = gym.make("highway-fast-v0")
model = DQN(
    "MlpPolicy",
    env,
    policy_kwargs={"net_arch": [256, 256]},
    learning_rate=5e-4,
    buffer_size=15_000,
    learning_starts=200,
    batch_size=32,
    gamma=0.8,
    train_freq=1,
    gradient_steps=1,
    target_update_interval=50,
    verbose=1,
)
model.learn(total_timesteps=1_000)  # smoke budget; increase only intentionally
model.save("highway_dqn_model")
env.close()
```

For a more serious DQN run, increase `total_timesteps` deliberately and record the budget. Do not leave evaluation as an unbounded loop.

## Minimal SB3 PPO skeleton with vectorized environments

Vectorized training can speed up sample collection, but it adds multiprocessing and wrapper complexity. Keep `n_envs` modest at first, avoid rendering inside worker processes, and put subprocess creation under a `__main__` guard in scripts.

```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv

if __name__ == "__main__":
    n_envs = 2
    batch_size = 64
    env = make_vec_env("highway-fast-v0", n_envs=n_envs, vec_env_cls=SubprocVecEnv)
    model = PPO(
        "MlpPolicy",
        env,
        policy_kwargs={"net_arch": {"pi": [256, 256], "vf": [256, 256]}},
        n_steps=batch_size * 12 // n_envs,
        batch_size=batch_size,
        n_epochs=10,
        learning_rate=5e-4,
        gamma=0.8,
        verbose=1,
    )
    model.learn(total_timesteps=1_000)  # smoke budget; increase only intentionally
    model.save("highway_ppo_model")
    env.close()
```

If vectorized creation fails, first reproduce the issue with a single environment. Then check that the factory is picklable, every worker receives the same observation/action space shape, and no human rendering is attempted in subprocesses.

## Image observations and CNN policies

HighwayEnv can expose rendered observations, such as grayscale stacks, for CNN policies. Image observations are heavier than kinematics observations and should be validated before training.

A typical image-observation skeleton is:

```python
import gymnasium as gym
import highway_env
from stable_baselines3 import DQN
from stable_baselines3.common.vec_env import DummyVecEnv

gym.register_envs(highway_env)

def make_env():
    env = gym.make(
        "highway-fast-v0",
        config={
            "observation": {
                "type": "GrayscaleObservation",
                "observation_shape": (128, 64),
                "stack_size": 4,
                "weights": [0.2989, 0.5870, 0.1140],
                "scaling": 1.75,
            }
        },
    )
    env.reset()
    return env

vec_env = DummyVecEnv([make_env])
model = DQN(
    "CnnPolicy",
    vec_env,
    learning_rate=5e-4,
    buffer_size=15_000,
    learning_starts=200,
    batch_size=32,
    gamma=0.8,
    train_freq=1,
    gradient_steps=1,
    target_update_interval=50,
    exploration_fraction=0.7,
    verbose=1,
)
model.learn(total_timesteps=1_000)  # smoke budget; increase only intentionally
vec_env.close()
```

Caveats:

- Inspect the observation shape before choosing a CNN policy. Grayscale stacks are channel-like arrays, and shape mismatches are common when wrappers transpose images.
- Pixel observations increase memory and training time. Validate with very small budgets first.
- Pixel observations are an observation configuration choice; for detailed shape and feature options, use the observations-actions-rewards sub-skill.
- Do not confuse recording a video with using image observations. A policy can train on kinematics while evaluation records `rgb_array` frames, or train on images without recording a video.

## Kinematics observations, MLPs, and vehicle ordering

A kinematics observation plus an MLP can produce reasonable but suboptimal policies because the MLP is sensitive to the order in which surrounding vehicles appear in the observation. If a scene is observed with vehicles listed in a different order, an MLP may treat it like a novel state.

Mitigations include:

- use an observation whose representation is not vehicle-order dependent, such as a grayscale image with a CNN;
- use a permutation-invariant or attention-based model when keeping entity/vehicle features;
- verify that the configured number of observed vehicles and selected features match the model input shape.

Poor MLP performance under kinematics observations is therefore not automatically evidence of a simulator bug.

## Optional rl-agents and planning algorithms

HighwayEnv is compatible with external RL/planning approaches such as DQN variants, value iteration on finite-MDP approximations, and tree search through external packages. These packages are not installed by `highway-env`. When using finite-MDP or planning methods, keep the conversion and rollout budget bounded and route environment/finite-MDP details to the simulation sub-skill.

## Bounded evaluation pattern

Use deterministic predictions for evaluation when the policy library supports it, but keep hard caps on episodes and steps. Aggregate returns, lengths, crashes, and success signals when available.

```python
def evaluate_policy(env, model, episodes=5, max_steps=500):
    results = []
    for episode in range(episodes):
        obs, info = env.reset(seed=episode)
        terminated = truncated = False
        total_reward = 0.0
        steps = 0
        crashed = False
        success = None
        while not (terminated or truncated) and steps < max_steps:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)
            steps += 1
            crashed = crashed or bool(info.get("crashed", False))
            if "is_success" in info:
                success = bool(info["is_success"])
        results.append(
            {
                "episode": episode,
                "return": total_reward,
                "steps": steps,
                "terminated": terminated,
                "truncated": truncated,
                "reached_step_cap": not (terminated or truncated),
                "crashed": crashed,
                "is_success": success,
            }
        )
    return results
```

For goal environments, include success rate. For driving tasks where random policies often crash, report crash rate separately from return so failures are visible.
