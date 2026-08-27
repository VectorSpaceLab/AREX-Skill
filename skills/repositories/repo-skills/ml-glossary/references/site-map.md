# Self-Contained Site Map

## Purpose

Read this when you need to understand what the ML Glossary repository covered without opening the original documentation, code, images, or notebook files. This reference converts the source tree into runtime-owned routes and notes which areas are complete, partial, or only placeholders.

## Repository purpose

ML Glossary, also branded in some files as ML Cheatsheet, is an educational Sphinx documentation project. Its goal is concise, visual explanations of machine-learning concepts with diagrams, code snippets, equations, citations, and links for deeper study. It is not an installable Python package and does not expose a stable public API.

## Content families

| Runtime owner | Source content represented | Self-contained coverage here |
| --- | --- | --- |
| Root skill | Project purpose, contribution loop, Sphinx docs build, resource catalogs, applications, datasets, libraries, papers, other content | Root routing plus `site-maintenance.md`, `resources-catalog.md`, `troubleshooting.md`, and scripts. |
| `basics-and-math` | Glossary, calculus, linear algebra, math notation, probability/statistics placeholders, gradient descent, linear regression, logistic regression, selected loss-function bridges | Topic map, formula cheatsheet, troubleshooting, and a runnable linear/logistic demo. |
| `classical-algorithms` | Classification algorithms, regression algorithms, clustering placeholders, reinforcement-learning overview, KNN/tree/random-forest code evidence | Algorithm topic map, caveats, KNN demo, and troubleshooting. |
| `neural-networks` | Neural-network concepts, forwardpropagation, backpropagation, activation functions, layers, loss functions, optimizers, regularization, architectures, illustrative PyTorch/NumPy code evidence | Topic map, architecture guide, activation/loss demo, and troubleshooting. |

## Original documentation topics distilled into this runtime

### Basics

- Linear regression: simple and multivariable regression, prediction equations, MSE cost, gradient descent, training loop, model evaluation, normalization, vectorized gradients, and bias term.
- Gradient descent: optimization by moving opposite the gradient, learning-rate tradeoffs, cost functions, and partial-derivative update steps.
- Logistic regression: classification probabilities, sigmoid activation, decision boundaries, binary log-loss/cross-entropy, vectorized gradient descent, class mapping, accuracy, multiclass one-vs-rest/softmax framing, and a scikit-learn comparison note.
- Glossary: definitions for accuracy, algorithm, attributes/features, bias/variance, categorical/continuous variables, classification threshold, confusion-matrix terms, convergence, epoch, extrapolation, feature selection/vector, gradient accumulation, hyperparameters, labels, loss, model, normalization, over/underfitting, precision/recall/specificity/FPR/TPR/ROC, regression, regularization, RL, supervised/unsupervised learning, transfer learning, training/test/validation set, and Universal Approximation Theorem.

### Math

- Calculus: derivatives as instantaneous slope, numerical derivative approximation, machine-learning use of derivatives, chain rule for composite functions, gradients and partial derivatives, directional derivatives, integral intuition, and probability expectations via integrals.
- Linear algebra: vectors, scalars, elementwise operations, dot products, Hadamard products, vector fields, matrices, dimensions, transpose, matrix multiplication rules, NumPy `dot`/`@`, and broadcasting.
- Notation: common symbols for algebra, calculus, linear algebra, probability, set theory, and statistics.
- Probability/statistics: mostly placeholders in the original, with enough notation and integral/probability links to support introductory explanations.

### Classical algorithms

- Classification: decision trees (ID3/C4.5/CART split criteria and feature support), KNN regression/classification procedure, logistic-regression route back to basics, random forests as tree ensembles, boosting as sequential focus on misclassified examples, and SVM linear/nonlinear hyperplane/kernel intuition.
- Regression algorithms: ordinary least squares, polynomial regression, lasso/L1, ridge/L2, and stepwise/spline regression.
- Clustering: named sections for centroid, density, distribution, hierarchical, K-means, and mean-shift were placeholders.
- Reinforcement learning: introductory agent/environment/state/action/reward/policy vocabulary, exploration vs exploitation, MDP framing, Monte Carlo methods, Q-learning/Q-table/epsilon-greedy, Deep Q-learning, and application/resource links. Several sections were TODO.

### Neural networks

- Concepts: neural network, neuron, synapse, weights, bias, layers, weighted input, activation functions, loss functions, optimizers, and gradient accumulation.
- Forwardpropagation: a simple one-hidden-layer network, matrix dimensions, weight and bias initialization, dynamic resizing with observations, matrix dot products, ReLU, and a refactored matrix feed-forward process.
- Backpropagation: chain-rule interpretation, derivatives of cost with respect to weights, layer error, memoization of derivatives, and the three-equation backward-pass summary.
- Activation functions: linear, ELU, ReLU, LeakyReLU, sigmoid, tanh, and softmax, with formulas, derivatives, pros/cons, and gradient caveats.
- Layers: BatchNorm, convolution, dropout, pooling, fully connected/linear, RNN, GRU, and LSTM concepts.
- Losses: cross-entropy/log loss, hinge, Huber, KL divergence, RMSE, MAE/L1, and MSE/L2.
- Optimizers: Adagrad, Adadelta, Adam, momentum, RMSProp, SGD; several others were placeholders.
- Regularization: data augmentation, dropout, early stopping, ensembling, injecting noise, L1, and L2.
- Architectures: autoencoder, CNN, GAN, MLP, RNN, and VAE descriptions with caveats that original code was illustrative.

### Resources and applications

- Applications: anomaly detection, computer vision classification/object detection/segmentation, natural-language dialog/machine translation/speech/text summarization/question answering, recommenders, and time series were mostly placeholder topic headings.
- Datasets: a broad public-dataset index grouped by domains such as agriculture, art, biology, climate, economics, finance, GIS, healthcare, image processing, machine learning, NLP, social networks, time series, transportation, and more.
- Libraries: a multilingual ML library catalog. The Python section included scikit-image, NLTK, spaCy, scikit-learn, XGBoost, TensorFlow, Theano, Keras-era libraries, MXNet, Gym, NumPy, SciPy, Pandas, matplotlib, statsmodels, PyMC, NetworkX, and others.
- Papers: a deep-learning paper list grouped by understanding, optimization/training, generative models, image/video, NLP, speech, RL, new papers, and classics.
- Other content: blogs, books, courses, podcasts, and tutorials.

## Source code evidence distilled

The `code/` tree was educational evidence, not a stable package. Important observations preserved in runtime guidance:

- Safe small example: KNN used `euclidean_distance`, `mean`, `mode`, and `KNN` over toy lists. A cleaned, self-contained version lives at `sub-skills/classical-algorithms/scripts/knn_demo.py`.
- Mostly parseable toy modules: activation functions, loss functions, `nn_matrix.py`, `nn_simple.py`, tree/random-forest classes, and several PyTorch architecture examples.
- Known legacy drift: `logistic_regression.py` and `logistic_regression_scipy.py` contain Python 2 print syntax; `optimizers.py` has a syntax issue; some snippets refer to missing imports, undefined variables, old APIs, or heavyweight optional libraries.
- Self-contained replacements: `linear_logistic_demo.py` and `activation_loss_demo.py` provide runnable educational equivalents for common tasks without relying on the original code files.

## Notebook evidence

The RNN notebook was effectively not useful as a runtime target. Neural-network RNN content is captured in the `neural-networks` references instead.

## How to use this map

- For conceptual answering, route to the relevant sub-skill; do not treat this file as the main manual.
- For maintenance tasks, combine this map with `site-maintenance.md` and `troubleshooting.md`.
- For verification or refresh decisions, compare current repo content with `repo-provenance.md` and the evidence categories above.
