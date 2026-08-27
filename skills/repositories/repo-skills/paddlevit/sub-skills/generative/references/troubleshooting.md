# GAN troubleshooting

## Imports and dependencies

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named paddle` | wrong interpreter or no Paddle install | activate/use the intended Paddle environment; run the import probe; do not install during a safe smoke |
| `No module named lmdb` | LSUN loader dependency absent | install/enable a compatible local package only with environment approval, or select a non-LSUN workflow; do not replace LMDB with a glob |
| `No module named cv2` | PSNR/SSIM or FID image path dependency absent | repair the approved environment or run model/generation-only checks; do not claim those metrics passed |
| `No module named scipy` | FID `scipy.linalg.sqrtm` unavailable | repair SciPy; FID cannot be replaced by a scalar placeholder |
| Pillow/OpenCV decode error | corrupt/non-RGB file or wrong path | decode one file, force RGB, inspect extensions and permissions; preserve the original data |
| matplotlib/tqdm import error | main script/helper dependency absent | use the narrow smoke where possible; repair only if the selected source workflow imports it |

The inspected environment facts are Paddle GPU 2.6.2, CUDA-capable A100 host,
Pillow/OpenCV/SciPy/LMDB/matplotlib/tqdm imports, and a passing CUDA smoke.
Paddle 2.6.2 is newer than the source's documented 2.1-era baseline; if a
historical API fails, record the version seam rather than silently rewriting
the architecture.

## Source-root and config errors

- `ImportError` or an apparently wrong `Generator`: run from exactly
  `gan/transGAN` or `gan/Styleformer` and expose only that directory on
  `PYTHONPATH`. Both families have modules with the same names.
- YACS unknown-key/merge error: check the YAML against its family's
  `config.py`, resolve `BASE` relative to the YAML, and print the final config.
  Do not feed a Styleformer YAML to TransGAN or vice versa.
- Model output has the wrong size: check `IMAGE_SIZE`, initial resolution,
  `NUM_LAYERS`, `G_DICT`, and the selected family. TransGAN's shipped path is
  32; Styleformer's discriminator requires a size present in its channel map.
- `KeyError` in Styleformer discriminator channels: the custom resolution is
  unsupported by the source `channels` table. Use one of the shipped sizes or
  deliberately extend and test the architecture; do not interpolate a
  checkpoint.
- checkpoint state mismatch: check the family, YAML, output resolution,
  latent width, and whether the file is raw generator state versus a wrapper
  with `gen_state_dict`/`dis_state_dict`. Do not port or reshape weights in
  this route.

## Dataset path and shape errors

- CIFAR attempts a URL: Paddle's dataset constructor is trying first-use
  download. Stop in no-network mode; provide a pre-populated offline cache or
  an explicitly approved local provider.
- STL10 reshape/EOF error: verify each `*_X.bin` has byte length divisible by
  `96*96*3`, and that label files exist for `train`/`test` but not necessarily
  `unlabeled`.
- STL10 labels/images differ: inspect `train_y.bin`/`test_y.bin` counts and
  confirm the selected mode. Unlabeled evaluation labels are dummy zeros.
- CelebA length is zero: `data_path` must directly contain JPGs, normally
  `img_align_celeba`, because the adapter globs only `file_folder/*.jpg`.
- LSUN open fails: pass the directory containing `data.mdb`/`lock.mdb`, ensure
  it is a valid read-only LMDB, and check `lmdb` import. Do not pass a parent
  archive or a normal image directory.
- discriminator receives `[B,H,W,3]`: transpose to `[B,3,H,W]` before the
  model; only transpose back when writing images.
- colors look wrong: Pillow is RGB; OpenCV file reads are often BGR. Convert
  explicitly and record the convention, especially before SSIM/FID.

## Generation and metrics

- generated values overflow or look flat: inspect native min/max. The source
  postprocess assumes approximately `[-1,1]`; clipping hides an output-scale
  or missing-checkpoint problem. TransGAN has no explicit final tanh.
- FID tries to download Inception weights: pass a local compatible parameter
  file/model through an explicitly approved evaluation path. The default
  source `premodel_path=None` is not safe here.
- FID covariance/`sqrtm` failure: check for at least two usable samples,
  finite features, identical feature dimensions, and non-degenerate data;
  increase the bounded sample count rather than adding arbitrary jitter.
- FID is strangely low/high: verify real and fake preprocessing, NCHW order,
  `[0,1]` versus `[0,255]`, RGB/BGR, feature dimension, checkpoint, seed, and
  actual whole-batch counts. Compare only like-for-like protocols.
- FID lists are empty or unequal: `MAX_*_NUM // batch_size` can truncate to
  zero, and the source may collect real/fake batches differently. Print
  effective counts and stop rather than reporting a score.
- PSNR assertion says shapes differ: pair like-for-like images and equalize
  shape/order first. PSNR is not meaningful for independent GAN samples.
- SSIM returns NaN/empty result: use images larger than the source's 11x11
  Gaussian window, inspect `crop_border`, finite values, and channel order.
  OpenCV is required.

## Runtime and GPU failures

- CUDA library load failure (`libcudnn`, `libcublas`): use the prepared
  Paddle/CUDA environment and its approved loader configuration, then rerun a
  tiny `paddle.set_device('gpu:0')` operation. Do not copy machine-specific
  library paths into this skill or claim CPU equivalence.
- CUDA out of memory: reduce per-GPU batch, generation count, workers, or
  image size; use a matching lower-resolution YAML. Multi-GPU does not make a
  single process's batch free.
- Styleformer CPU training fails in `gradient_penalty`: the source helper uses
  `.cuda()`; mark CPU as unsupported for that training path. Use CPU only for
  parser/data/metric or tiny contract diagnostics.
- multi-GPU hangs or wrong counts: check `CUDA_VISIBLE_DEVICES`, `-ngpus`,
  process-per-GPU launch, NCCL availability, distributed sampler, and FID
  gather. A single-GPU pass is not a distributed verification.
- non-finite loss/output: verify range conversion is not inserted into a
  gradient path, lower batch/learning rate, inspect input data, and run the
  tiny deterministic smoke. Do not continue a long training run with NaN.

## Escalation boundary

Weight porting, checkpoint conversion, external Inception acquisition,
full-dataset training, and large benchmark reproduction need a separate
explicitly authorized plan. Preserve local partial evidence and stop; do not
invoke the source `load_pytorch_weights*.py` or `port_weights/` helpers as a
shortcut.
