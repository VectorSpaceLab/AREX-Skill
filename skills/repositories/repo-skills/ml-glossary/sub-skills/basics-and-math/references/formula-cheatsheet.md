# Formula Cheatsheet

## Purpose

Read this when the user asks for formulas, derivations, or code-like steps for ML Glossary basics. Use it with `topic-map.md` for wording and caveats.

## Calculus essentials

### Numerical derivative

```text
derivative at x ≈ (f(x + h) - f(x)) / h
```

Use a very small `h`. This approximates the slope at a point. Exact symbolic derivatives are preferred when available.

### Chain rule

For `f(x) = A(B(x))`:

```text
df/dx = dA/dB * dB/dx
```

For deeper nesting, multiply each derivative along the chain. Backpropagation is repeated chain rule with memoized intermediate derivatives.

### Gradient

For a function with variables `x` and `z`:

```text
∇f(x,z) = [df/dx, df/dz]
```

Gradient descent updates parameters opposite the gradient because the gradient points toward greatest increase.

## Linear algebra essentials

### Dot product

```text
[a1, a2] · [b1, b2] = a1*b1 + a2*b2
```

### Matrix multiplication dimensions

```text
(m, n) @ (n, k) -> (m, k)
```

The inner dimensions must match. The result takes rows from the first matrix and columns from the second.

### Hadamard product

```text
A ⊙ B = elementwise multiplication
```

Use this for elementwise operations, not matrix multiplication.

## Linear regression

### Prediction

Simple regression:

```text
y_hat = weight * x + bias
```

Multivariable regression:

```text
y_hat = X @ W + b
```

where `X` is the feature matrix and `W` is a vector/matrix of weights.

### Mean squared error

```text
MSE = (1/N) * Σ_i (y_i - y_hat_i)^2
```

Some derivations use `1/(2N)` to make derivatives cleaner; both describe squared-error minimization with a constant scale difference.

### Simple-regression gradients

For `f(m,b) = (1/N) Σ(y_i - (m*x_i + b))^2`:

```text
df/dm = (1/N) * Σ -2*x_i*(y_i - (m*x_i + b))
df/db = (1/N) * Σ -2*(y_i - (m*x_i + b))
```

Update rule:

```text
m = m - learning_rate * df/dm
b = b - learning_rate * df/db
```

### Vectorized gradient

For feature matrix `X`, targets `y`, and predictions `p`:

```text
error = y - p
gradient = -X.T @ error / N
W = W - learning_rate * gradient
```

The source docs explain this as the matrix version of calculating one derivative per feature.

### Feature normalization

Mean normalization and scaling:

```text
for each feature column:
    feature = feature - mean(feature)
    feature = feature / (max(feature) - min(feature))
```

Use this when feature ranges differ greatly.

## Logistic regression

### Sigmoid

```text
sigmoid(z) = 1 / (1 + e^(-z))
```

Derivative:

```text
sigmoid'(z) = sigmoid(z) * (1 - sigmoid(z))
```

### Prediction

```text
z = X @ W + b
p(class=1) = sigmoid(z)
```

### Decision boundary

```text
if p >= threshold: class = 1
else: class = 0
```

The default threshold is often 0.5, but precision/recall tradeoffs may require another threshold.

### Binary cross-entropy / log loss

```text
loss = -(y*log(p) + (1-y)*log(1-p))
```

A confident wrong prediction is penalized heavily. Use small clipping such as `p = min(max(p, eps), 1-eps)` in code to avoid `log(0)`.

### Logistic gradient

For average loss over `N` examples:

```text
gradient = X.T @ (p - y) / N
W = W - learning_rate * gradient
```

The source docs point out the gradient looks similar to linear-regression MSE updates, but the prediction function is sigmoid-transformed and the loss is cross-entropy.

### Multiclass softmax

Softmax converts real-valued logits into probabilities that sum to 1:

```text
softmax(z_i) = exp(z_i) / Σ_j exp(z_j)
```

Use softmax for mutually exclusive multiclass classification. Use one-vs-rest logistic regression when explaining the repository's simpler procedure.

## Loss-function bridge

| Loss | Use | Formula sketch | Caveat |
| --- | --- | --- | --- |
| MSE / L2 | Regression | mean squared error | Sensitive to outliers; source linear-regression examples use it. |
| RMSE | Regression | sqrt(MSE) | Same unit as target. |
| MAE / L1 | Regression | mean absolute error | More robust to outliers; derivative less smooth at zero. |
| Cross-entropy / log loss | Classification probabilities | `-(y log p + (1-y) log(1-p))` | Clip probabilities in code. |
| Hinge | Margin classification/SVM-style | `max(0, margin)` variants | Repo loss snippet is illustrative. |
| Huber | Regression with outlier robustness | squared near zero, linear for large error | Needs delta threshold. |
| KL divergence | Distribution comparison | `Σ p log(p/q)` | Not symmetric. |

## Evaluation formulas

```text
accuracy = (TP + TN) / (TP + TN + FP + FN)
precision = TP / (TP + FP)
recall = TP / (TP + FN)
specificity = TN / (TN + FP)
false_positive_rate = FP / (FP + TN) = 1 - specificity
true_positive_rate = recall
```

Use these to explain threshold tradeoffs in logistic regression.

## Runnable bundled demo

The pure-Python script `../scripts/linear_logistic_demo.py` demonstrates:

```bash
python sub-skills/basics-and-math/scripts/linear_logistic_demo.py --mode linear
python sub-skills/basics-and-math/scripts/linear_logistic_demo.py --mode logistic
```

It is a runtime-owned replacement for legacy source snippets. It does not require NumPy, datasets, notebooks, or the original checkout.
