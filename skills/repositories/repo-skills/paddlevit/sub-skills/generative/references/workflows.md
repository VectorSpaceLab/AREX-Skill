# GAN workflows

## A. Safe no-network preflight

Use this before any source import or model allocation:

1. Select `transgan_cifar10.yaml` or one Styleformer YAML and record the
   dataset, image size, latent width, and expected output.
2. Check that the checkpoint and (for FID) Inception parameter paths are local
   regular files. A checkpoint prefix may be a source convention; resolve it
   to the actual `.pdparams` file without downloading anything.
3. Check dependencies with the active environment's interpreter:

   ```bash
   python -c "import paddle, PIL, cv2, scipy, lmdb, matplotlib, tqdm"
   ```

   The `lmdb` import is required for LSUN, while OpenCV/SciPy are required by
   the source metrics and Pillow is needed by image datasets/output. `lmdb`
   may be omitted for a CIFAR-only generation smoke, but not for an LSUN
   source loader. Missing Paddle is a hard model-build block.
4. Check the dataset layout from `references/data-formats.md`; do not invoke a
   first-use CIFAR constructor unless its cache/provider is known offline.
5. Run the bundled synthetic contract smoke. It is deliberately independent
   of the source checkout and contains no URL, checkpoint, or dataset code.

## B. TransGAN generation plan

For a local approved checkpoint:

```bash
cd gan/transGAN
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
CUDA_VISIBLE_DEVICES=0 python generate.py \
  -cfg=./configs/transgan_cifar10.yaml \
  -num_out_images=16 \
  -out_folder=./images_cifar10 \
  -pretrained=/local/weights/transgan_cifar10.pdparams
```

Before running, inspect `generate.py` and reconcile its loader with the actual
checkpoint format. The source model is built from `models.ViT_custom.Generator`
and the generation latent is `[N,256]`. Output files are RGB PNGs. Use a
small count first, inspect output statistics and one decoded image, then scale
up only with explicit approval.

For source evaluation, the README's representative single-GPU shape is:

```bash
CUDA_VISIBLE_DEVICES=0 python main_single_gpu.py \
  -cfg=./configs/transgan_cifar10.yaml -dataset=cifar10 \
  -batch_size=32 -data_path=/local/data -eval \
  -pretrained=/local/weights/transgan_cifar10
```

The source may instantiate FID with no local `premodel_path` and trigger a
network lookup. Do not run that path in safe mode. A no-network FID evaluation
requires a small local compatibility adaptation or a source API call that
passes a local Inception model/weights; document the adaptation outside the
runtime skill and never silently claim it is the stock command.

## C. Styleformer generation plan

Select the YAML that matches the target domain:

```bash
cd gan/Styleformer
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
CUDA_VISIBLE_DEVICES=0 python generate.py \
  -cfg=./configs/styleformer_cifar10.yaml \
  -num_out_images=16 \
  -out_folder=./images_cifar10 \
  -pretrained=/local/weights/cifar10.pdparams
```

The same pattern applies to STL10, CelebA, and LSUN, but the `IMAGE_SIZE`,
`GEN_DICT`, resolution stages, data path, and GPU memory change with the YAML.
Styleformer generation uses `z [N,512]`, calls the style mapping/synthesis
network, and writes NCHW→HWC RGB PNGs. For `C_DIM=0`, labels have no semantic
conditioning effect.

The training/evaluation scripts load combined state dictionaries using a
prefix and append `.pdparams`. Confirm whether a standalone generation file
contains the raw generator dictionary or a wrapper before calling
`load_dict`; do not reshape or partially port weights.

## D. Bounded evaluation plan

A valid FID plan must declare:

```text
family/config + commit
real source and generated source
local Inception weights and feature dims
preprocessing/range/order
batch size and effective real/fake counts
seed and device
whether files or in-memory tensors are used
```

Use a tiny local fixture only to check plumbing. Do not infer quality from a
2-image FID: covariance is degenerate and the number is not comparable to
`fid50k_full`. For a real bounded evaluation, use enough local samples for a
stable declared protocol, cap both collections intentionally, and preserve
all logs. The source implementation truncates by whole batches, so check the
actual count rather than the configured limit.

PSNR/SSIM can be run only when there is a meaningful paired target, such as a
reconstruction or a deterministic same-seed comparison. Pairing arbitrary
real images with random GAN images is invalid. Keep arrays in `[0,255]`, same
shape, and record `input_order`, `crop_border`, and channel convention.

## E. Training plan (explicitly expensive)

Do not launch from a generic request. Obtain explicit authorization for local
data, checkpoint/output paths, epoch/batch budget, GPU count, and stop
conditions. Then:

1. start with a one-batch source build/forward and finite-output check;
2. run a bounded one- or few-batch diagnostic, observing loss and memory;
3. verify checkpoint writes to a user-approved output directory;
4. only then consider the configured long run (both shipped configs default to
   300 epochs).

TransGAN uses single-GPU or process-per-GPU distributed scripts; its effective
batch is per process and validation gathers FID feature lists in multi-GPU
mode. Styleformer's distributed path has the same per-GPU distinction and a
WGAN-GP `.cuda()` boundary. `CUDA_VISIBLE_DEVICES` must match `-ngpus` and
NCCL/process setup. A successful tiny `gpu:0` forward does not prove
multi-GPU launch or full training.

## F. No-network stop conditions

Stop and report `blocked`/`partial` rather than improvising when:

- Paddle or the requested CUDA backend is unavailable;
- a checkpoint, dataset, or Inception weights file is absent and the only
  source fallback is a network URL;
- the dataset path is ambiguous or its shape/count contract fails;
- FID receives fewer than two usable samples, mismatched feature dimensions,
  or unequal effective real/fake collections;
- a custom resolution is not represented by the Styleformer discriminator's
  channel table;
- a source import resolves the other family's `config.py`/`utils.py`; or
- the user requested full training/evaluation without an explicit compute and
  data budget.

Do not turn a synthetic smoke, import-only check, or historical README number
into a model-quality claim.
