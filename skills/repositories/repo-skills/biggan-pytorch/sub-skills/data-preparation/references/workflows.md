# Data-preparation workflows

Run repository entry points from `REPO_ROOT`. Set `SKILL_ROOT` to the
directory containing the root skill `SKILL.md` and `REPO_ROOT` to the checked-
out BigGAN-PyTorch repository, then run `cd "$REPO_ROOT"`. Confirm the
environment has a compatible PyTorch/torchvision pair plus NumPy, SciPy, h5py,
Pillow, and tqdm. Confirm CUDA before moments generation because the source
metric script uses `device = 'cuda'` unconditionally.

```bash
python make_hdf5.py --help
python calculate_inception_moments.py --help
python "$SKILL_ROOT/sub-skills/data-preparation/scripts/validate_hdf5.py" --help
```

For ImageFolder, install the ImageNet tree as `data/ImageNet/<class>/<image>`.
This is a network/storage-dependent prerequisite outside the repository; do
not script its acquisition here. For CIFAR, use `--dataset C10` or `C100` and
approve the torchvision archive download if it is not already present.

## 2. Direct ImageFolder or CIFAR loading

Use direct folders when repeated HDF5 conversion is not worth its disk and
preprocessing cost. The central loader applies the following exact routing:

```text
I32/I64/I128/I256       -> data/ImageNet
I32_hdf5/...            -> data/ILSVRC{size}.hdf5
C10/C100                -> data/cifar
```

Typical training flags are `--dataset I128 --data_root data --shuffle`, or
`--dataset C10 --data_root data --shuffle`. Add `--augment` only when random
crops/flips are part of the intended data protocol. Start with
`--num_workers 0` while diagnosing paths or transforms, then choose a higher
value after measuring. The normal loader defaults to `drop_last=True`; the
conversion script overrides this to preserve every sample.

## 3. Convert ImageFolder to HDF5

The checked-in `scripts/utils/prepare_data.sh` is exactly:

```bash
python make_hdf5.py --dataset I128 --batch_size 256 --data_root data
python calculate_inception_moments.py --dataset I128_hdf5 --data_root data
```

Run the two stages separately when monitoring or validating. The conversion
stage should receive a **non-HDF5 ImageNet** key (`I32`, `I64`, `I128`, or
`I256`), and refuses a key containing `hdf5` to avoid reading and overwriting
its intended output. Although the parser mentions `C10` and `C100`, the output
is still named `ILSVRC{size}.hdf5` and the central mappings expose no
`C10_hdf5` or `C100_hdf5` training keys; use the script for the supported
ImageNet HDF5 route unless you have deliberately implemented and verified
custom mappings. It calls `utils.get_data_loaders()` with `shuffle=False`,
`drop_last=False`, `pin_memory=False`, and the source dataset's normal
non-augmented transforms. The first batch creates
`<data_root>/ILSVRC<size>.hdf5`; later batches append along axis 0.

Useful parameters:

- `--batch_size`: source read/write batch. Reduce it if image decoding or
  temporary tensors exceed RAM/VRAM; this script's loader is CPU-oriented and
  sets pinning off.
- `--num_workers`: image decoding workers, default 16. Start lower for
  diagnosis or constrained hosts.
- `--chunk_size`: HDF5 sample chunk length, default 500. Chunks affect random
  read amplification, write behavior, and temporary HDF5 buffering; they do
  not change the logical schema.
- `--compression`: enables LZF. It can reduce storage but may reduce read
  throughput; benchmark the target filesystem rather than assuming it is
  faster.

The source comments report approximate ImageNet experiments: at 128px, chunk
500 without compression was about 102 reads/s, about 61GB, and 23 minutes to
write; chunk 500 with LZF was about 8 reads/s, about 56GB, and 23 minutes.
Other chunk sizes were measured at different resolutions. Treat these as
historical machine-specific observations, not guarantees. A raw image chunk
alone is approximately `chunk_size * 3 * size * size` bytes (about 24.6MB for
500 samples at 128px and 98.3MB at 256px), before process/batch overhead.
Conversion also needs free space for the source data and output; a failed or
interrupted run may leave a partial output that should be removed or
recreated after inspection.

After conversion, validate metadata without loading all images:

```bash
python "$SKILL_ROOT/sub-skills/data-preparation/scripts/validate_hdf5.py" \
  "$REPO_ROOT/data/ILSVRC128.hdf5" --resolution 128 --classes 1000 --check-label-range
```

## 4. Calculate reference Inception moments

Once the exact dataset representation and resolution are accepted, run:

```bash
python calculate_inception_moments.py \
  --dataset I128_hdf5 --data_root data \
  --batch_size 64 --num_workers 8
```

The script loads the repository's PyTorch Inception network, computes pool
activations and softmax logits for every sample, reports the training-data
Inception Score, and saves `mu` and `sigma` as
`I128_inception_moments.npz` in the current working directory. It strips the
`_hdf5` suffix for this filename; downstream code loads
`<base-dataset>_inception_moments.npz`. The output location is not derived
from `data_root`, so move/copy it deliberately if the training or sampling
roots differ.

The parser defaults to `shuffle=False` to reduce nondeterminism, but the
source warns that an ordered, label-grouped dataset underestimates Inception
Score. Use `--shuffle` when the training-data IS estimate is intended to be
less order-biased; record the choice. Do not use random augmentation for
reference FID moments unless that augmented distribution is explicitly the
target. HDF5's loader ignores the transform anyway.

This stage is expensive: it requires a CUDA-capable runtime, reads the entire
selected dataset, retains batches of pool/logit/label arrays in host memory,
and computes a covariance matrix. Set `--batch_size` and `--num_workers` to
fit the GPU/host, and do not infer a valid full moments file from a one-batch
run. These repository PyTorch Inception metrics are monitoring metrics and
are not directly comparable to the official TensorFlow Inception scores
called out in the README.
