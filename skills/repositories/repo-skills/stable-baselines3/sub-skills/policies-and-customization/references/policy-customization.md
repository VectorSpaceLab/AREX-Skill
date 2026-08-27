# Policy Customization

## Policy aliases

SB3 accepts either a policy alias string or a policy class.

- `MlpPolicy`: vector-like observations. Internally uses a flattening feature extractor unless overridden.
- `CnnPolicy`: image observations. Uses `NatureCNN`; images are expected to be image spaces and are preprocessed before the CNN.
- `MultiInputPolicy`: `gymnasium.spaces.Dict` observations. Uses `CombinedExtractor` by default and is mandatory for Dict observations, including HER goal environments.
- A custom policy class: subclass the algorithm-compatible policy, such as `ActorCriticPolicy` for PPO/A2C, when `policy_kwargs` is not enough.

Common mistake: using `MlpPolicy` or `CnnPolicy` for a Dict observation space raises a policy hint/error. Switch to `MultiInputPolicy` or flatten the observation externally if a flat vector policy is truly intended.

## `policy_kwargs` essentials

Pass model-construction policy settings through `policy_kwargs`:

```python
import torch as th
from stable_baselines3 import PPO

policy_kwargs = dict(
    activation_fn=th.nn.ReLU,
    net_arch=dict(pi=[32, 32], vf=[64, 64]),
)
model = PPO("MlpPolicy", "CartPole-v1", policy_kwargs=policy_kwargs)
```

Useful keys include:

- `net_arch`: hidden-layer sizes after the feature extractor.
- `activation_fn`: PyTorch activation class, not an instance; use `th.nn.ReLU`, not `th.nn.ReLU()`.
- `features_extractor_class`: custom extractor class deriving from `BaseFeaturesExtractor`.
- `features_extractor_kwargs`: kwargs passed to the extractor constructor, such as `features_dim` or `cnn_output_dim`.
- `normalize_images`: whether image observations are divided by 255 before feature extraction.
- `optimizer_class` and `optimizer_kwargs`: custom optimizer settings.
- `share_features_extractor`: controls sharing between actor/critic where applicable.

## `net_arch` by algorithm family

On-policy actor-critic algorithms such as PPO and A2C use policy/value-function terminology:

```python
policy_kwargs = dict(net_arch=dict(pi=[64, 64], vf=[64, 64]))
```

- `pi`: actor/policy latent network.
- `vf`: value-function latent network.
- `net_arch=[128, 128]`: same hidden sizes for actor and value network.
- `net_arch=[]`: no hidden MLP after features; output heads attach directly.

Off-policy actor-critic algorithms such as SAC, TD3, and DDPG use policy/Q-function terminology:

```python
policy_kwargs = dict(net_arch=dict(pi=[64, 64], qf=[400, 300]))
```

- `pi`: actor network.
- `qf`: critic/Q-function network.
- `net_arch=[256, 256]`: same hidden sizes for actor and critic branches.
- Dict-form off-policy `net_arch` must provide both `pi` and `qf`.

DQN uses its own Q-network policy architecture; simple list `net_arch` customization is the common case.

## Default architecture expectations

Defaults vary by algorithm and observation type:

- 1D observations: PPO/A2C/DQN commonly use two 64-unit layers; SAC commonly uses 256-unit layers; TD3/DDPG commonly use `[400, 300]`.
- Image observations: `NatureCNN` performs feature extraction; off-policy actor/critic networks may have separate extractors.
- Dict observations: `CombinedExtractor` builds per-key extractors and concatenates their outputs before `net_arch`.

Print `model.policy` or use `scripts/inspect_policy.py` to verify the actual resolved network.

## Advanced custom policy classes

Use a custom policy class when you need behavior that `policy_kwargs` cannot express, such as a custom actor/critic latent module.

For PPO/A2C, subclass `ActorCriticPolicy` and override `_build_mlp_extractor()`. The custom extractor module must expose:

- `latent_dim_pi`: actor latent output dimension.
- `latent_dim_vf`: value latent output dimension.
- `forward_actor(features)` and `forward_critic(features)` methods.
- `forward(features)` returning `(latent_policy, latent_value)`.

Keep the constructor signature compatible with SB3: accept `observation_space`, `action_space`, `lr_schedule`, `*args`, and `**kwargs`, then call `super().__init__()`.

## Save/load persistence notes

- `policy_kwargs` are saved with SB3 models and loaded automatically when all referenced classes are importable.
- Custom feature extractor classes, custom policy classes, custom activations, or optimizer classes must be importable at load time.
- If a saved object changed or cannot be imported, use the model class `load(..., custom_objects={...})` mechanism to override constructor-time objects, then verify predictions and architecture.
- HER replay buffers require an environment at load time because relabeling calls `env.compute_reward()`; see [HER and replay buffers](her-and-replay-buffers.md).

## Quick checklist

1. Match policy alias to observation space: `MlpPolicy` for flat/vector, `CnnPolicy` for image, `MultiInputPolicy` for Dict.
2. Match `net_arch` keys to algorithm family: `vf` for PPO/A2C value functions, `qf` for SAC/TD3/DDPG critics.
3. Pass PyTorch classes where SB3 expects classes, such as `activation_fn=th.nn.Tanh`.
4. Print `model.policy` before long training runs.
5. Save custom classes in importable modules before training if the model will be reloaded later.
