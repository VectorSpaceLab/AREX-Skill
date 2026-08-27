# Augmentation and sampling troubleshooting

- **Invalid probability or transform type**: keep probability numeric in `[0,1]`
  and pass a `Transform`, list of transforms, or `Compose` as required by the
  loader. Test construction before iteration.
- **Unexpected batch size**: `n_augmentation=0` does not expand a batch;
  positive values add transformed blocks after clean originals. Check label
  tiling and reduce the value for memory.
- **Shape/device mismatch**: preserve `(batch, channels, time)`, move the
  transform/model/batch to the same device, and make sure labels remain aligned.
  Start on CPU when CUDA allocation is uncertain.
- **Sampler index errors or empty sequences**: check trial boundaries, sequence
  length/stride, metadata columns, and split membership. Enumerate the first
  few indices on a tiny fixture.
- **Negative `n_augmentation` or missing metadata**: reject the configuration;
  attach the expected window/description metadata or choose a plain loader.
- **Stochastic regression**: provide a seeded random state and compare shape and
  invariants rather than exact transformed values unless the operation is
  deterministic.
