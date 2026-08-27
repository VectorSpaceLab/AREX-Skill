# Evaluation Workflow

This reference adapts the repository's `test.py` workflow into a safe, reusable evaluation process. It is intentionally configuration-first: resolve the checkpoint and policy settings before importing Gym or starting render loops.

## Native evaluation pattern

The native evaluation script follows this sequence:

1. Choose `env_name`, `has_continuous_action_space`, `max_ep_len`, and `action_std`.
2. Create the environment with `gym.make(env_name)`.
3. Read dimensions from the live environment:
   - `state_dim = env.observation_space.shape[0]`
   - continuous action space: `action_dim = env.action_space.shape[0]`
   - discrete action space: `action_dim = env.action_space.n`
4. Construct `PPO(state_dim, action_dim, lr_actor, lr_critic, gamma, K_epochs, eps_clip, has_continuous_action_space, action_std)`.
5. Resolve the checkpoint path as `PPO_preTrained/<env_name>/PPO_<env_name>_<random_seed>_<run_num_pretrained>.pth`.
6. Call `ppo_agent.load(checkpoint_path)`.
7. For each test episode, repeatedly call `ppo_agent.select_action(state)`, step the environment, accumulate reward, optionally render, clear `ppo_agent.buffer`, and print the reward.
8. Report the average reward across all test episodes.

The native defaults are `total_test_episodes=10`, `render=True`, `frame_delay=0`, `lr_actor=0.0003`, `lr_critic=0.001`, `gamma=0.99`, `eps_clip=0.2`, and `K_epochs=80`.

## Recommended preflight

Run the bundled helper before a rollout:

```bash
python scripts/evaluation_config_helper.py \
  --env-name RoboschoolWalker2d-v1 \
  --checkpoint-root PPO_preTrained \
  --check-file
```

Use `--checkpoint-root` for a directory that contains environment subdirectories such as `RoboschoolWalker2d-v1/`. Use `--checkpoint-path` when the checkpoint lives somewhere else.

If you only need to identify available built-in presets, run:

```bash
python scripts/evaluation_config_helper.py --list-presets
```

The helper does not run Gym episodes. It catches mistakes such as misspelled environment names, wrong checkpoint roots, missing `action_std` for continuous policies, or a checkpoint filename that names a different environment.

## Minimal rollout skeleton

Use this skeleton in user code after dependencies are installed. It handles both old Gym-style and newer Gymnasium-style reset/step returns.

```python
import time
import gym  # or gymnasium as gym

# Import PPO from the generated root skill's shared core module.


def reset_env(env):
    out = env.reset()
    return out[0] if isinstance(out, tuple) else out


def step_env(env, action):
    out = env.step(action)
    if len(out) == 5:
        next_state, reward, terminated, truncated, info = out
        return next_state, reward, bool(terminated or truncated), info
    next_state, reward, done, info = out
    return next_state, reward, bool(done), info


env_name = "RoboschoolWalker2d-v1"
has_continuous_action_space = True
max_ep_len = 1000
action_std = 0.1
checkpoint_path = "PPO_preTrained/RoboschoolWalker2d-v1/PPO_RoboschoolWalker2d-v1_0_0.pth"

env = gym.make(env_name)
state_dim = env.observation_space.shape[0]
action_dim = env.action_space.shape[0] if has_continuous_action_space else env.action_space.n

ppo_agent = PPO(
    state_dim,
    action_dim,
    lr_actor=0.0003,
    lr_critic=0.001,
    gamma=0.99,
    K_epochs=80,
    eps_clip=0.2,
    has_continuous_action_space=has_continuous_action_space,
    action_std_init=action_std,
)
ppo_agent.load(checkpoint_path)

rewards = []
for episode in range(10):
    state = reset_env(env)
    episode_reward = 0.0
    for _ in range(max_ep_len):
        action = ppo_agent.select_action(state)
        state, reward, done, _ = step_env(env, action)
        episode_reward += reward
        if done:
            break
    ppo_agent.buffer.clear()
    rewards.append(episode_reward)

print("average test reward:", round(sum(rewards) / len(rewards), 2))
env.close()
```

For a human render loop, insert `env.render()` and an optional `time.sleep(frame_delay)` inside the timestep loop. Do this only after the display path is known to work.

## Rendering choices

- **No rendering:** best for smoke tests, headless servers, CI, and reward-only evaluation. Leave render disabled.
- **Human window rendering:** works only when the environment supports a human render mode and the process has a display. Some newer Gym/Gymnasium versions require `gym.make(env_name, render_mode="human")` rather than calling `env.render()` with no mode.
- **Frame capture:** use an `rgb_array` render mode or equivalent. Frame saving and GIF composition belong to the [visualization sub-skill](../../visualization/SKILL.md), not this evaluation sub-skill.
- **Remote or notebook rendering:** the Colab workflow used virtual display packages (`xvfb`, `python-opengl`, `pyvirtualdisplay`) for headless frame capture. Locally, prefer normal rendering and avoid virtual display setup unless needed.

## Interpreting results

The native script prints every episode reward and an average across `total_test_episodes`. Reward variance can be high; a single failed episode does not necessarily mean the checkpoint failed to load. Check for these distinct cases:

- **Immediate exception during load:** usually checkpoint path, architecture, or dependency mismatch.
- **Successful load but poor continuous-control reward:** often wrong `action_std`, wrong environment variant, or a changed environment implementation.
- **Successful numeric evaluation but render failure:** display/render-mode issue, not necessarily a policy issue.

## Load/save compatibility reminder

The root PPO implementation saves only the `policy_old.state_dict()`. Loading a checkpoint restores that state dict into both `policy_old` and `policy` using `torch.load` with `map_location`. The checkpoint does not carry the environment name, action-space type, `action_std`, or evaluation episode limits as metadata, so keep those values in your evaluation config.
