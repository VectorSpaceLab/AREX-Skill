---
name: optimization-meta-rl
description: "Routes Papers-in-100-Lines optimizer, activation, layer,
  meta-learning, hypergradient, Deep Image Prior, and reinforcement-learning
  tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Optimization, Meta-Learning, and RL

Use this sub-skill when the user asks about the compact optimizer, activation,
layer, meta-learning, hyperparameter optimization, Deep Image Prior, or
reinforcement-learning entries in Papers-in-100-Lines.

## Read these bundled files

- [Workflow guide](references/workflow-guide.md) maps the family entries,
  reusable classes/functions, adaptation patterns, long-loop controls, and
  validation signals.
- [Troubleshooting](references/troubleshooting.md) covers Keras/MNIST downloads,
  hard-coded CUDA, optimizer state pitfalls, autograd updates, gym/ALE/ROM
  setup, and plot/output side effects.
- [Implementation index](../../references/implementation-index.md) lists the
  owner group and entry metadata.
- [Dependency and backend guide](../../references/dependency-and-backend-guide.md)
  explains why older torch/Keras/gym pins should be isolated per entry.
- [estimate_training_steps.py](scripts/estimate_training_steps.py) estimates
  update counts before running long training examples.

## Trigger routes

- **Optimizers**: Adam and RAdam implementations, optimizer state, bias
  correction, variance rectification, or comparing to `torch.optim`.
- **Layers and activations**: Maxout, Network-in-Network, ELU, GELU, SELU/SNN.
- **Meta-learning and hypergradients**: MAML, Reptile, learned initializations,
  implicit differentiation, weight-decay hyperparameters.
- **Deep Image Prior**: image reconstruction via untrained convolutional model
  and noise input.
- **Reinforcement learning**: DQN, Double DQN, PPO, Atari wrappers, replay
  buffers, long environment loops.

## Safe workflow

1. Query the catalog if the target is ambiguous:

   ```bash
   python ../../scripts/query_implementation_index.py --group optimization-meta-rl --query "adam"
   ```

2. Read [Workflow guide](references/workflow-guide.md) for the family and pick
   the smallest reusable component: optimizer class, activation module,
   meta-update loop, hypergradient helper, or RL network.
3. Estimate loop size before running:

   ```bash
   python scripts/estimate_training_steps.py --nb-epochs 70000 --batch-size 10 --eval-interval 1000
   ```

4. For a quick check, create a CPU toy model/environment and run one or a few
   updates. Do not launch million-step Atari or 70k-step MAML loops as smoke
   tests.
5. Preserve autograd semantics when adapting meta-learning or hypergradient
   code; copying `.data` updates or cloned parameters blindly can change the
   algorithm.

## Boundaries

Route GANs, VAEs, flows, diffusion, DreamBooth, Stable Diffusion, and image
translation to [generative-models](../generative-models/SKILL.md). Route NeRF,
3D Gaussian splatting, SIREN/MFN, camera, ray, and 3D reconstruction tasks to
[neural-rendering-3d](../neural-rendering-3d/SKILL.md). Use
[paper-catalog-and-execution](../paper-catalog-and-execution/SKILL.md) for
catalog lookup and first-run planning.
