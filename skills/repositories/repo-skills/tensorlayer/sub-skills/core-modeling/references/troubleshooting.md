# Troubleshooting

## Import issues

### `import tensorlayer` fails because `matplotlib` is missing

The current package import reaches `tensorlayer.app`, so `matplotlib` is part of the practical runtime set. Install it and retry.

### TensorFlow is missing or mismatched

The model API expects TensorFlow 2.x. Confirm the active environment has a compatible TensorFlow build before debugging TensorLayer itself.

## Model construction issues

### `ValueError` from duplicate names

TensorLayer tracks model names. If you reuse a name, choose a new one or allow auto-naming.

### Static and dynamic patterns are mixed up

Static models start from `Input(...)`. Dynamic models need `forward(...)` and usually specify `in_channels` for layers created in `__init__`.

### NumPy legacy alias errors

If a layer or native test fails with `np.float` or `np.math` missing, you are seeing an old TensorLayer compatibility path. Use a TensorFlow-compatible NumPy 1.x stack or a short import-time alias shim for native tests.

## Serialization issues

### Save/load format mismatch

Use the same save/load path and format on both sides. The bundled smoke uses `tl.files.save_weights_to_hdf5` and normalizes HDF5 attrs before load because the current h5py/TensorLayer combo stores string attrs in a way the raw loader does not like. Keep the round-trip small and deterministic.

### Nested or Lambda models reload poorly

Nested models and Lambda layers are more brittle than weight-only persistence. Keep the round-trip small and deterministic, and treat full graph serialization as an edge workflow.

## Pretrained constructor issues

### `pretrained=True` tries to fetch external weights

That is expected. Bundled checks should stay on `pretrained=False` so they are safe and offline.
