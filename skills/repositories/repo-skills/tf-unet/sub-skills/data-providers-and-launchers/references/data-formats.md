# Data formats

## Provider shape contract

Every provider in this package produces tensors shaped like this:

- Data: `[n, nx, ny, channels]`
- Labels: `[n, nx, ny, n_class]`

The package uses `nx`/`ny` for the spatial axes and `channels` for the feature axis.

## Base provider behavior

`BaseDataProvider`:

- clips the absolute value of the input data to the configured range,
- subtracts the minimum,
- rescales to `0..1` when the data has a non-zero maximum,
- converts binary labels into two-channel one-hot arrays when `n_class == 2`,
- leaves multi-class labels unchanged when `n_class > 2`.

That last point matters for synthetic fixtures: a 2-class `SimpleDataProvider` workflow should provide a binary mask, while a multi-class `SimpleDataProvider` workflow can provide one-hot labels directly.

## `SimpleDataProvider`

- Input: NumPy arrays already shaped like `[n, nx, ny, channels]` and `[n, nx, ny, n_class]`.
- Use it when you already have arrays in memory and only want the package's provider contract.
- For binary segmentation, prefer a mask-style label and let the base provider expand it to two classes.
- For multi-class segmentation, pass one-hot labels directly.

## `ImageDataProvider`

- Input: a glob pattern for image files, such as a synthetic or curated `*.tif` set.
- It pairs each image with a mask file by replacing the configured data suffix with the mask suffix.
- Default suffixes are `.tif` for data and `_mask.tif` for labels.
- The first file pair determines `channels` and `n_class`.
- The repo's launcher workflows expect even-sized images and matching mask dimensions.

## Toy generators

### `GrayScaleDataProvider`

- Produces one-channel synthetic images with circles.
- Parameters: `nx`, `ny`, and optional shape controls such as `cnt`, `r_min`, `r_max`, `border`, and `sigma`.
- `rectangles=True` turns the toy example into a 3-class segmentation problem.

### `RgbDataProvider`

- Produces a 3-channel RGB version of the synthetic toy data.
- Uses the same shape controls as `GrayScaleDataProvider`.
- Useful when you want to test color-image handling without external data.

## Launcher-style HDF5 patterns

The dataset-specific launcher workflows in this package follow these evidence-backed layouts:

- RFI chunk workflow: HDF5 groups or datasets named `data` and `mask`.
- UFIG workflow: an `image` dataset plus `segmaps/galaxy` and `segmaps/star` datasets.
- Ultrasound workflow: paired TIFF image and mask files in the same directory.

Treat these as format patterns to reproduce in synthetic fixtures or private datasets, not as bundled assets.

## Display helpers

- `util.to_rgb(...)` converts grayscale or multi-channel arrays into display-friendly RGB output.
- `util.combine_img_prediction(...)` concatenates input, ground truth, and prediction for visual inspection.
- `util.save_image(...)` writes the resulting RGB snapshot as a JPEG.
