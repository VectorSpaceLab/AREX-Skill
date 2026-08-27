# Modules And Networks

## Core Concepts

`EvolvableModule` wraps `torch.nn.Module` with mutation-aware behavior. AgileRL modules can expose mutation methods that add/remove layers, change nodes/channels, adjust kernels, or otherwise alter architecture while preserving compatible weights where possible.

`EvolvableNetwork` builds on `EvolvableModule` for RL policies, actors, critics, Q-networks, and value networks. It usually contains:

- An encoder for the observation space.
- A head network that maps latent features to actions, values, or distributions.
- Mutation bookkeeping so algorithm-level mutation can apply compatible changes.

## Included Building Blocks

| Building block | Use |
| --- | --- |
| `EvolvableMLP` | Vector observations or dense heads. |
| `EvolvableCNN` | Image observations. |
| `EvolvableLSTM` | Recurrent/sequence processing. |
| `EvolvableMultiInput` | Dict/Tuple or mixed observation spaces. |
| `EvolvableSimBa` | SimBa-style residual MLP architecture. |
| `QNetwork`, `RainbowQNetwork`, `ContinuousQNetwork` | Discrete, distributional, and continuous Q/value estimation. |
| `ValueNetwork` | State-value function for policy-gradient workflows. |
| `DeterministicActor`, `StochasticActor` | Continuous deterministic policies and stochastic policies. |
| `DummyEvolvable` | Compatibility wrapper for non-evolvable PyTorch modules. |

## Build Pattern

1. Inspect the observation and action spaces.
2. Choose encoder type: MLP for vectors, CNN for images, LSTM for sequences, MultiInput for Dict/Tuple.
3. Define `encoder_config` and `head_config` with mutation bounds.
4. Construct the network or pass the config into `create_population(...)`.
5. Run a tiny forward pass before training.
6. Register custom modules/networks correctly if writing new algorithm classes.

## Custom Network Guidance

- Inherit `EvolvableModule` when the custom architecture should participate in architecture mutation.
- Use `DummyEvolvable` around a normal `torch.nn.Module` when architecture mutation is not needed or unsupported.
- Keep mutation methods deterministic enough to debug with a fixed seed.
- Ensure output shapes match algorithm expectations: Q-values for discrete actions, bounded continuous actions for deterministic actors, logits/distributions for stochastic policies.
