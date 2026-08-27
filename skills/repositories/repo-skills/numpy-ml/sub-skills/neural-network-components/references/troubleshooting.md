# Troubleshooting

## Import or version failures

- Python 3.10+ may fail at package import because this legacy snapshot imports
  `collections.Hashable`.
- NumPy 1.24+ may remove aliases used by some neural-network paths.
- Use the root compatibility guidance before debugging layer code.

## Shape mismatch in `forward` or loss calls

**Recovery checklist:**

1. Print the input batch shape before every layer.
2. Run one layer at a time.
3. Inspect the output shape before computing a loss.
4. Match target shape to loss expectations.
5. Avoid flattening or squeezing until you know which axis is the batch axis.

## Missing derived variables or cache state

Some backward/update paths require intermediate values stored during a previous
forward pass. If a backward call reports missing state, rerun `forward` with the
same object and check whether the method exposes a `retain_derived` or cache
control argument.

## Optimizer or scheduler confusion

Constructors often accept either strings or initialized helper objects in the
source. When in doubt, pass an explicit object such as `SGD(lr=0.01)` and verify
that the layer stores it before training.

## PyTorch/TensorFlow import errors

Those frameworks are comparison-test dependencies, not package runtime
requirements. Install them only when intentionally running original comparison
tests. Do not make a user install them just to use NumPy layer classes.

## Performance expectations

The package prioritizes legibility and educational value. Avoid using this
implementation for production-scale GPU training or benchmarking; use tiny
fixtures and clear shape assertions instead.
