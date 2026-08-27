---
name: generative
description: "Use for PaddleViT GAN workflows with TransGAN or Styleformer:
  choose the generator/discriminator family, validate
  CIFAR10/STL10/CelebA/LSUN-LMDB inputs, generate or evaluate image batches,
  interpret FID/PSNR/SSIM, and respect single- or multi-GPU and dependency
  boundaries. Excludes checkpoint porting, network downloads, and full
  dataset-scale training unless explicitly requested."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleViT GANs

## Responsibility and boundaries

Use this route when a request names the PaddleViT GAN module, **TransGAN**, or
**Styleformer**, or asks to generate/evaluate images from one of those
transformer GANs. The route owns:

- the two model families' generator/discriminator contracts and shipped YAML
  variants;
- the CIFAR10, STL10, CelebA, and LSUN-church LMDB data contracts;
- safe generation/evaluation planning, image range/layout checks, FID/PSNR/SSIM
  interpretation, and training/evaluation resource boundaries;
- dependency diagnosis for Paddle, Pillow, OpenCV, SciPy, LMDB, matplotlib, and
  tqdm; and
- the download-free bundled contract smoke at
  `scripts/generative_model_smoke.py`.

Do not use this route for classification, detection, segmentation, generic
Paddle export, or repository-wide environment operations. Do not port PyTorch
weights or download checkpoints, Inception weights, or datasets as part of a
safe generation/evaluation request. The source contains weight-porting helpers
and external model links, but those are deliberately excluded. Full
50k-sample evaluation and multi-epoch/full-dataset training are expensive and
require explicit user authorization, local data, local checkpoints, and a
verified budget.

This is a self-contained operating guide. It does not import the original
checkout at runtime. The source was inspected at PaddleViT commit
`5ac7d89d4fd0e3235d055ff15d5b1b1315499d70`; source paths in the evidence list
are provenance, not runtime dependencies.

## Route a request

1. Identify the family and operation before touching a config:
   - choose **TransGAN** for the pure-transformer generator and two-scale
     transformer discriminator;
   - choose **Styleformer** for the style-vector mapping/synthesis generator
     and StyleGANv2-style convolutional discriminator;
   - choose `generate` for images only, `eval` for FID or metric reporting, and
     `train` only after the user explicitly accepts data/GPU/compute cost.
2. Choose the dataset and exact image size. The shipped Styleformer YAMLs map
   CIFAR10→32, STL10→48, CelebA→64, and LSUN-church→128. The TransGAN YAML is
   CIFAR10→32. Do not silently reuse a 32-pixel config for a 48/64/128-pixel
   dataset.
3. Inspect the local data layout with the checklist in
   `references/data-formats.md`. An absent optional dependency is a preflight
   failure, not a reason to create a fake dataset or claim evaluation passed.
4. Run the safe, deterministic synthetic smoke before a source build or a
   costly run:

   ```bash
   python /path/to/this/skill/scripts/generative_model_smoke.py --help
   python /path/to/this/skill/scripts/generative_model_smoke.py --model all --device auto
   ```

   This checks small independent Paddle contracts only. It does not import the
   checkout, load a checkpoint, open a dataset, contact a URL, or prove
   historical GAN quality. If Paddle is unavailable, the script reports a
   clearly marked skip.
5. For a source model build, run from exactly one family directory and expose
   only that directory on `PYTHONPATH`:

   ```bash
   cd gan/transGAN       # or gan/Styleformer
   export PYTHONPATH="$PWD:${PYTHONPATH:-}"
   ```

   Both families use common module names (`config.py`, `utils.py`,
   `generate.py`). Mixing both source roots can import the wrong family.
6. Record the final config, source commit, device, seed, local checkpoint
   provenance, data counts, image range/order, metric feature extractor, and
   sample limits. If any of those are unknown, report the result as partial.

## Source command contract

The source uses short single-dash flags. A safe command is a plan/template,
not permission to download or run expensive work:

```text
-cfg PATH             family YAML; recursive BASE entries are supported
-dataset NAME         cifar10, stl10, celeba, or lsun where wired
-batch_size N         per-process batch size
-data_path PATH       dataset root or family-specific image/LMDB directory
-image_size N         override only when model architecture supports it
-eval                 evaluation-only path
-pretrained PREFIX    source training/eval appends .pdparams in main scripts
-resume PREFIX        source expects PREFIX.pdparams and PREFIX.pdopt
-num_out_images N     generation count for generate.py
-out_folder DIR       generated image destination
```

`generate.py` has family-specific conventions. TransGAN's generator loads a
state dictionary under `gen_state_dict`; Styleformer's standalone generator
loader expects the saved generator dictionary directly, while the training
scripts expect a combined `gen_state_dict`/`dis_state_dict` checkpoint. Verify
the actual local file keys before loading. Do not add `.pdparams` to a
`-pretrained` prefix when using the training/evaluation scripts; generation
examples are inconsistent and may accept a complete filename. Prefer an
explicit local-file check and a tiny load test over guessing.

## Generation and evaluation procedure

### Generation

- Set the device before model construction. Use one visible GPU for a normal
  source generation run; CPU is suitable only for parser/shape diagnostics and
  may be impractical for the full transformer.
- Seed Paddle (and NumPy/Python if used by the caller) before sampling. The
  source scripts use random latent tensors and do not promise a stable
  benchmark seed.
- TransGAN samples `z` with shape `[B, 256]`, calls `Generator(z, epoch)`, and
  returns `[B, 3, 32, 32]` for the shipped CIFAR10 config. Styleformer samples
  `z` with shape `[B, 512]`; its `c_dim` is zero in the shipped configs, so the
  mapping network ignores labels even though eval code supplies a label
  tensor. It returns `[B, 3, H, W]` with H/W set by the chosen config.
- Both source generation scripts postprocess model output with
  `(output * 127.5 + 128).clip(0, 255).astype('uint8')`, then transpose from
  CHW to HWC and write RGB PNGs. This assumes the model output is in a
  `[-1, 1]`-like range. TransGAN's final source `Conv2D` has no explicit tanh;
  inspect output statistics rather than treating the assumption as a proven
  invariant.
- Keep generated tensors in NCHW for Paddle discriminators and metric feature
  extraction. Convert to HWC only at the image-file boundary.

### Evaluation

The source validation loop pairs each real batch with a random generated batch,
converts fake images to `[0,1]` after uint8 clipping, and feeds both through
the local FID implementation. `MAX_REAL_NUM` and `MAX_GEN_NUM` are converted
to whole batches with integer division; a limit smaller than one batch can
silently yield no usable samples. Check effective counts after batching.

FID is distribution-level and requires both real and generated collections,
the same image preprocessing, a local compatible InceptionV3 parameter file,
and enough samples to form non-degenerate statistics. The source FID class
will otherwise call Paddle's URL weight helper, which violates this skill's
no-network boundary. Pass a local `premodel_path` only in an explicitly
approved evaluation environment; never let a safe smoke implicitly download
it. The repository README's `fid50k_full` numbers are historical reference
claims, not results produced by this skill.

PSNR and SSIM are paired image-fidelity metrics in the bundled source metric
implementation. They require equal shapes, accept `HWC` or `CHW`, and expect
pixel values in `[0,255]`; `crop_border` removes pixels on every edge. They
are not substitutes for GAN FID when comparing unrelated generated and real
sets. SSIM uses OpenCV's Gaussian filter and the source reverses channels in
its implementation, so record channel order and do not compare its number to
a differently configured library without a controlled fixture.

## Training and device boundaries

Training is not a smoke:

- TransGAN's single-GPU loop uses a hinge-style discriminator loss and updates
  the generator on alternating epochs; the config defaults to 300 epochs,
  `AdamW`, warmup/cosine scheduling, and gradient clipping. The discriminator
  can apply `DiffAugment` when `DATA.DIFF_AUG` is not effectively disabled.
- Styleformer's loop uses a WGAN-GP-like objective, one discriminator update
  followed by five generator updates, and a gradient penalty. Its helper uses
  an explicit `.cuda()` for interpolation, so CPU training is not a valid
  substitute without a deliberate source fix. Its source also places uint8
  clipping/scaling in the training path; verify current Paddle gradient
  behavior before claiming that an unmodified source run trains correctly.
- Single-GPU scripts construct both networks and ordinary data loaders. The
  multi-GPU scripts use `paddle.distributed`, `DataParallel`, distributed
  batch sampling, and gather FID feature lists. `-batch_size` is per GPU, so
  effective batch size scales with visible process count. Set
  `CUDA_VISIBLE_DEVICES` and `-ngpus` consistently; do not infer that a CPU
  run verifies NCCL or multi-GPU behavior.
- The prepared inspection evidence is Paddle GPU 2.6.2 on an A100 host with
  Pillow/OpenCV/SciPy/LMDB/matplotlib/tqdm imports and CUDA dependency smoke
  passing. This is environment evidence, not a guarantee that every
  Paddle-2.1-era script is unchanged-compatible with Paddle 2.6.2.

## Verification ladder

Use the cheapest check that answers the question:

1. Parse the YAML and inspect dataset/checkpoint paths without opening data.
2. Run `generative_model_smoke.py` for deterministic, download-free tiny
   generator/discriminator shape and finite-value contracts.
3. Build one source family on a tiny local/synthetic tensor and record actual
   output shapes. The inspected source smoke passed on `gpu:0` for both
   shipped CIFAR10 configurations: each generator returned `[1,3,32,32]`
   and each discriminator returned `[1,1]` with finite values.
4. Decode a few local data examples and verify range/order/shape. Test LMDB
   opening separately from model construction.
5. Run a bounded local generation or metric calculation only with an explicit
   checkpoint, local Inception weights for FID, local data, and a declared
   sample count.
6. Treat full training, 50k FID, multi-GPU eval, and historical model-zoo
   reproduction as expensive acceptance tests, not default verification.

A pass at an earlier level does not establish checkpoint compatibility, FID
quality, dataset correctness at scale, or historical benchmark reproduction.

## References and recovery

Use the focused references for details rather than expanding this router:

- `references/model-overview.md`: model and discriminator internals, config
  matrix, tensor contracts, and source quirks.
- `references/workflows.md`: safe generation/evaluation/training planning,
  single/multi-GPU commands, metric gates, and no-network rules.
- `references/data-formats.md`: exact dataset layouts, transforms, path
  semantics, labels, ranges, and preflight checks.
- `references/troubleshooting.md`: dependency, path, shape, metric, CUDA, and
  source-compatibility recovery.

When a problem is shared with Paddle installation, AMP, distributed launch,
export, or inference, hand off to the repository's deployment/operations
route instead of inventing a second global environment procedure.
