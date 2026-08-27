# Training Experiments Troubleshooting

## Loader/model/loss arity mismatch

If `fit` raises because of a tuple length or target shape mismatch, check the loader first. The repository supports four different batch shapes:

- images + class labels
- image pairs + binary targets
- image triplets + empty target
- balanced batches + labels for online mining

## Scheduler warning

The repo's `fit` loop calls `scheduler.step()` in a way that newer PyTorch releases warn about. The bundled smoke accepts the warning because the goal is to verify the training contract, not to modernize the loop.

## Metric state leaks between passes

The metric objects are stateful. Always call `reset()` before reusing them in another smoke or epoch.

## Long notebook runs

The notebooks are for illustration and visualization. Do not use them as the only verification step; run the bundled tiny smoke instead.

## Download or network failures

The notebooks request MNIST/FashionMNIST downloads. If the network is unavailable, the generated skill's tiny smoke still verifies the core training loop.
