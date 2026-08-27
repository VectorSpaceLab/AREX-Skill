# API Reference

## Verified helpers

These package facts were checked during skill construction:

- `load_mnist_dataset(shape=(-1, 784), path='data')`
- `load_cifar10_dataset(shape=(-1, 32, 32, 3), path='data', plotable=False)`
- `save_weights_to_hdf5(filepath, network)`
- `save_npz(filepath, network)`
- `load_npz(path=None, name=None)`
- `load_and_assign_npz(filepath, network)`
- `affine_transform_cv2(x, transform_matrix, flags=None, border_mode='constant')`
- `affine_rotation_matrix(angle=(-20, 20))`
- `affine_transform_keypoints(coords, transform_matrix)`
- `minibatches(inputs, targets, batch_size, shuffle=False)`

## Practical notes

- Dataset loaders may download data or expect a local data directory.
- Preprocessing helpers usually accept NumPy images and return transformed arrays.
- Visualization helpers are useful for confirming tensor/image shape and layout, but bundled smoke scripts should remain headless-safe.

## Evidence summary

This page distills TensorLayer's file save/load tests plus preprocessing and TFRecord tutorials into the verified helper map above. Runtime instructions rely on bundled smoke scripts rather than source-checkout examples.
