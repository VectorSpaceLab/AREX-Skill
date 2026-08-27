# Troubleshooting Policy Customization

## Wrong policy for Dict observations

Symptoms:

- Error or hint when using `MlpPolicy` or `CnnPolicy` with a Dict observation space.
- HER goal env fails at model construction.

Fix:

- Use `MultiInputPolicy` for Dict observations.
- Use `gymnasium.wrappers.FlattenObservation` only when you intentionally want to discard per-key processing and are not using HER.
- Remove nested Dict spaces; SB3 supports single-level Dict observations.

## Custom extractor shape mismatch

Symptoms:

- Linear layer shape errors during model creation or first forward pass.
- Runtime error such as matrix dimensions cannot be multiplied.
- Policy heads appear to expect a different feature width than the extractor returns.

Fix:

- Ensure `BaseFeaturesExtractor.__init__(..., features_dim=N)` matches the actual `forward()` output width.
- For Dict extractors, update `self._features_dim` to the concatenated total after building per-key extractors.
- Use `nn.ModuleDict` for per-key extractors.
- Run one sampled observation through `model.policy.extract_features(...)` or use `scripts/inspect_policy.py` before training.

## Image normalization and channel order

Symptoms:

- `NatureCNN` assertion says it should only be used with images.
- CNN receives unexpected channel count.
- Normalized float image spaces fail dtype/bounds checks.
- Tiny images fail convolution shape checks.

Fix:

- Use `CnnPolicy` for image-only spaces and `MultiInputPolicy` for Dict spaces with image keys.
- Prefer uint8 image spaces with bounds `[0, 255]` and let SB3 normalize by default.
- If the env already returns normalized images, set `policy_kwargs=dict(normalize_images=False)` or the algorithm-level equivalent where accepted.
- Confirm wrapper channel order; SB3 can transpose image observations when spaces are correctly declared.
- For very small images, reduce CNN complexity with a custom extractor instead of `NatureCNN`.

## Action noise on incompatible action spaces

Symptoms:

- Shape errors constructing `NormalActionNoise` or during `learn()`.
- Discrete-action algorithm receives action noise.

Fix:

- Use action noise only with continuous `Box` actions and off-policy continuous-control algorithms.
- Compute `n_actions = env.action_space.shape[-1]` and build `mean`/`sigma` arrays of that exact length.
- For DQN or other discrete-action use cases, remove `action_noise`.

## gSDE on incompatible action spaces

Symptoms:

- `ValueError` when setting `use_sde=True` on a discrete env such as CartPole.
- Assertion involving `squash_output` and `use_sde`.

Fix:

- Enable gSDE only for continuous-action environments.
- For PPO/A2C, set `squash_output=True` only together with `use_sde=True`.
- For SAC, remember output squashing is part of the algorithm's continuous-control policy.

## HER treated as an algorithm

Symptoms:

- `ImportError` after calling `HER("MlpPolicy", ...)`.
- Code expects `HER` to be a model class.

Fix:

- Replace `HER(...)` with an off-policy algorithm such as `DQN`, `SAC`, `TD3`, or `DDPG`.
- Pass `replay_buffer_class=HerReplayBuffer` and HER settings via `replay_buffer_kwargs`.
- Use `MultiInputPolicy` with goal environments.
- Load HER models with `env=...` so relabeled rewards can call `compute_reward()`.

## Loading saved custom policies

Symptoms:

- Load fails because a custom policy/extractor/optimizer class cannot be imported.
- Loaded model silently uses stale constructor values.

Fix:

- Keep custom classes in importable Python modules, not inside notebooks or local closures.
- Import those classes before calling `ModelClass.load(...)`.
- Use `custom_objects={...}` only for deliberate overrides, then print `model.policy` and verify predictions.
- Keep the same observation/action spaces when loading policy architecture customizations.

## Quick diagnosis order

1. Print `env.observation_space` and `env.action_space`.
2. Verify policy alias: `MlpPolicy`, `CnnPolicy`, or `MultiInputPolicy`.
3. Print `model.policy` before training.
4. Check `policy_kwargs` keys for the algorithm family: `vf` vs `qf`.
5. Instantiate with tiny `net_arch` and `train_steps=0` using `scripts/inspect_policy.py`.
6. Move to the environment/vectorization sibling if the issue is space declaration, wrappers, or env checker output.
