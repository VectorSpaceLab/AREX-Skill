# Optimizers, losses, schedulers, initializers, and sample weights

River's `optim` module is used most directly by `linear_model` and `facto` estimators. Treat the optimizer/loss choice as part of the model configuration, not as a separate training loop concern.

## Which estimators use these objects

- `linear_model.LogisticRegression` accepts an `optim.base.Optimizer`, a `BinaryLoss`, `l1`, `l2`, `intercept_lr`, `clip_gradient`, and an initializer.
- `linear_model.LinearRegression` accepts an optimizer, a `RegressionLoss`, regularization, intercept settings, gradient clipping, and an initializer.
- `linear_model.SoftmaxRegression` accepts an optimizer, a `MultiClassLoss`, and `l2`.
- `linear_model.Perceptron` is a specialized hinge-loss linear classifier.
- `facto.*Classifier` and `facto.*Regressor` accept separate optimizers for linear weights, latent factors, and sometimes field-interaction weights.
- Tree, forest, naive Bayes, neighbors, and most wrappers do not use `optim` optimizers directly.

## Loss compatibility

| Task | Compatible River loss classes | Common estimator uses |
| --- | --- | --- |
| Binary classification | `optim.losses.Log`, `Hinge`, `BinaryFocalLoss` | `LogisticRegression`, binary `facto` classifiers |
| Multiclass classification | `optim.losses.CrossEntropy` | `SoftmaxRegression` |
| Regression | `Squared`, `Absolute`, `Huber`, `Quantile`, `Poisson`, `Cauchy`, `EpsilonInsensitiveHinge` | `LinearRegression`, `facto` regressors |

Do not pass a regression loss to a classifier or a binary loss to `SoftmaxRegression`. If you need multiclass behavior from a binary loss, wrap the binary classifier with a multiclass wrapper; if you need native normalized multiclass probabilities, use `SoftmaxRegression` with a multiclass loss.

## Optimizer selection cues

| Optimizer | Use when | Notes |
| --- | --- | --- |
| `SGD(lr=...)` | You want simple, transparent updates and can tune the learning rate | Often a good baseline; sensitive to feature scale |
| `AdaGrad` | Sparse features with rare but informative keys | Accumulates historical squared gradients; can slow down over time |
| `RMSProp` | Non-stationary dense streams where old gradients should decay | Uses a moving average rather than unbounded accumulation |
| `Adam`, `AMSGrad`, `AdaMax`, `Nadam` | You want adaptive steps with momentum-like behavior | Good defaults for many dense tasks; set `seed` only in the model/initializer if stochasticity matters |
| `AdaDelta`, `AdaBound` | You want adaptive learning without hand-picking a fixed scale or with a bounded final rate | More moving parts than SGD; smoke-test on a short stream |
| `Momentum`, `NesterovMomentum` | Smooth dense gradients and stable feature scale | Less robust to sparse disappearing features than adaptive optimizers in some workflows |
| `Newton` | Online Newton-style second-order updates | Can be sensitive to loss/scale assumptions |
| `FTRLProximal` | Sparse high-dimensional online logistic-style problems with regularization | Useful for ad/CTR-style problems and sparse dictionaries |
| `Averager(optimizer, start=...)` | You want Polyak/Ruppert-style averaged weights around an underlying optimizer | Wraps another optimizer |

## Learning-rate schedules

Optimizers accept either a number or a scheduler object.

```python
from river import linear_model, optim

model = linear_model.LogisticRegression(
    optimizer=optim.SGD(optim.schedulers.InverseScaling(learning_rate=0.05, power=0.5)),
    intercept_lr=optim.schedulers.InverseScaling(learning_rate=0.05, power=0.5),
)
```

Available scheduler classes include:

- `optim.schedulers.Constant(learning_rate)` for fixed step size.
- `optim.schedulers.InverseScaling(learning_rate, power=0.5)` for decay over iterations.
- `optim.schedulers.Optimal(loss, alpha=...)` for an optimal schedule tied to a loss and regularization strength.

The intercept uses its own schedule. Set `intercept_lr=0` to keep the intercept fixed. When comparing with scikit-learn SGD models, remember that River's intercept update is configured separately from the weight optimizer.

## Initializers

- `optim.initializers.Zeros()` is deterministic and safe for most linear baselines.
- `optim.initializers.Constant(value)` is useful for controlled tests.
- `optim.initializers.Normal(mu, sigma, seed)` is useful for latent factors and experiments where randomized initial weights should be reproducible.

Factorization machines have separate `weight_initializer` and `latent_initializer` parameters. If you compare factorization variants, set the estimator `seed` and stochastic initializers to make changes attributable to the configuration rather than random initial states.

## Regularization and clipping

Linear GLM estimators expose:

- `l2` for weight decay.
- `l1` for cumulative shrinkage to zero.
- `clip_gradient` to cap extreme gradient values.

Do not set nonzero `l1` and `l2` together for `LinearRegression`/`LogisticRegression`; the GLM base explicitly rejects the joint use of L1 and L2 penalties. If both sparsity and shrinkage are desired, choose one first and validate it on a stream before adding wrapper complexity.

## Safe sample-weight patterns

Single-instance GLM learning accepts `w=`:

```python
from river import linear_model, optim

model = linear_model.LogisticRegression(optimizer=optim.SGD(0.05))
model.learn_one({"amount": 10.0, "is_new": 1}, True, w=3.0)
```

Mini-batch GLM learning accepts scalar or per-row weights:

```python
model.learn_many(X, y, w=weights)
```

Many trees also accept keyword-only `w=` in `learn_one`, including Hoeffding tree classifiers/regressors and stochastic gradient trees. Some ensembles forward extra keyword arguments to base learners, but not every wrapped model supports weights. If you are not sure, check the concrete estimator signature before passing weights through a wrapper.

Practical rule:

1. If the final estimator is a GLM, pass `w=` directly.
2. If the final estimator is a tree, pass `w=` only to tree classes with a `learn_one(..., *, w=...)` signature.
3. If the final estimator is an ensemble or wrapper, verify that it forwards `**kwargs` and that the base learner accepts the same weight keyword.
4. If a dataset stream yields `(x, y, w)`, route the evaluation-loop mechanics to `streaming-evaluation` and keep the estimator-specific weight decision here.

## Optimizer/loss configuration examples

### Robust regression

```python
from river import linear_model, optim, preprocessing

model = preprocessing.StandardScaler() | linear_model.LinearRegression(
    optimizer=optim.Adam(0.02),
    loss=optim.losses.Huber(epsilon=1.0),
    intercept_lr=0.02,
    clip_gradient=100.0,
)
```

### Quantile regression

```python
from river import linear_model, optim, preprocessing

lower = preprocessing.StandardScaler() | linear_model.LinearRegression(
    optimizer=optim.SGD(0.03),
    loss=optim.losses.Quantile(alpha=0.05),
    intercept_lr=0,
)
upper = preprocessing.StandardScaler() | linear_model.LinearRegression(
    optimizer=optim.SGD(0.03),
    loss=optim.losses.Quantile(alpha=0.95),
    intercept_lr=0,
)
```

Use several quantile models when you need interval-style predictions. Evaluate each model with a metric appropriate to the downstream quantity; do not treat quantile predictions as calibrated probability intervals without checking coverage separately.

### Class imbalance in a binary linear classifier

```python
from river import linear_model, optim

model = linear_model.LogisticRegression(
    optimizer=optim.FTRLProximal(alpha=0.05, beta=1.0, l1=0.001, l2=1.0),
    loss=optim.losses.Log(weight_pos=5.0, weight_neg=1.0),
)
```

`Log(weight_pos=..., weight_neg=...)` changes the loss contribution for binary labels. It is different from passing per-sample `w=`; you can use either or both, but document why the imbalance correction belongs in the loss, the stream weights, or both.

### Native multiclass linear classifier

```python
from river import linear_model, optim, preprocessing

model = preprocessing.StandardScaler() | linear_model.SoftmaxRegression(
    optimizer=optim.Adam(0.01),
    loss=optim.losses.CrossEntropy(),
    l2=1e-4,
)
```

Use multiclass metrics for this model. Do not pass `optim.losses.Log`, because that is binary.

## Mini-batch cautions

`LinearRegression`, `LogisticRegression`, `BayesianLinearRegression`, and some wrappers implement mini-batch methods. Mini-batch behavior is designed to be consistent with River's data-frame boundary, but it is not always identical to a loop of `learn_one`; GLM mini-batches use a mean-gradient batch update. If exact row-by-row update semantics matter, use `learn_one` in your stream loop.

Mini-batch code requires an installed dataframe backend compatible with the estimator path. The common setup uses pandas, and River's optional pandas extra installs that dependency. Some current paths are backend-agnostic through narwhals when the corresponding eager backend is installed.
