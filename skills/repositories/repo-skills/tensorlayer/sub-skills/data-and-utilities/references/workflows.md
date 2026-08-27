# Workflows

## Tiny affine transform

```python
import numpy as np
import tensorlayer as tl

img = np.zeros((8, 8, 3), dtype=np.uint8)
img[2:6, 2:6] = 255
matrix = tl.prepro.affine_rotation_matrix(angle=15)
out = tl.prepro.affine_transform_cv2(img, matrix)
```

Use this pattern when you need a deterministic shape-preserving preprocessing smoke.

## Tiny TFRecord round-trip

1. Generate a few tiny images or byte arrays in a temporary directory.
2. Write them to a TFRecord file with a label feature and a raw-bytes feature.
3. Read them back with `tf.data.TFRecordDataset` and parse the example.
4. Confirm the decoded batch shape and label values.

The bundled `scripts/smoke_tfrecord.py` follows this pattern without depending on the repo's sample data tree.

## Iteration helper check

When the task is about minibatches or sequence chunks, use the iterator helpers on synthetic arrays first. Keep the fixture small enough that the resulting batch order is easy to inspect.
