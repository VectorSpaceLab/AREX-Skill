# Dataset and Configuration

## SHHQ access and license

SHHQ-1.0 is a 40K-image release intended for non-commercial research. Access requires reading, signing, and submitting the dataset release agreement through the project’s institutional process. Do not place credentials, signed agreements, passwords, or released images in the generated skill directory, and do not assume a public mirror is licensed for the user’s purpose.

## Expected layout

The documented training commands assume a layout like:

```text
data/
└── SHHQ-1.0/
    ├── 000000.png (or another image format supported by the loader)
    ├── ...
    └── dataset metadata / labels when applicable
```

A directory or zip may be passed to `--data`. The loader must be able to discover images and their resolution/aspect ratio. For the standard human model, preserve the 1024x512 rectangle rather than silently resizing to square.

Before training, validate the path and sample the data independently. A path-exists check does not prove that the image count, file extensions, dimensions, or permissions are correct.

## Geometry and flags

- `--square False` is the documented setting for full-body 1024x512 SHHQ training.
- `--square True` is only appropriate when the dataset and intended model are square.
- `--mirror 1`/`True` enables horizontal flips; confirm that left/right semantics are safe for the dataset.
- `--cond` trains a conditional model only when usable dataset labels are present.
- `--subset` (SG2) is useful for controlled debugging, not for paper-scale quality claims.

## SG2 configuration

The SG2 entry point supports `auto`, `stylegan2`, `paper256`, `paper512`, `paper1024`, `cifar`, and `shhq` configs. `shhq` is the intended base for the documented human-image recipe. `--batch`, `--gamma`, `--kimg`, augmentation flags, precision flags, and worker count override defaults.

The StyleGAN-Human repository stores modified SG2 files under a training-scripts directory. Verify that the execution root also has the support modules from a complete StyleGAN2-ADA training tree, especially `training_loop`, `metrics`, `torch_utils`, and `dnnlib`.

## SG3 configuration

The SG3 entry point requires a base configuration such as `stylegan3-r`, `stylegan3-t`, or `stylegan2`. It also requires explicit total batch and R1 gamma values. The documented rectangle recipe uses `stylegan3-r`, batch 32, gamma 12.4, no augmentation, and eight GPUs.

As with SG2, make sure the execution root contains the complete StyleGAN3 training support modules. The generated command builder prints warnings when the default patch-script directory is not a complete root.

## Run manifest

Record at least:

- data path or dataset release identifier, not private credentials;
- image geometry and whether `square`/`mirror` were enabled;
- SG2/SG3 config, batch, gamma, augmentation, kimg, snap, seed, and GPU count;
- resume checkpoint and checksum when resuming;
- output directory and environment/package versions.

This record is necessary to distinguish a debug adaptation from a paper-scale reproduction.
