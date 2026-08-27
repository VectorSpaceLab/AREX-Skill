# Workflows

## Tiny component smoke

```python
import numpy as np
from numpy_ml.neural_nets.activations import ReLU
from numpy_ml.neural_nets.layers import FullyConnected
from numpy_ml.neural_nets.losses import SquaredError
from numpy_ml.neural_nets.optimizers import SGD

x = np.ones((2, 2))
act = ReLU()
print(act.fn(np.array([-1.0, 2.0])))

layer = FullyConnected(3, act_fn='ReLU', optimizer=SGD(lr=0.01))
out = layer.forward(x)
print(out.shape)

loss = SquaredError().loss(np.ones((2, 1)), np.zeros((2, 1)))
print(loss)
```

Use this as a first sanity check before attempting a multi-layer network.

## Building a small layer stack

1. Choose input shape and batch axis explicitly.
2. Instantiate layers with explicit activation and optimizer choices.
3. Call `forward(...)` on a tiny batch and inspect output shapes before adding
   losses or backpropagation.
4. Add a loss only after the layer shapes match the target shape.
5. Add backward/update logic in the same order the package examples and source
   methods require; do not assume PyTorch-style autograd.

## Toy model route

The package includes educational toy models such as Bernoulli VAE, WGAN-GP, and
Word2Vec. Treat them as source-backed reference implementations. Keep data
synthetic or very small, avoid long training runs in validation, and route text
preprocessing to the preprocessing sub-skill when preparing corpora for
Word2Vec-like tasks.

## Optional comparison tests

The repository contains comparison tests against PyTorch, TensorFlow, SciPy, or
scikit-learn. Use those tests only in a separately approved test environment.
The base runtime and bundled smoke do not install those heavy dependencies.
