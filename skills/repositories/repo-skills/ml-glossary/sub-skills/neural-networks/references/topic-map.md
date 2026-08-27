# Neural Networks Topic Map

## Purpose

Read this for self-contained ML Glossary neural-network explanations: core concepts, forwardpropagation, backpropagation, activations, layers, losses, optimizers, regularization, and training vocabulary.

## Core concepts

| Concept | Repo-grounded explanation |
| --- | --- |
| Neural network | A model that passes inputs through layers of weighted functions and nonlinear activations to produce predictions. Training iteratively reduces error. |
| Neuron | Takes weighted inputs, adds bias, applies an activation function, and outputs a value. |
| Synapse | Connection between input/neuron/output nodes; each connection has a weight. |
| Weight | Learned value controlling how much an input influences the next computation. |
| Bias | Learned/additional constant added before activation to shift outputs and avoid forcing patterns through the origin. |
| Layer | Group of neurons or operations. Input layers hold data; hidden layers transform it; output layers produce predictions. |
| Weighted input | Sum or matrix product of inputs and weights, often `Z = XW + b`. |
| Activation function | Nonlinear transformation applied to weighted input, enabling complex relationships. |
| Loss function | Numeric error signal comparing predictions to targets. |
| Optimizer | Update rule that changes weights using loss gradients. |
| Gradient accumulation | Splits a large batch into smaller mini-batches, accumulates gradients, then applies one update equivalent to a larger batch. |

## Prediction and training flow

1. **Forwardpropagation**: compute predictions by moving data forward through layers.
2. **Loss calculation**: compare prediction with target.
3. **Backpropagation**: use chain rule to compute derivatives of loss with respect to each weight.
4. **Optimizer update**: adjust weights in the direction that reduces loss.
5. Repeat until validation or training criteria indicate convergence, early stopping, or another stop condition.

## Forwardpropagation

For a simple one-hidden-layer network:

```text
Prediction = A(A(X * W_hidden) * W_output)
```

where `A` is an activation function. In matrix form:

```text
Z_hidden = X @ W_hidden + b_hidden
H = activation(Z_hidden)
Z_output = H @ W_output + b_output
O = activation_or_identity(Z_output)
```

Important dimension rule: if `X` has shape `(num_examples, input_features)` and the hidden layer has `hidden_units`, then `W_hidden` has shape `(input_features, hidden_units)` and `H` has shape `(num_examples, hidden_units)`.

Dynamic resizing insight from the source: changing the number of observations changes the number of rows in layer activations, but not the weight-matrix column counts fixed by architecture.

## Backpropagation

Backpropagation computes how much each weight contributed to the final error. It is repeated chain rule through the nested forward computation.

For a single neuron-style path:

```text
Cost = C(R(Z(XW)))
dCost/dW = C'(prediction) * R'(Z) * X
```

For a layer:

```text
output_layer_error = (prediction - target) * activation_prime(Z_output)
hidden_layer_error = output_layer_error @ W_output.T * activation_prime(Z_hidden)
dCost/dW_layer = previous_layer_activation.T @ current_layer_error
```

The source emphasized memoization: once a layer error is computed, reuse it while moving backward instead of recomputing the full derivative chain.

## Activation functions

| Activation | Formula / behavior | Pros | Caveats |
| --- | --- | --- | --- |
| Linear | `f(z) = m*z` | Simple, unbounded, useful for regression output layers. | Constant derivative; stacking linear activations stays linear. |
| ELU | `z` if positive, `alpha*(e^z - 1)` if negative | Smooth negative side, can produce negative outputs. | Positive side unbounded; alpha choice matters. |
| ReLU | `max(0,z)` | Cheap, reduces vanishing-gradient issues, common hidden activation. | Dead ReLU risk when units stay at zero for negative inputs; unbounded positive side. |
| LeakyReLU | `z` if positive, `alpha*z` if negative | Keeps small gradient for negative values. | Benefit varies by task; alpha choice matters. |
| Sigmoid | `1/(1+e^-z)` | Outputs `(0,1)`, useful for binary probability output. | Saturation and vanishing gradients; not zero-centered. |
| Tanh | `(e^z-e^-z)/(e^z+e^-z)` | Outputs `[-1,1]`, zero-centered. | Still can vanish in saturated regions. |
| Softmax | `exp(z_i)/sum_j exp(z_j)` | Converts logits to class-probability distribution. | Use for mutually exclusive multiclass outputs; use stable implementation in real code. |

Use `../scripts/activation_loss_demo.py` for a pure-Python demonstration.

## Layers

| Layer / component | Explanation | Notes |
| --- | --- | --- |
| BatchNorm | Normalizes batch activations to reduce internal covariate shift and accelerate convergence. | Uses batch mean/std; training and inference behavior differ in real frameworks. |
| Convolution | Applies kernels/filters across local input regions with a stride to produce feature maps. | Core CNN operation for images/audio/grids. |
| Dropout | Randomly sets a fraction of activations to zero during training to reduce co-adaptation. | Not used the same way at inference; scaling matters. |
| Pooling | Reduces spatial dimensions, commonly max or average pooling over windows. | Helps reduce parameters/overfitting and capture local invariance. |
| Fully connected / linear | Every input connects to every output unit. | Common final classifier/regressor layers. |
| RNN | Recurrent layer with hidden state that carries information across timesteps. | Useful for sequences but can struggle with long-term dependencies. |
| GRU | Gated recurrent unit with reset and update gates. | Simplifies gating compared with LSTM. |
| LSTM | Recurrent unit with memory cell and gates for long-term information. | Addresses longer-term dependencies better than vanilla RNN. |

## Loss functions

| Loss | Use | Caveat |
| --- | --- | --- |
| Cross-entropy / log loss | Classification probability outputs. | Clip probabilities or use framework-stable implementations. |
| Hinge | Margin-based classification. | Often associated with SVM-style objectives. |
| Huber | Regression with outlier robustness. | Delta threshold defines squared vs linear region. |
| KL divergence | Distribution mismatch. | Asymmetric; use with valid distributions. |
| RMSE | Regression, interpretable in target units. | Inherits MSE outlier sensitivity. |
| MAE / L1 | Regression robust to outliers. | Less smooth at zero. |
| MSE / L2 | Regression and simple neural examples. | Penalizes large errors strongly; not ideal for logistic classification probabilities. |

## Optimizers

| Optimizer | Repo-grounded idea | Caveat |
| --- | --- | --- |
| SGD | Updates parameters using gradients from samples/mini-batches rather than necessarily full data. | Noisier path but cheaper for large data. |
| Momentum | Uses exponentially weighted average of past gradients to reduce oscillation and speed convergence. | Momentum coefficient must be tuned. |
| Nesterov momentum | Placeholder-level in source. | Do not overstate repo coverage. |
| Adagrad | Adapts learning rates based on accumulated squared gradients. | Learning rate can shrink too much over time. |
| Adadelta | Uses moving window of gradient updates to avoid Adagrad's ever-growing accumulator. | Source gives conceptual formula, not full runtime API. |
| Adam | Combines momentum-like first moment and RMSProp-like second moment with bias correction. | Hyperparameters still matter. |
| RMSProp | Uses moving average of squared gradients to scale updates. | Common in neural optimization; details are framework-dependent. |
| BFGS / conjugate gradients / Newton's method | Named or placeholder in source. | Treat as optimizer vocabulary unless user asks for external detail. |

## Regularization and training controls

| Technique | Explanation | When useful |
| --- | --- | --- |
| Data augmentation | Generates modified training data to improve robustness, such as image jitter/flips or NLP word perturbations. | Small datasets, CV/NLP tasks. |
| Dropout | Randomly drops activations during training. | Reduces co-adaptation/overfitting in neural networks. |
| Early stopping | Stops training when validation performance worsens. | Avoids overfitting without training many models to completion. |
| Ensembling | Combines models, via bagging/boosting/voting/averaging. | Improves stability or performance; bridge to classical algorithms. |
| Injecting noise | Adds noise to inputs, weights, or outputs during training. | Reduces memorization and improves robustness. |
| L1 regularization | Adds absolute-weight penalty; can encourage sparsity. | High-dimensional features, feature selection. |
| L2 regularization | Adds squared-weight penalty; shrinks coefficients. | Multicollinearity and overfitting control. |
| Gradient accumulation | Accumulates gradients over mini-batches before updating. | Large effective batch when memory is limited. |

## Cross-links to basics

- Weighted input `XW + b` is the same linear algebra foundation as linear regression.
- Sigmoid output and cross-entropy are shared with logistic regression.
- Backpropagation relies on calculus chain rule and gradients.
- Matrix dimension errors are usually linear-algebra errors; use `../../basics-and-math/references/formula-cheatsheet.md`.
