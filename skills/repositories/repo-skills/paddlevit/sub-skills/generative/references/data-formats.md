# GAN data and tensor formats

## Common image contract

The source data adapters return image tensors in Paddle's channel-first form
`[C,H,W]`; a batch is `[B,3,H,W]`. Pillow/OpenCV arrays at file boundaries are
normally RGB/HWC. Keep the conversion explicit:

```text
PIL/OpenCV/NumPy HWC uint8 [0,255]
  -> ToTensor
Paddle CHW float32 [0,1]
  -> batch NCHW
```

The source GAN transforms generally use `ToTensor` and do not apply the
classification ImageNet mean/std normalization. Generated outputs are in the
model's native float tensor form and source generation/eval converts them with
`clip(output*127.5+128, 0, 255)`, then HWC uint8. Check actual min/max because
TransGAN has no final tanh in its inspected generator.

Do not pass HWC directly to a discriminator or FID feature extractor. Do not
compare `[0,1]` tensors to `[0,255]` arrays in PSNR/SSIM without a single,
recorded conversion.

## CIFAR10

The README says CIFAR10 is constructed through Paddle's
`paddle.vision.datasets.Cifar10`; it is not a manually unpacked directory in
this source workflow. A first-use constructor may try to fetch/cache data
through Paddle's dataset machinery. That is prohibited in this skill's
no-network mode. Only use it when the dataset is already cached or an
explicitly approved offline cache/data provider is configured.

Styleformer selects CIFAR10 in `gan/Styleformer/datasets.py`; its config is
32x32. In the source validation branch, CIFAR10's val selection uses the
Paddle dataset with a `mode='train'` override. Treat the resulting split and
sample count as source behavior to verify, not as a conventional test split.
TransGAN's dispatcher also supports CIFAR10 and its shipped config is 32x32.

## STL10

The expected root contains the binary files:

```text
STL10/
├── train_X.bin
├── train_y.bin
├── test_X.bin
├── test_y.bin
└── unlabeled.bin
```

The loader reads the whole `*_X.bin` as uint8, reshapes to
`[N,3,96,96]`, then transposes to `[N,96,96,3]` before the transform. Training
uses `train_X.bin`; Styleformer evaluation uses `unlabeled_X.bin` and assigns
zero labels. The shipped Styleformer STL10 YAML resizes to 48x48. Check that
`*_X.bin` byte length is divisible by `3*96*96`; a missing label file is only
valid for `unlabeled` mode.

## CelebA

The adapter uses `glob(os.path.join(file_folder, '*.jpg'))`, opens each file
with Pillow, forces RGB, and returns dummy label `0`. The path must therefore
be the directory containing the JPGs, commonly:

```text
Celeba/
└── img_align_celeba/
    ├── 000001.jpg
    ├── 000002.jpg
    └── ...
```

Pass `.../Celeba/img_align_celeba` to the source Styleformer `-data_path`,
not merely the parent unless it directly contains the JPGs. The shipped
CelebA YAML is 64x64. A valid-looking empty parent directory produces a
zero-length dataset; count JPGs before constructing the loader.

## LSUN-church LMDB

The expected path is an LMDB directory, not a normal folder of PNGs:

```text
LSUNchurch/
└── church_outdoor_train_lmdb/
    ├── data.mdb
    └── lock.mdb
```

The loader imports `lmdb`, opens read-only with `readahead=False`, enumerates
keys, decodes each value as an image through Pillow, and returns label `0`.
The source opens a separate LMDB handle lazily in `__getitem__` to support
multi-process loading. `map_size` in the inspection constructor is large but
read-only; do not create or repair a database during a smoke. Styleformer
LSUN is 128x128 and uses the Linformer generator variant.

A directory containing only `data.mdb` without a valid LMDB environment, a
missing `lock.mdb` on a copied/incomplete fixture, or an unavailable `lmdb`
module is a preflight failure. Do not replace an LMDB dataset with a glob of
images while claiming source equivalence.

## Dataset dispatch map

| Dataset | Styleformer main dispatcher | TransGAN main dispatcher | Required path |
|---|---|---|---|
| CIFAR10 | yes | yes | Paddle dataset cache/provider |
| STL10 | yes | no in `datasets.py` | root with binary files |
| CelebA | yes | no in `datasets.py` | JPG-containing `img_align_celeba` directory |
| LSUN | yes | no in `datasets.py` | `church_outdoor_train_lmdb` LMDB directory |
| ImageNet2012 | yes | yes | root with `train_list.txt`/`val_list.txt` |

The GAN request scope is the first four rows. Auxiliary TransGAN dataset
modules exist, but source main dispatch is the authority for what a stock
command actually wires.

## FID and paired metrics data

### FID

The source FID supports either two image directories or already-computed
`.npz` statistics in its path helper, and also accepts in-memory generated and
real Paddle tensors in validation. A valid run needs:

- a generated collection and a real collection from the same dataset/domain;
- matching preprocessing, channels, image range, and effective sample policy;
- a compatible local InceptionV3 parameter file, unless an explicit network
  permission is granted outside safe mode;
- a feature dimension supported by `InceptionV3.BLOCK_INDEX_BY_DIM`: 64, 192,
  768, or 2048; and
- at least two usable samples per covariance estimate. Record skipped files,
  batch truncation, and the exact `dims`.

The source's default `premodel_path=None` invokes
`get_weights_path_from_url`. Never use that default in a no-network run.
`MAX_REAL_NUM`/`MAX_GEN_NUM` are whole-batch limits in the validation loops;
inspect counts after floor division and do not report a number when either
collection is empty or unmatched.

### PSNR/SSIM

The source `PSNR` and `SSIM` metrics take paired arrays of identical shape,
`[H,W,C]` or `[C,H,W]`, pixel range `[0,255]`, and `input_order='HWC'` or
`'CHW'`. They use OpenCV. PSNR is infinite for identical arrays. SSIM uses an
11x11 Gaussian window and crops five pixels internally; images that are too
small can yield an invalid/empty comparison. `crop_border` must be chosen
consistently. These metrics evaluate reconstruction/paired fidelity; they do
not measure the distribution quality of independent GAN samples.
