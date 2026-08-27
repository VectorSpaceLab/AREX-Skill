# Configuration, normalization, and checkpoints

## `Config.initialize`

`style_transfer/config.py` defines a mutable `Config` class. Important defaults
are:

```text
name = pretrained
cuda_id = 0
expr_dir = directory containing config.py
data_filename = xia.npz
data_path = <expr_dir>/data/xia.npz
extra_data_dir = <expr_dir>/data/xia_norms
batch_size = 128
max_iter = 300000
num_classes = 8
```

`initialize(args, save=True)` applies a non-`None` `args.name` and derives:

```text
main_dir   = expr_dir / name
model_dir  = main_dir / pth
tb_dir     = main_dir / log
info_dir   = main_dir / info
output_dir = main_dir / output
```

It creates these directories plus `extra_data_dir`, selects
`torch.device("cuda:0")` when CUDA is available and `cpu` otherwise, and copies
`<config>.py` to `info` when saving. The config name must therefore be both
importable in the source layout and available as a file below `style_transfer`.
The source CLIs do not expose data, model, device, or normalization arguments.

There is a source typo:

```python
if hasattr(args, 'batch_size') and args.name is not None:
    self.batch_size = args.batch_size
```

Thus `--batch_size` without a non-`None` name is not applied; conversely, a
non-`None` name with the option omitted assigns `None` and can break training.
The bundled training helper always passes an explicit default of 128. Inference
uses a single `to_batch=True` sample, so this chiefly matters for training. The
source also passes `lr_gen` to the discriminator RMSprop and `lr_dis` to the
generator RMSprop; defaults are equal, but custom learning rates should be
checked.

## Data and normalization

For default 3D inference, `process_single_bvh` loads:

```text
<expr_dir>/data/xia_norms/train_content.npz
<expr_dir>/data/xia_norms/train_style3d.npz
```

Each NumPy archive must contain `mean` and `std` arrays. They are converted to
float tensors with a singleton time dimension and applied as `(raw-mean)/std`.
When `NormData` creates an archive, exact zero std values become `1e-9`.
Missing files/keys, wrong channel counts, NaNs, or norms from a different
skeleton/dataset are not repaired automatically.

The JSON path's `process_single_json` has a separate source-relative default:

```text
style_transfer/data/treadmill_norm/test2d.npz
```

It also requires `mean`/`std` and 42 channels. The source test CLI cannot
replace this path. A helper's `--normalization-dir` covers the content/BVH
side; it does not override the hard-coded 2D archive.

Training's default `dataset_norm_config` is:

```python
{
  "train": {"content": None, "style3d": None, "style2d": None},
  "test": {"content": "train", "style3d": "train", "style2d": "train"},
  "trainfull": {"content": "train", "style3d": "train", "style2d": "train"},
}
```

A `None` prefix computes a new `<subset>_<key>.npz`; a non-`None` prefix
requires that archive already exist. Default training therefore creates
`train_content.npz`, `train_style3d.npz`, and `train_style2d.npz` under
`extra_data_dir`, then reuses them for test/trainfull.

## Dataset/config alignment

Default config is Xia: `data_filename=xia.npz` and `num_classes=8`. BFA has 16
labels and requires a config that points at `bfa.npz`, sets `num_classes=16`,
and uses compatible norms and checkpoints. Do not load an eight-class checkpoint
with a 16-class discriminator.

Architecture fields that must agree with weights include `rot_channels=128`,
`pos3d_channels=64`, `proj_channels=42`, content encoder channels `[128,144]`,
style encoder output 144, decoder output `31*4` rotations, discriminator
channels `[64,96,144]`, and `num_classes`. Changes to skeleton/channel/decoder
fields, rotation loss, or decoder variant can make state dictionaries
incompatible. `model.py` combines adversarial, reconstruction, feature,
quaternion/twist, triplet, and joint losses; its `Trainer` wraps RMSprop and
optional schedulers.

## Checkpoint resume

The source does not accept `--checkpoint`. `Trainer.resume` searches its
computed `model_dir` for the lexicographically last regular filename containing
`gen` and `.pt`, then expects a matching `dis` file and `optimizer.pt`. It
loads state dictionaries with `map_location=config.device`, restores both
optimizer states/schedulers, parses iteration from the generator filename, and
prints the resumed iteration. With no generator it prints `Initialize from 0`.

A complete run normally has:

```text
<name>/pth/gen_XXXXXXXX.pt
<name>/pth/dis_XXXXXXXX.pt
<name>/pth/optimizer.pt
<name>/info/<config>.py
<name>/log/...
<name>/output/...
```

Changing `--name` changes `main_dir` and all these lookup paths. Supplying a
checkpoint directory to the helper is a preflight assertion that it is the
source-derived directory; the source CLI itself cannot redirect lookup. Do not
copy or rename weights to fake compatibility. The helper requires explicit
`--allow-resume` before an existing complete set is used and rejects partial
sets.

## Import/device caveats

The source inserts its own `style_transfer` directory and repository parent
into `sys.path` and imports short names such as `model`, `data_loader`, and
`py_utils`. Run via a helper with an explicit source root or reproduce the
source working-directory layout; normal pip import is not promised. A CUDA
installation can still fail due to driver/device mismatch. CPU fallback occurs
after imports and can be too slow for full training.
