# Global Histogram API Reference

## Purpose

Read this for the Caffe classes, method signatures, blob names, and artifact roles used by the global histogram transfer workflow.

## Wrapper class

### `ColorizeImageCaffeGlobDist(Xd=256)`

This class extends the Caffe local-hints wrapper with one additional global histogram input. It inherits image loading, Lab conversion, and full-resolution output helpers from the Caffe/base colorization classes.

Important attributes and methods from source inspection:

| Item | Meaning |
| --- | --- |
| `glob_mask_mult = 1.` | Value written to the last entry of the global blob when a histogram is supplied. |
| `glob_layer = 'glob_ab_313_mask'` | Caffe blob receiving the 313-bin distribution plus a mask/enabled flag. |
| `net_forward(input_ab, input_mask, glob_dist=-1)` | Runs colorization without global conditioning when `glob_dist` is `-1`, or with conditioning when a distribution vector is supplied. |
| `get_img_fullres()` | Returns the full-resolution RGB prediction after a forward pass. |
| `get_img_gray_fullres()` | Returns the full-resolution grayscale RGB image for comparison. |

When `glob_dist` is `-1`, the wrapper sets all entries of `glob_ab_313_mask` to zero. When a histogram is supplied, it writes the distribution into all but the last channel and writes `glob_mask_mult` to the final channel.

## Global statistics network

The notebook constructs a separate Caffe net from:

- `models/global_model/global_stats.prototxt`
- `models/global_model/dummy.caffemodel`

The reference image is loaded with `caffe.io.load_image`, resized to `(Xd, Xd)`, converted to uint8 BGR channel order, and written into blob `img_bgr`.

After `gt_glob_net.forward()`, the notebook reads:

```python
glob_dist_ref = gt_glob_net.blobs["gt_glob_ab_313_drop"].data[0, :-1, 0, 0].copy()
```

The `[:-1]` slice removes the mask/enabled channel, leaving the 313-bin global distribution expected by `ColorizeImageCaffeGlobDist.net_forward`.

## Model/prototxt roles

| File | Used by | Role |
| --- | --- | --- |
| `models/global_model/deploy_nodist.prototxt` | `ColorizeImageCaffeGlobDist.prep_net` | Global colorization network definition. |
| `models/global_model/global_model.caffemodel` | `ColorizeImageCaffeGlobDist.prep_net` | Weights for global histogram-conditioned colorization. |
| `models/global_model/global_stats.prototxt` | `caffe.Net` global stats model | Reference-image distribution extraction network. |
| `models/global_model/dummy.caffemodel` | `caffe.Net` global stats model | Dummy weights paired with global stats prototxt. |

## Data shape expectations

- `input_ab`: NumPy array shaped `2 x Xd x Xd`.
- `input_mask`: NumPy array shaped `1 x Xd x Xd`.
- `glob_dist`: vector compatible with the 313 in-gamut color bins before the wrapper appends/enables the mask channel.
- Reference image for `gt_glob_net`: resized to `Xd x Xd`, converted to uint8, BGR channel order, transposed to `3 x Xd x Xd`.

## Native execution gate

Do not run or claim global histogram transfer from static Python dependencies alone. Required runtime pieces are PyCaffe, the global model weights, the dummy stats weights, and a valid target/reference image pair.
