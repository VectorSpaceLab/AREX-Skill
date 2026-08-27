# Feature Extractors and Dict Observations

## SB3 preprocessing before feature extraction

SB3 preprocesses observations before sending them to the policy feature extractor:

- Images are normalized by default (`normalize_images=True`), converting uint8 `[0, 255]` images to floats in `[0, 1]`.
- Discrete observations are one-hot encoded.
- Vector observations are flattened by `FlattenExtractor` unless a custom extractor is supplied.
- Image observations may be transposed to channel-first format internally when the observation space marks them as images.

If images are already normalized floats, set `normalize_images=False`. For `NatureCNN` and `CombinedExtractor`, SB3 also passes `normalized_image=True` to relax dtype/bounds checks in the default extractor path.

## Custom `BaseFeaturesExtractor`

A custom extractor must derive from `stable_baselines3.common.torch_layers.BaseFeaturesExtractor` and call `super().__init__(observation_space, features_dim)` with a positive output dimension.

Minimal pattern:

```python
import torch as th
from torch import nn
from gymnasium import spaces
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

class SmallExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space: spaces.Box, features_dim: int = 32):
        super().__init__(observation_space, features_dim)
        input_dim = int(th.prod(th.tensor(observation_space.shape)))
        self.net = nn.Sequential(nn.Flatten(), nn.Linear(input_dim, features_dim), nn.ReLU())

    def forward(self, observations: th.Tensor) -> th.Tensor:
        return self.net(observations)
```

Use it with:

```python
policy_kwargs = dict(
    features_extractor_class=SmallExtractor,
    features_extractor_kwargs=dict(features_dim=32),
)
```

Requirements and pitfalls:

- `forward()` must return shape `(batch_size, features_dim)`.
- `features_dim` must match the final tensor width exactly; SB3 uses it to build action/value heads.
- Put submodules on `self`; PyTorch only registers modules assigned as attributes or inside `nn.ModuleDict`/`nn.Sequential`.
- Avoid creating layers inside `forward()`, which prevents optimizer registration and breaks save/load.
- Use a dummy forward pass in `__init__` to calculate CNN flatten sizes, and wrap it in `with th.no_grad()`.

## Image feature extractors

`NatureCNN` expects an image `Box` and assumes channel-first tensors at CNN time. Custom CNNs usually read `observation_space.shape[0]` for the channel count because SB3/wrappers handle transposition before policy use.

Watch these constraints:

- Use `CnnPolicy` only for image observation spaces, not arbitrary low-dimensional vectors.
- Use `MlpPolicy` for non-image vectors.
- If a CNN receives channel-last tensors unexpectedly, use the environment/vectorization sibling to add image wrappers or check channel-order metadata.
- For normalized images with `VecNormalize` or custom float image spaces, set `normalize_images=False` and confirm the extractor's `normalized_image` behavior.
- Small images can fail in `NatureCNN` because convolution kernels/strides require enough spatial size; use a custom CNN or larger image inputs.

## `MultiInputPolicy` and `CombinedExtractor`

Use `MultiInputPolicy` for `gymnasium.spaces.Dict` observations. The default `CombinedExtractor` creates one sub-extractor per key:

- Image-like keys use `NatureCNN` and output `cnn_output_dim` features, default `256`.
- Non-image keys are flattened, including vector and discrete-derived inputs.
- Per-key outputs are concatenated into a single feature vector passed to `net_arch`.

Example for reducing CNN output on a tiny Dict env:

```python
policy_kwargs = dict(
    net_arch=[64],
    features_extractor_kwargs=dict(cnn_output_dim=32),
)
model = PPO("MultiInputPolicy", dict_env, policy_kwargs=policy_kwargs)
```

Nested Dict observation spaces are not supported. Flatten nested structures into a single-level Dict before using SB3 policies.

## Custom `CombinedExtractor`

Use a custom extractor for mixed image/vector observations when the default CNN+flatten concatenation is too limited.

Important pattern:

```python
from torch import nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

class CustomCombinedExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space):
        super().__init__(observation_space, features_dim=1)
        extractors = {}
        total_concat_size = 0
        for key, subspace in observation_space.spaces.items():
            if key == "image":
                extractors[key] = nn.Sequential(nn.MaxPool2d(4), nn.Flatten())
                total_concat_size += (subspace.shape[1] // 4) * (subspace.shape[2] // 4)
            elif key == "vector":
                extractors[key] = nn.Sequential(nn.Linear(subspace.shape[0], 16), nn.ReLU())
                total_concat_size += 16
        self.extractors = nn.ModuleDict(extractors)
        self._features_dim = total_concat_size

    def forward(self, observations):
        return th.cat([extractor(observations[key]) for key, extractor in self.extractors.items()], dim=1)
```

Key requirements:

- Use `nn.ModuleDict`, not a plain dict, for extractor modules.
- Update `self._features_dim` after computing the true concatenated width.
- Handle every expected observation key or intentionally raise a clear error.
- Keep key order deterministic by iterating over `observation_space.spaces.items()`.

## Dict image + vector synthetic case

A difficult usability case should combine:

- Dict observation with an image key and a vector key.
- `MultiInputPolicy` with a custom combined extractor.
- `cnn_output_dim` or custom `features_dim` small enough to instantiate quickly.
- A dry run that calls `model.predict(obs)` without training.

Expected failure to test: custom extractor reports `features_dim=64` but returns `(batch, 63)` or misses one Dict key; SB3 should fail during policy head construction or first forward pass.
