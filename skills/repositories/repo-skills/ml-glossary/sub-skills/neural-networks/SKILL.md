---
name: neural-networks
description: "Explains ML Glossary neural-network concepts, forward and
  backpropagation, activations, layers, losses, optimizers, regularization, and
  architecture examples."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Neural Networks

Use this sub-skill for ML Glossary tasks about neural-network concepts, training mechanics, activations/losses/optimizers, layers, regularization, and architecture examples such as autoencoders, CNNs, GANs, MLPs, RNNs, GRUs, LSTMs, and VAEs.

## Read when

- The user asks how neural networks make predictions or learn.
- The task mentions neurons, synapses, weights, bias, layers, weighted inputs, forwardpropagation, backpropagation, chain rule through layers, activation functions, loss functions, optimizers, gradient accumulation, dropout, batch normalization, convolution, pooling, recurrent units, autoencoders, CNNs, GANs, MLPs, RNNs, or VAEs.
- A documentation task needs the correct beginner wording for neural-network pages or architecture entries.
- The user asks whether legacy PyTorch/NumPy source snippets should be run, modernized, or treated as illustrative.

## Main references

- `references/topic-map.md` contains the self-contained neural-network concept map, activation/loss/optimizer summaries, layer notes, training flow, and regularization map.
- `references/architecture-guide.md` contains the repo-grounded architecture summaries and code-snippet caveats for autoencoder, CNN, GAN, MLP, RNN, and VAE examples.
- `references/troubleshooting.md` covers conceptual mistakes, legacy source limitations, optional dependency issues, and docs-maintenance guidance.
- `scripts/activation_loss_demo.py` is a safe pure-Python toy script for activation and loss calculations.

## Fast routing

| Task | Use |
| --- | --- |
| Explain neuron/weights/bias/layers/weighted input | `topic-map.md` core concepts. |
| Explain forwardpropagation with matrices | `topic-map.md` forwardpropagation section and basics/math matrix cross-link. |
| Explain backpropagation | `topic-map.md` backpropagation section and basics/math chain-rule cross-link. |
| Compare ReLU, sigmoid, tanh, softmax, ELU, LeakyReLU | `topic-map.md` activation table and `activation_loss_demo.py`. |
| Compare MSE, cross-entropy, hinge, Huber, KL, MAE/RMSE | `topic-map.md` loss table; route formula-heavy basics to `../basics-and-math/SKILL.md`. |
| Explain optimizers or learning-rate adaptation | `topic-map.md` optimizer section. |
| Explain regularization: dropout, early stopping, L1/L2, augmentation, noise, ensembling | `topic-map.md` regularization section. |
| Compare neural architectures | `architecture-guide.md`. |
| Triage old PyTorch examples | `troubleshooting.md` and `architecture-guide.md` caveats. |

## Workflow for answers

1. Start with the computation graph: weighted input → activation → prediction → loss → gradient/backprop → optimizer update.
2. Link neural math back to foundations when necessary: dot products and matrix dimensions from `../basics-and-math/SKILL.md`.
3. Use examples at toy scale. The source repository was educational; do not imply full production training scripts.
4. For architecture comparisons, state input type, key layers/components, typical use, and source caveat.
5. If code is requested, use the bundled activation/loss demo or write a short self-contained snippet. Avoid requiring PyTorch unless the user explicitly asks for modern external code.
6. For documentation edits, preserve the beginner-first style and keep long code/training details outside glossary prose.

## Boundaries

This sub-skill owns:

- Neural-network teaching content and architecture summaries.
- Activation, layer, optimizer, regularization, and training-mechanics concepts.
- Caveats about original neural code snippets.

Route elsewhere:

- Calculus, linear algebra, gradient descent basics, logistic-regression log-loss derivations → `../basics-and-math/SKILL.md`.
- KNN, decision trees, SVM, random forests, boosting, regression variants, RL tabular methods → `../classical-algorithms/SKILL.md`.
- Datasets/libraries/papers/courses for neural learning → `../../references/resources-catalog.md`.
- Sphinx authoring/build issues → `../../references/site-maintenance.md` and root troubleshooting.

## Quality checks

- Distinguish conceptual snippets from runnable training code.
- Warn that some original architecture examples required PyTorch/torchvision, datasets, and training loops and were not selected as runtime checks.
- Do not say dropout is used at inference without explaining scaling/training-vs-test behavior.
- Do not confuse activation functions with loss functions or optimizers.
- For softmax, state that outputs form a probability distribution over mutually exclusive classes.
