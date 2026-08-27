# iGAN Data Formats and Artifacts

## Public HDF5 Dataset Inventory

The public dataset archives follow the URL pattern:

```text
http://efrosgans.eecs.berkeley.edu/iGAN/datasets/<dataset>.zip
```

Each ZIP is expected to contain `<dataset>.hdf5`. Use
`../scripts/igan_dataset_urls.py` for a dry-run table.

| Dataset | Domain | Resolution | Channels | Compressed size | Approximate source count |
| --- | --- | ---: | ---: | ---: | ---: |
| `outdoor_64` | outdoor natural images | 64 | 3 | 1.4 GB | 150K |
| `outdoor_128` | outdoor natural images | 128 | 3 | 5.5 GB | 150K |
| `church_64` | outdoor church images | 64 | 3 | 1.3 GB | 126K |
| `church_128` | outdoor church images | 128 | 3 | 4.6 GB | 126K |
| `shoes_64` | shoe product images | 64 | 3 | 260 MB | 50K |
| `shoes_128` | shoe product images | 128 | 3 | 922 MB | 50K |
| `handbag_64` | handbag product images | 64 | 3 | 774 MB | 137K |
| `handbag_128` | handbag product images | 128 | 3 | 2.8 GB | 137K |
| `sketch_shoes_64` | Photoshop shoe sketches | 64 | 1 | 76 MB | 50K |
| `sketch_shoes_128` | Photoshop shoe sketches | 128 | 1 | 278 MB | 50K |
| `hed_shoes_64` | HED shoe edges | 64 | 1 | 69 MB | 50K |
| `hed_shoes_128` | HED shoe edges | 128 | 1 | 244 MB | 50K |

Reserve more than the compressed size. During the legacy download flow, both
`<dataset>.zip` and `<dataset>.hdf5` may exist at the same time.

## HDF5 Layout

The legacy converter writes one dataset:

```text
imgs: uint8 array shaped (N, width, width, channel)
```

Expected dimension labels:

1. `batch`
2. `height`
3. `width`
4. `channel`

Expected file attribute:

```text
split: Fuel H5PYDataset split metadata with train and test sets
```

The split convention is:

```text
n_val = min(int(N * 0.05), 10000)
train imgs: [0, N - n_val)
test imgs:  [N - n_val, N)
```

For tiny fixtures, `int(N * 0.05)` can be zero, so the test split may be empty.
That is acceptable for planning but is not useful for monitoring training
quality.

## Directory Image Conversion Semantics

For `--mode dir`, the legacy converter:

- Reads file names from the top level of the image directory.
- Shuffles the file list with NumPy's process-global RNG.
- Reads each image with OpenCV in BGR color mode.
- Resizes to `(width, width)` using cubic interpolation.
- For `--channel 3`, converts BGR to RGB and reshapes to
  `(1, width, width, 3)`.
- For `--channel 1`, converts BGR to grayscale, inverts with `255 - gray`, and
  reshapes to `(1, width, width, 1)`.
- Concatenates all images into the `imgs` dataset.

The dry-run helper sorts file names for deterministic output and does not open
image pixels. Use it to catch count, naming, width, and channel issues before a
real conversion.

## MNIST and LMDB Modes

The converter also contains legacy branches for `mnist` and `lmdb`:

- `mnist` reads a raw byte file, skips the first 16 bytes, reshapes to
  `(60000, 28, 28, 1)`, and shuffles.
- `lmdb` requires the optional `lmdb` package, reads encoded images from an LMDB
  cursor, decodes with OpenCV, resizes, and appends to the image list.

Use these modes only when reproducing old experiments. For new custom data,
`dir` mode is easier to audit.

## Training Transform

Training code transforms stored images after loading:

- RGB datasets (`nc == 3`) are transposed from NHWC to NCHW, cast to float, and
  scaled from `[0, 255]` to `[-1, 1]`.
- Grayscale datasets (`nc == 1`) are transposed from NHWC to NCHW, cast to
  float, and scaled from `[0, 255]` to `[0, 1]`.
- RGB generator outputs use `tanh`; grayscale outputs use `sigmoid` and are
  inverted by the inverse transform for display.

A channel mismatch between the HDF5 file and the selected model config usually
fails during Theano graph execution or yields nonsensical samples.

## Cache Directory Layout

A training cache normally contains:

```text
<cache_dir>/
  samples/
    real_samples.png
    gen_00001.png
    ...
  models/
    disc_params
    gen_params
    disc_batchnorm
    gen_batchnorm
    predict_params
    predict_batchnorm
  log/
    training_log.ndjson
    training_predict_log.ndjson
  web_dcgan/
  rec/
  web_rec/
```

Not every file is mandatory. Predictor files exist only if predictor training
and predictor batchnorm were run.

## Packed Model Keys

The compact `.dcgan_theano` file is a pickle dictionary. The packer includes
available keys from:

```text
disc_params
gen_params
disc_batchnorm
gen_batchnorm
predict_params
predict_batchnorm
```

Downstream inference needs at least generator parameters and generator
batchnorm for normal sampling. Projection paths may require predictor keys.
Keep missing-key warnings visible instead of assuming a partial packed file is
complete.
