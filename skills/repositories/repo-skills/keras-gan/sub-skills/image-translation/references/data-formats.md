# Data Formats for Image Translation

Validate dataset layout before importing Keras or starting any training loop. The
bundled helper performs the safe checks described here:

```bash
python sub-skills/image-translation/scripts/check_dataset_layout.py \
  --dataset-root datasets/<dataset_name> \
  --workflow {cyclegan,discogan,pix2pix} \
  --min-files 1 \
  --check-images
```

The command never downloads data and never trains.

## Common assumptions

- Images are RGB and are eventually resized to each workflow's `img_res`.
- Model loaders normalize pixel values from `[0, 255]` to `[-1, 1]` with
  `img / 127.5 - 1.0`.
- Supported extensions for layout checks are `.jpg`, `.jpeg`, `.png`, `.bmp`,
  `.gif`, `.tif`, `.tiff`, and `.webp`.
- Download scripts in the original project point to external Berkeley-hosted
  archives. Treat them as reference-only because they require network access and
  may change or disappear.

## CycleGAN unpaired layout

Use CycleGAN for unpaired domains where any image from A can be sampled with any
image from B.

Required for the default script path:

```text
datasets/apple2orange/
  trainA/  # domain A training images
  trainB/  # domain B training images
  testA/   # domain A sample/test images
  testB/   # domain B sample/test images
```

For a custom dataset such as `summer2winter_yosemite`, use the same folder names:

```text
datasets/summer2winter_yosemite/
  trainA/
  trainB/
  testA/
  testB/
```

CycleGAN loader behavior:

- `load_data(domain='A', is_testing=False)` reads `trainA`; with
  `is_testing=True` it reads `testA`. Domain B maps to `trainB`/`testB`.
- `load_batch(is_testing=False)` reads `trainA` and `trainB`.
- `load_batch(is_testing=True)` reads `valA` and `valB`, although the common
  CycleGAN archive layout uses `testA`/`testB`. If you need validation batches,
  either provide `valA`/`valB` as aliases/copies in a scratch dataset or adapt
  the loader to use `testA`/`testB`.
- The loader computes `n_batches = int(min(len(trainA), len(trainB)) / batch_size)`
  and then iterates `range(n_batches - 1)`. For a real train-loop smoke test,
  provide at least `2 * batch_size` images in each training domain.

The helper checks `trainA`, `trainB`, `testA`, and `testB` by default. It does
not require `valA`/`valB` for CycleGAN unless you add those checks yourself.

## DiscoGAN layout caveat

The README presents DiscoGAN as a cross-domain image translation workflow and
its download example uses `edges2shoes`. The actual bundled `discogan/data_loader.py`
uses paired side-by-side images in `train/` and `val/`, splitting each file into
left half A and right half B. It does **not** read `trainA`/`trainB` in the code
that ships with this repository.

For the source code as written, use:

```text
datasets/edges2shoes/
  train/  # side-by-side paired images; left half A, right half B
  val/    # side-by-side paired validation/sample images
```

DiscoGAN loader behavior:

- `load_data(is_testing=False)` reads `train`; with `is_testing=True` it reads
  `val`.
- `load_batch(is_testing=False)` reads `train`; with `is_testing=True` it reads
  `val`.
- Each file is split at `half_w = int(width / 2)` into `img_A = left half` and
  `img_B = right half`, then both halves are resized to `(128, 128)`.
- Like Pix2Pix, odd widths technically split but are a data-quality smell: one
  side gets one more column than the other before resizing.

If a caller expects a truly unpaired DiscoGAN dataset with
`trainA/trainB/testA/testB`, do not run the stock loader unchanged. Either route
to CycleGAN or adapt the DiscoGAN loader deliberately, documenting the change.

## DiscoGAN unpaired-reference layout

Some external DiscoGAN descriptions and production briefs refer to a CycleGAN-like
unpaired layout plus optional validation domains:

```text
datasets/<name>/
  trainA/
  trainB/
  testA/
  testB/
  valA/   # optional for validation-batch adaptations
  valB/   # optional for validation-batch adaptations
```

Use this layout only for an adapted unpaired DiscoGAN loader. The generated
helper currently validates the repository's stock `discogan/data_loader.py`
contract (`train/` and `val/` side-by-side images), because future agents should
not assume the original code supports domain folders it never reads.

## Pix2Pix paired side-by-side layout

Use Pix2Pix for paired conditional translation where each sample contains both
output A and conditioning input B in a single image.

Expected layout:

```text
datasets/facades/
  train/  # side-by-side images, left half A and right half B
  test/   # used by load_data(is_testing=True) and sample_images()
  val/    # used by load_batch(is_testing=True)
```

Pix2Pix loader behavior:

- `load_data(is_testing=False)` reads `train`; with `is_testing=True` it reads
  `test`.
- `load_batch(is_testing=False)` reads `train`; with `is_testing=True` it reads
  `val`.
- Every image is split vertically into `img_A = left half` and
  `img_B = right half`, then each half is resized to `(256, 256)` by the
  `Pix2Pix` class.
- Training pairs use B as condition and learn to generate A:
  `fake_A = generator(img_B)`.

Do **not** provide Pix2Pix data as separate `trainA` and `trainB` folders unless
you are also writing a custom loader. The stock Pix2Pix script will ignore those
folders and later fail with empty paths or missing split directories.

## Download script evidence and safe replacement

The original scripts do only archive download/extract/remove work:

- CycleGAN: `download_dataset.sh <name>` accepts names such as `apple2orange`,
  `summer2winter_yosemite`, `horse2zebra`, `monet2photo`, `facades`, and related
  CycleGAN datasets; it downloads `<name>.zip` from an external URL into
  `./datasets/`.
- DiscoGAN and Pix2Pix: `download_dataset.sh <name>` downloads `<name>.tar.gz`
  from an external Pix2Pix datasets URL into `./datasets/`.

Because those scripts require network and external archives, this generated
skill bundles a validator, not a downloader. If a user already has data, point
`--dataset-root` at the extracted dataset directory and validate it locally.
