# Model Components Troubleshooting

Use this reference when direct API calls fail before creating or running full Gym environments.

## Action Space Is Unsupported

Symptom:

```text
NotImplementedError
```

Likely cause: `Policy` supports only action spaces whose class name is exactly `Discrete`, `Box`, or `MultiBinary`.

Fix:

- For custom discrete-like spaces, adapt or wrap them to a Gym-compatible `Discrete` space before constructing `Policy`.
- For continuous actions, use a one-dimensional `Box`; `Policy` uses `action_space.shape[0]`.
- For multi-binary actions, verify `Policy.act` and `Policy.evaluate_actions` with a synthetic smoke before training.
- To add a new space, update `Policy`, add a distribution head, update `RolloutStorage` action-shape logic, and add tests for `sample`, `log_probs`, `entropy`, and `mode`.

Caveat: this source snapshot's `FixedBernoulli.log_probs` implementation contains a `super.log_prob(...)` call instead of `super().log_prob(...)`. If `MultiBinary` policies fail with an `AttributeError` around `log_prob`, patch that typo and rerun a `MultiBinary`-specific smoke test.

## Observation Shape Is Unsupported

Symptom:

```text
NotImplementedError
```

Likely cause: `Policy` selects a base only for one-dimensional vector observations and three-dimensional image observations.

Fix:

- Vector state: use `obs_shape=(feature_dim,)`, which selects `MLPBase`.
- Image state: use channel-first three-dimensional shape, which selects `CNNBase`.
- Other shapes: flatten or wrap observations, or pass a custom base with the required base interface.

## CNNBase Fails With a Linear Shape Error

Symptoms include errors such as:

```text
mat1 and mat2 shapes cannot be multiplied
shape '[-1, ...]' is invalid
```

Likely cause: `CNNBase` assumes Atari-like 84x84 image preprocessing because its final linear layer is fixed at `32 * 7 * 7` inputs. A three-dimensional custom pixel observation can select `CNNBase` but still fail if the spatial dimensions are not compatible.

Fix:

- Use the training workflow's Atari preprocessing/frame-stack route for Atari environments.
- For non-Atari pixel inputs, add a wrapper that emits the expected channel-first spatial shape or replace `CNNBase` with a custom base sized for the environment.
- For vector control tasks, avoid image observations and use `MLPBase`.

## Custom Pixel Environment Rejected by Environment Wrappers

Symptom from environment creation:

```text
CNN models work only for atari,
please use a custom wrapper for a custom pixel input env.
```

Likely cause: non-Atari environments with 3D observations are intentionally rejected in the environment wrapper stack. Route to `../training-workflows/` for wrapper-level changes, then return here to verify the resulting `Policy` shape.

## Recurrent ACKTR Is Rejected

Symptom from CLI argument parsing:

```text
AssertionError: Recurrent policy is not implemented for ACKTR
```

Likely cause: the argument parser allows recurrent policies only for A2C and PPO. Programmatic callers should enforce the same rule before creating `A2C_ACKTR(..., acktr=True)`.

Fix:

- Use `--algo a2c --recurrent-policy` or `--algo ppo --recurrent-policy`.
- For ACKTR, use a feed-forward policy unless you are prepared to implement and verify recurrent KFAC support.

## PPO Mini-Batch Assertions

Feed-forward PPO symptom:

```text
PPO requires the number of processes (...) * number of steps (...) = ... to be greater than or equal to the number of PPO mini batches (...).
```

Cause: `num_steps * num_processes < num_mini_batch` and no explicit `mini_batch_size` was supplied.

Recurrent PPO symptom:

```text
PPO requires the number of processes (...) to be greater than or equal to the number of PPO mini batches (...).
```

Cause: recurrent generator splits by process, so `num_processes >= num_mini_batch` is required.

Fix:

- For tiny synthetic tests, use `num_mini_batch=1`.
- For real PPO runs, increase `num_steps`/`num_processes` or lower `num_mini_batch`.
- Keep recurrent PPO especially conservative: choose a minibatch count that divides or is less than the number of processes.

## Rollout Insert Shape or Dtype Mismatch

Symptoms:

```text
RuntimeError: output with shape ... doesn't match the broadcast shape ...
RuntimeError: Expected object of scalar type Long but got Float
```

Likely causes:

- `Discrete` actions must have shape `(num_processes, 1)` and dtype `long`.
- `Box` and `MultiBinary` actions use width `action_space.shape[0]` and floating-point tensors.
- Rewards, masks, bad masks, value predictions, and action log probabilities should have shape `(num_processes, 1)`.
- `obs` passed to `insert` should be the next observation with shape `(num_processes, *obs_shape)`.

Fix: print the tensor shapes before `insert`, compare them with the `RolloutStorage` tensor table in `api-reference.md`, and convert dtype/shape before copying.

## Recurrent Hidden State Mismatch

Symptoms:

```text
RuntimeError: Expected hidden size ...
RuntimeError: shape ... is invalid for input of size ...
```

Likely causes:

- `rnn_hxs` width does not equal `policy.recurrent_hidden_state_size`.
- Flattened rollout batches use `(T * N, ...)` observations but hidden state should remain `(N, hidden_size)`.
- `masks` were flattened inconsistently with observations.

Fix:

- Initialize hidden states as `torch.zeros(num_processes, policy.recurrent_hidden_state_size, device=device)`.
- For non-recurrent policies, still pass hidden states of width `1`.
- When manually calling `evaluate_actions`, mirror the flattening logic used in `A2C_ACKTR.update` or `PPO.update`.

## Tensor Device Mismatch

Symptoms:

```text
Expected all tensors to be on the same device
Input type ... and weight type ... should be the same
```

Fix:

- Move the policy and rollout tensors to the same device: `policy.to(device)` and `rollouts.to(device)`.
- Create masks, rewards, hidden states, and synthetic observations directly on that device.
- For CPU-only inspection, keep everything on CPU; do not mix CUDA tensors into a CPU smoke.

## KFAC `torch.symeig` or Hook Failures

Symptoms on newer PyTorch releases can include deprecation errors, removed API errors, or hook warnings around:

```text
torch.symeig
register_backward_hook
```

Likely cause: the KFAC implementation is written for older PyTorch APIs. It calls `torch.symeig(..., eigenvectors=True)` during optimizer steps and uses backward hooks for covariance statistics.

Fix options:

- Prefer A2C or PPO when ACKTR/KFAC is not required.
- If ACKTR is required, verify the exact PyTorch version with a minimal ACKTR update before long training.
- Patch eigendecomposition to a modern API such as `torch.linalg.eigh` only after checking eigenvalue/eigenvector ordering and tensor shapes.
- Treat hook warnings as a sign to run a focused ACKTR regression check; do not assume a successful import proves KFAC updates work.

## KFAC KeyError During Step

Symptom:

```text
KeyError: Parameter containing...
```

Likely cause: KFAC expects every trainable parameter to have a corresponding module update. New parameterized modules outside `Linear`, `Conv2d`, or `AddBias` may not be represented in the `updates` dictionary.

Fix:

- Keep ACKTR policies within the known module set.
- If adding modules, extend KFAC covariance handling and verify `KFACOptimizer.step` with a tiny forward/backward/update.
- Use non-ACKTR A2C or PPO for architectures outside KFAC's assumptions.

## Learning Rate Does Not Change as Expected

Likely causes:

- `utils.update_linear_schedule` mutates all optimizer param groups in place.
- Passing an already-decayed value as `initial_lr` causes compounding decay.
- ACKTR wrappers may expose `optimizer.lr` differently from standard PyTorch optimizers.

Fix: keep an explicit immutable initial learning-rate value in your training configuration and pass that to the schedule helper.

## Monitor CSV Files Disappear

Likely cause: `utils.cleanup_log_dir(log_dir)` deletes `*.monitor.csv` files when `log_dir` already exists.

Fix:

- Use a fresh log directory for experiments that may be cleaned.
- Archive existing monitor CSVs before calling the helper.
- Route log/artifact questions to the root data-and-artifacts reference or `../training-workflows/`.
