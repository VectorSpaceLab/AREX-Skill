# Dataset-Sampling API Reference

## `SiameseMNIST`

- Input: a MNIST-like dataset object.
- Training mode:
  - picks a random positive or negative pair for the requested index
  - returns `(img1, img2), target`
- Test mode:
  - builds a deterministic list of fixed pairs
  - returns `(img1, img2), target`

## `TripletMNIST`

- Input: a MNIST-like dataset object.
- Training mode:
  - picks one positive and one negative example for each anchor
  - returns `(img1, img2, img3), []`
- Test mode:
  - builds a deterministic list of fixed triplets
  - returns `(img1, img2, img3), []`

## `BalancedBatchSampler`

- Input: label tensor, number of classes per batch, number of samples per class.
- Output: a list of indices containing `n_classes × n_samples` items.
- Notes:
  - classes are sampled without replacement inside each batch
  - the sampler reshuffles class indices when it runs out of examples
  - the batch size is fixed by the constructor arguments

## Fixture expectations

- Labels should be a 1D tensor of class ids.
- Image tensors should be grayscale `28×28` values before PIL conversion.
- A no-download smoke can use a tiny fake MNIST-like object with six samples and three classes.
