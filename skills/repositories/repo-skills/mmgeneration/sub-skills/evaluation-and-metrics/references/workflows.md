# Evaluation and Metrics Workflows

## Purpose

Use this reference when a user needs a score, a sample-saving evaluation run, or precomputed statistics for a metric.

## Main entry points

### `tools/evaluation.py`

The repo's primary evaluation driver handles metric-based evaluation and sample saving.
Key flags:

- `--batch-size`
- `--samples-path`
- `--sample-model`
- `--eval`
- `--online`
- `--num-samples`
- `--sample-cfg`

Use `--eval none` when you only want saved samples and no metric score.

### `tools/utils/translation_eval.py`

Use this for translation models.
It reuses the model's translation domain logic and feeds real/fake images into the chosen metrics.

### `tools/utils/inception_stat.py`

Use this to precompute real-image inception statistics for FID-style evaluation.
It can load either a directory of images or a dataset config.

## Metric classes

Verified classes and signatures:

- `FID(num_images, image_shape=None, inception_pkl=None, bgr2rgb=True, inception_args={...})`
- `IS(num_images, image_shape=None, bgr2rgb=True, resize=True, splits=10, use_pil_resize=True, inception_args={...})`
- `PPL(num_images, image_shape=None, crop=True, epsilon=0.0001, space='W', sampling='end', latent_dim=512)`
- `PR(num_images, image_shape=None, num_real_need=None, full_dataset=False, k=3, bgr2rgb=True, vgg16_script='work_dirs/cache/vgg16.pt', row_batch_size=10000, col_batch_size=10000)`
- `SWD(num_images, image_shape)`
- `MS_SSIM(num_images, image_shape=None)`
- `GaussianKLD(num_images, base='e', reduction='batchmean')`

## Online vs offline

- **Offline** evaluation saves or reuses images on disk before feeding them to metrics.
- **Online** evaluation keeps the images in memory and is generally faster, but it uses more memory.

## Distributed metric limits

The distributed evaluation path intentionally supports only a subset of metrics. In practice, treat FID and IS as the primary distributed metrics and keep the other metrics in the single-process path unless the repo evidence says otherwise.

## Cached statistics and assets

Some metric paths need cached external assets:

- Real-image inception statistics for FID.
- Tero-style inception or VGG script modules for some metric variants.
- Pretrained cache files used by metric or evaluation helpers.

The generated skill should explain these assets as optional or required depending on the exact metric path.

## Evidence sources

- `mmgen/core/evaluation/*`
- `tests/test_cores/test_metrics.py`
- `docs/en/tutorials/inception_stat.md`
- `docs/en/quick_run.md`
- `docs/en/tutorials/customize_runtime.md`
- `docs/en/tutorials/ddp_train_gans.md`
