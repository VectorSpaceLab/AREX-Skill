---
name: deep-learning
description: "Assemble and debug ML-From-Scratch NeuralNetwork, layers,
  activations, losses, optimizers, MLP/CNN/RNN, and generative model-building
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# deep-learning

Use this sub-skill when a task involves ML-From-Scratch's neural-network framework: `NeuralNetwork`, deep-learning layers, activation/loss/optimizer selection, MLP/CNN/RNN model assembly, or advanced generative model builders.

## Route here for

- Building or debugging `NeuralNetwork(optimizer, loss, validation_data=None)` workflows.
- Selecting and ordering layers such as `Dense`, `Activation`, `Dropout`, `Flatten`, `Conv2D`, pooling, `BatchNormalization`, `RNN`, `Reshape`, and `UpSampling2D`.
- Choosing optimizers, losses, and activations for small CPU examples.
- Diagnosing shape errors in MLP, CNN, RNN, autoencoder, GAN, or DCGAN-style builders.
- Creating a tiny CPU smoke check that imports the installed package and performs one deterministic epoch.

## Route away

- Classical supervised estimators such as tree, regression, SVM, Naive Bayes, perceptron, or GMM classifier workflows: use `supervised-learning`.
- Clustering, dimensionality reduction, association mining, and non-neural unsupervised estimators: use `unsupervised-learning`.
- Gym environment loops, replay memory, epsilon decay, CartPole training/play loops, and DQN compatibility: use `reinforcement-learning`. This sub-skill only covers the neural model-builder portion.

## Operating procedure

1. Treat the installed `mlfromscratch` package as the runtime source of truth. Do not require source-checkout reads or original demo scripts during user work.
2. Start with the framework contracts in [references/api-reference.md](references/api-reference.md), especially input shape conventions and exact constructor names.
3. Use [references/workflows.md](references/workflows.md) for MLP, CNN, RNN, autoencoder, GAN/DCGAN, and fast validation recipes.
4. If a user reports an exception or unexpected output, diagnose from [references/troubleshooting.md](references/troubleshooting.md) before changing model code.
5. For quick environment validation, run one of the bundled scripts:
   - `python scripts/run_mlp_smoke.py`
   - `python scripts/run_cnn_smoke.py`

## High-signal rules

- The first shape-bearing layer must receive `input_shape` without the batch dimension: e.g. `Dense(..., input_shape=(n_features,))`, `Conv2D(..., input_shape=(channels, height, width))`, or `RNN(..., input_shape=(timesteps, input_dim))`.
- `CrossEntropy` expects one-hot encoded targets with the same final class dimension as the network output. For multiclass classification, finish with `Dense(n_classes)` then `Activation('softmax')`.
- The framework expects channels-first image batches for convolution: `(n_samples, channels, height, width)`, not channels-last.
- Add transform layers in data-flow order: shape-bearing first layer, activation after affine/convolution/recurrent output, `Flatten()` before dense layers after image-like tensors.
- Full demos can be slow and plot by default. Prefer the bundled smokes or reduce epochs/sample counts and set a headless Matplotlib backend before importing plotting libraries.
