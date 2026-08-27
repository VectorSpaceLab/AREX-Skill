# Safe Workflows for CycleGAN, DiscoGAN, and Pix2Pix

These workflows are designed for future agents using the generated skill tree.
They avoid network access, full training, and dependencies on the original
checkout.

## 1. Choose the image-translation workflow

Use this decision table first:

| Task/data | Use | Why |
|---|---|---|
| Unpaired domains with `trainA/trainB/testA/testB`, e.g. `apple2orange` or custom `summer2winter_yosemite` | CycleGAN | Stock loader reads separate A/B domain folders and trains dual generators with cycle and identity losses. |
| Paired side-by-side files in `train/val`, often `edges2shoes` | DiscoGAN as shipped | Stock loader splits each image into left A and right B, then trains two generators with direct translation and reconstruction objectives. |
| Paired side-by-side files in `train/test/val`, e.g. `facades` | Pix2Pix | Stock loader splits paired samples and trains a conditional generator B-to-A with L1 reconstruction weight 100. |
| Separate `trainA/trainB` folders intended for Pix2Pix | Do not use stock Pix2Pix | Convert to side-by-side paired images or write a custom loader. |
| MNIST samples, latent-vector image generation, super-resolution, inpainting, PixelDA | Sibling skill | Not part of this sub-skill. |

## 2. Validate dataset layout safely

From the generated repo skill root, run one of:

```bash
python sub-skills/image-translation/scripts/check_dataset_layout.py \
  --dataset-root datasets/apple2orange \
  --workflow cyclegan \
  --min-files 2 \
  --check-images
```

```bash
python sub-skills/image-translation/scripts/check_dataset_layout.py \
  --dataset-root datasets/edges2shoes \
  --workflow discogan \
  --min-files 2 \
  --check-images
```

```bash
python sub-skills/image-translation/scripts/check_dataset_layout.py \
  --dataset-root datasets/facades \
  --workflow pix2pix \
  --min-files 2 \
  --check-images
```

Use `--min-files 2` rather than the default `1` when planning even a one-batch
training smoke test, because the original `load_batch()` loops over
`range(n_batches - 1)` and yields zero batches for exactly one full batch.

Expected success signal:

```text
OK: <workflow> dataset layout looks usable at <dataset-root>
```

Expected failure signal: one or more `ERROR:` lines and nonzero exit status.
Warnings do not fail the command but should be reviewed.

## 3. Constructor/import smoke checks

Only run these in a compatible legacy Keras environment. Do not run them as the
first validation step; dataset layout errors are faster and safer to catch with
the bundled helper.

Because the original scripts import a local `data_loader.py` by bare module
name, the safest pattern for a copied/adapted script is to run from the workflow
script directory or temporarily add that directory to `PYTHONPATH`.

Minimal constructor expectations:

```python
# CycleGAN
from cyclegan import CycleGAN
gan = CycleGAN()
assert gan.dataset_name == 'apple2orange'
assert gan.img_shape == (128, 128, 3)
assert gan.disc_patch == (8, 8, 1)
assert hasattr(gan, 'g_AB') and hasattr(gan, 'g_BA')

# DiscoGAN
from discogan import DiscoGAN
gan = DiscoGAN()
assert gan.dataset_name == 'edges2shoes'
assert gan.img_shape == (128, 128, 3)
assert gan.disc_patch == (8, 8, 1)
assert hasattr(gan, 'd_A') and hasattr(gan, 'd_B')

# Pix2Pix
from pix2pix import Pix2Pix
gan = Pix2Pix()
assert gan.dataset_name == 'facades'
assert gan.img_shape == (256, 256, 3)
assert gan.disc_patch == (16, 16, 1)
assert hasattr(gan, 'generator') and hasattr(gan, 'discriminator')
```

If adapting these snippets into tests, do not include machine-specific Python
paths or environment names in public reports.

## 4. Adapting dataset names and resolutions

The classes hard-code `dataset_name`, resolution, and `DataLoader` construction
inside `__init__`. For a clean adaptation, parameterize rather than editing many
sites by hand:

```python
class CycleGAN(object):
    def __init__(self, dataset_name='apple2orange', img_rows=128, img_cols=128):
        self.img_rows = img_rows
        self.img_cols = img_cols
        self.channels = 3
        self.img_shape = (self.img_rows, self.img_cols, self.channels)
        self.dataset_name = dataset_name
        self.data_loader = DataLoader(dataset_name=self.dataset_name,
                                      img_res=(self.img_rows, self.img_cols))
        patch = int(self.img_rows / 2**4)
        self.disc_patch = (patch, patch, 1)
```

Apply the same idea to DiscoGAN and Pix2Pix. Keep these invariants:

- `img_shape` must match the resize output of the loader.
- `disc_patch` must be recomputed after resolution changes.
- Pix2Pix side-by-side source images should have enough width for both halves;
  after splitting, each half is resized to `img_res`.
- If changing Pix2Pix direction, update both comments and training targets. The
  stock script conditions on B and generates A.

## 5. Bounded sampling workflow

A safe image-sampling workflow after a successful constructor smoke and with
weights already loaded or after a deliberately tiny training run:

1. Validate the dataset split used by `sample_images()`:
   - CycleGAN: `testA` and `testB`.
   - DiscoGAN: `val` side-by-side images.
   - Pix2Pix: `test` side-by-side images.
2. Ensure the process working directory is the workflow runtime directory, or
   adapt paths so `images/<dataset_name>/` resolves to a scratch output folder.
3. Call `sample_images(epoch=0, batch_i=0)`.
4. Check for a PNG named `images/<dataset_name>/0_0.png`.

Do not claim sample quality from this check. It only proves pathing, loader,
model prediction, Matplotlib, and output writing.

## 6. Download replacement workflow

If a user asks to download `apple2orange`, `edges2shoes`, or `facades`, explain
that the original repository used external archives and that this generated skill
intentionally does not bundle a downloader. Ask the user to provide an already
extracted dataset root or explicitly authorize network access in a separate
workflow. Once data exists locally, run the validator.

