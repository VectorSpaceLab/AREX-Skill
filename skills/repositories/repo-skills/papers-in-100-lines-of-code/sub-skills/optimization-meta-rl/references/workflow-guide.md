# Optimization, Meta-Learning, and RL Workflow Guide

This reference covers the compact educational entries that are not primarily
GAN/diffusion/flow or 3D rendering tasks. Use it to adapt isolated components
safely before attempting full training.

## Family map

| Family | Entries | Core pattern | First validation |
|---|---|---|---|
| Optimizers | Adam, RAdam | custom optimizer class with state buffers, bias correction or rectified variance, `zero_grad`, `step` | one scalar/model parameter update compared against expected direction |
| Activations and layers | ELU, GELU, SELU/SNN, Maxout, Network-in-Network | `nn.Module` layers, initialization, MLP/CNN training loops | CPU forward pass on tiny tensor; output shape and finite values |
| Meta-learning | MAML, Reptile, learned NeRF initialization | task sampler, inner-loop adaptation, cloned parameters, meta-optimizer step | one sampled task and one inner update with finite loss |
| Hyperparameter optimization | Optimizing Millions of Hyperparameters by Implicit Differentiation | hypergradient, inverse-HVP approximation, weight-decay wrapper | tiny linear/MLP toy problem and finite hypergradient |
| Deep Image Prior | Deep Image Prior | untrained CNN or decoder optimized against a single degraded image | tiny image/noise tensor reconstruction step |
| Reinforcement learning | DQN, Double DQN, PPO, Atari control | CNN policy/value networks, replay buffer or rollout loop, wrappers, epsilon/advantage updates | instantiate network and run one fake observation batch; avoid full emulator loop until environment is ready |

## Adaptation patterns

### Optimizer entries

- Fix global references when extracting. The Adam script's `step` logic is
  educational; when adapting, iterate over `self.model.parameters()` rather than
  relying on a global variable named `model`.
- Validate one update with known gradients before training on MNIST.
- Preserve epsilon, beta, and bias-correction placement when comparing to
  `torch.optim`.

### Activation/layer entries

- Treat Keras MNIST loading and plotting as demonstration scaffolding, not part
  of the reusable layer.
- For SELU/SNN, initialization and dropout choices matter for self-normalizing
  behavior; keep them explicit in the adaptation.
- For Maxout and Network-in-Network, verify reshaping/channel dimensions before
  training.

### Meta-learning and hypergradients

- MAML and Reptile examples use sinusoid tasks or NeRF-style learned
  initialization. Start with one task, one inner step, and a tiny batch.
- Be careful with `clone()`, `.data` updates, and `torch.autograd.grad`:
  educational code may prioritize brevity over full higher-order gradient
  hygiene.
- Hypergradient examples can be numerically brittle. Check finite values and
  dimensionality before scaling the inner optimization.

### Reinforcement learning

- DQN/DDQN/PPO scripts are training-scale demonstrations. Atari wrappers,
  replay buffers, frame stacking, ROM availability, and millions of environment
  steps make them unsuitable as quick smoke tests.
- For code adaptation, instantiate the network with fake observations and check
  action logits/values before connecting a real environment.
- For real experiments, pin Gym and Stable-Baselines3 versions exactly and
  verify Atari/ALE support separately.

## Loop-scale controls

Use the bundled estimator before running any training loop:

```bash
python scripts/estimate_training_steps.py --nb-epochs 30000000 --batch-size 32 --eval-interval 50000
```

Reduce the loop for debugging, but record that reduced loops validate wiring and
shape behavior only; they do not reproduce paper metrics.

## Validation signals

- One optimizer step changes parameters in the expected direction and resets
  gradients without losing state.
- Layer/activation forward passes preserve documented shapes and produce finite
  tensors.
- Meta-learning inner updates return parameters that can be evaluated on a
  held-out tiny task.
- Hypergradient computations produce finite vectors with expected shapes.
- RL networks return one value/logit per action and environment wrappers are
  validated before long loops.
