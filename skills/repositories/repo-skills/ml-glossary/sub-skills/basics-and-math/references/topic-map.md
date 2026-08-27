# Basics and Math Topic Map

## Purpose

Read this for self-contained ML Glossary foundations: core term definitions, math concepts, linear/logistic regression, gradient descent, notation, and evaluation terms.

## Core glossary terms

| Term | Repo-grounded explanation |
| --- | --- |
| Accuracy | Percentage or fraction of predictions that are correct. Useful but can mislead with imbalanced classes. |
| Algorithm | A method or sequence of instructions used to learn or generate a model, such as linear regression, decision trees, SVMs, or neural networks. |
| Attribute | A quality describing an observation, equivalent to a column header in a spreadsheet. |
| Feature | An attribute-value representation used as model input. A feature vector is a row/list of feature values for one observation. |
| Label | The target answer in supervised learning. For flower classification, petal measurements are features and species is the label. |
| Observation / instance | One data point, row, or sample in a dataset. |
| Model | The learned representation of a dataset, often weights, biases, coefficients, support vectors, tree rules, or neural-network parameters. |
| Parameter | A value learned during training, such as linear-regression weights or neural-network weights. |
| Hyperparameter | A setting chosen before or around training, such as learning rate, number of iterations, tree depth, or hidden-layer count. |
| Bias term | A constant/intercept that lets a model represent patterns that do not pass through the origin. |
| Bias metric | Average difference between predictions and correct values; high bias often means underfitting. |
| Variance | How much predictions vary across training samples or model fits; high variance often means overfitting. |
| Overfitting | The model learns training noise/details too well and performs poorly on new/test data. |
| Underfitting | The model is too simple or poorly trained and performs badly on both training and test data. |
| Loss / cost | Numeric error signal used to judge predictions and update parameters. Lower is usually better unless the model overfit. |
| Convergence | Training state where loss changes very little between iterations. |
| Learning rate | Step size for parameter updates. Too high can overshoot; too low can make training slow. |
| Epoch | One pass over the entire training dataset. |
| Training set | Data used to fit/learn model parameters. |
| Validation set | Data used during training to tune choices and detect overfitting. |
| Test set | Held-out data used at the end to estimate generalization. |
| Classification | Predicting categorical outputs. Binary classification has two classes; multiclass has more than two. |
| Regression | Predicting continuous numeric outputs such as price or sales. |
| Categorical variable | Variable with discrete values; ordinal if order matters, nominal if it does not. |
| Continuous variable | Variable with values on a numeric scale. |
| Classification threshold | Probability cutoff for assigning a positive class, often 0.5 by default. |
| Confusion matrix | Table of true positives, true negatives, false positives, and false negatives. |
| Precision | Among positive predictions, how many were correct: TP / (TP + FP). |
| Recall / sensitivity / true positive rate | Among actual positives, how many were caught: TP / (TP + FN). |
| Specificity | Among actual negatives, how many were correctly rejected: TN / (TN + FP). |
| False positive rate | FP / (FP + TN), equivalently 1 - specificity. |
| ROC curve | Plot of true positive rate vs false positive rate over thresholds. |
| Null accuracy | Baseline accuracy from always predicting the most frequent class. |
| Normalization | Rescaling or restricting values so features/weights are comparable and training is easier. |
| Regularization | Technique to reduce overfitting by penalizing complexity or adding robustness. |
| Supervised learning | Training with labeled examples. |
| Unsupervised learning | Finding structure in unlabeled data, such as clusters. |
| Transfer learning | Reusing weights from a model trained on one task as a starting point for another. |
| Noise | Irrelevant randomness in data that obscures the pattern. |
| Outlier | Observation that deviates strongly from others. |
| Extrapolation | Predicting outside the observed data range; often risky. |
| Universal Approximation Theorem | A one-hidden-layer neural network can approximate continuous functions on a bounded range, but not magically generalize outside training support. |

## Math foundations

### Calculus

- A **derivative** is the instantaneous rate of change or the slope at a point.
- A numerical derivative can be approximated as `(f(x+h) - f(x)) / h` with very small `h`.
- ML uses derivatives in optimization: the sign and magnitude of a derivative tell how to adjust a parameter to reduce cost.
- The **chain rule** handles nested/composite functions. If `f(x) = A(B(x))`, then `df/dx = dA/dB * dB/dx`.
- A **gradient** is a vector of partial derivatives, one per input variable/parameter.
- Gradients point in the direction of greatest increase; gradient descent moves in the opposite direction.
- **Directional derivatives** measure slope along a chosen vector direction.
- **Integrals** compute area under a curve and support probability concepts such as probabilities over intervals, expected value, and variance for continuous variables.

### Linear algebra

- A **vector** is a one-dimensional array. In geometry it can represent magnitude and direction.
- A **matrix** is a rectangular grid with dimensions rows × columns.
- **Scalar operations** apply one number to every vector/matrix element.
- **Elementwise operations** combine matching positions; dimensions must match unless broadcasting applies.
- The **dot product** produces a scalar for two vectors and underlies matrix multiplication.
- The **Hadamard product** is elementwise multiplication.
- **Matrix transpose** swaps rows and columns, often written `X^T`.
- Matrix multiplication requires columns of the first matrix to equal rows of the second; an `(m,n)` times `(n,k)` product yields `(m,k)`.
- NumPy uses `np.dot(A, B)` or `A @ B` for matrix multiplication, and broadcasting allows operations when dimensions are equal or one side has size 1.

### Notation highlights

- `Δ` means change/difference.
- `Σ` means summation.
- `e` is Euler's number and appears in sigmoid/logistic formulas.
- `∇` (nabla) denotes gradient.
- `X^T` denotes transpose.
- `·` denotes dot product; `⊙` denotes Hadamard product.
- `P(A)` denotes probability of event A.
- `μ`, `σ²`, `σ`, `x̄`, and `s` represent mean/variance/standard-deviation statistics in common notation.

## Linear regression

Linear regression is supervised learning for continuous outputs. The simplest prediction equation is:

```text
y = m x + b
```

where `m`/weight is the learned slope and `b`/bias is the intercept. In multivariable regression, the prediction is a weighted sum of features:

```text
prediction = W1*x1 + W2*x2 + ... + Wn*xn + b
```

The repository's teaching example predicts sales from advertising spend. It uses mean squared error (MSE) as the cost function and gradient descent to update weights.

Key concepts:

- **Prediction**: compute weighted input plus bias.
- **Cost**: MSE averages squared differences between true and predicted values.
- **Gradient descent**: calculate partial derivatives of cost with respect to each weight/bias and subtract a learning-rate-scaled gradient.
- **Normalization**: important when feature ranges differ, especially in multivariable regression.
- **Vectorization**: matrix operations replace repeated loops for many features/observations.

## Logistic regression

Logistic regression is classification, not continuous regression. It starts with a linear weighted input `z`, then applies sigmoid:

```text
probability = 1 / (1 + e^(-z))
```

The output is a probability between 0 and 1. A decision boundary, often 0.5, maps probabilities to classes.

Key concepts:

- **Binary logistic regression** predicts probability of class 1.
- **Decision boundary** turns probabilities into labels.
- **Cross-entropy / log loss** is preferred over MSE for logistic regression because sigmoid makes MSE non-convex and harder to optimize.
- **Gradient** for logistic regression has a convenient form based on `(prediction - label) * feature`.
- **Multiclass logistic regression** can be framed as one-vs-rest binary tasks or as a softmax probability distribution over classes.

## Evaluation metrics bridge

- Use **accuracy** for balanced simple classification when all errors cost about the same.
- Use **precision** when false positives are costly.
- Use **recall** when false negatives are costly.
- Use **specificity/FPR** when negative-class behavior matters.
- Use **ROC** to inspect threshold tradeoffs.
- Always compare against **null accuracy** for imbalanced data.

## Probability/statistics status

The source probability and statistics pages were minimal placeholders. This runtime supports introductory definitions through notation, calculus-integral probability links, and glossary metrics, but do not claim a full probability/statistics curriculum is repo-grounded.
