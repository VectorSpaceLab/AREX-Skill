# DeblurGAN data layout

## Supported image inputs

The repository's image discovery helper accepts these extensions:

- `.jpg`, `.JPG`
- `.jpeg`, `.JPEG`
- `.png`, `.PNG`
- `.ppm`, `.PPM`
- `.bmp`, `.BMP`

Any other file type is ignored by the folder scanner.

## Layouts used by the repository

### `aligned`

This layout is for paired AB images already concatenated into one file.

Expected shape:

```text
dataroot/
  train/
    0001.jpg
    0002.jpg
  test/
    1001.jpg
```

Behavior:

- `AlignedDataset` reads `dataroot/<phase>`.
- Each AB image is resized to `(loadSizeX * 2, loadSizeY)` before cropping.
- The loader splits the tensor in half along width to produce `A` and `B`.
- Random crops and optional horizontal flips are applied during training.

### `single`

This layout is for one folder of individual images.

Expected shape:

```text
dataroot/
  image_001.jpg
  image_002.png
```

Behavior:

- `SingleDataset` scans the whole directory tree below `dataroot`.
- Each file is loaded as RGB.
- The loader returns only `A` and `A_paths`.
- This is the layout used by `model=test` inference.

### `unaligned`

The repository contains an `UnalignedDataset` class, but the shipped dataset factory does not initialize it correctly. Treat it as unsupported for DeblurGAN routing unless the source is fixed in a later repo revision.

## Pair generation helper behavior

The bundled pair helper mirrors the repo script logic:

- Iterate through split folders under `fold_A` and `fold_B`.
- Match filenames between the two trees.
- Concatenate image A and image B horizontally.
- Save the paired image under `fold_AB/<split>/`.

If `--use_AB` is set, the helper expects A-side filenames with `_A.` and maps them to `_B.` on the B side.

## Practical layout checks

Before training or inference, verify:

1. The folder you point at actually exists.
2. The expected phase folder exists for `aligned` mode.
3. The image files are readable and in a supported extension.
4. The A and B naming scheme is consistent when you build AB pairs.
