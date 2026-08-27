# Metrics workflows

This reference covers the ALAE repository metric scripts `metrics/fid.py`, `metrics/fid_rec.py`, `metrics/ppl.py`, and `metrics/lpips.py`. These are legacy, optional evaluation paths. Prefer readiness checks and documentation until the user explicitly accepts the runtime, data, checkpoint, and dependency cost of a native metric run.

## Critical import warning

Do not import the metric modules for inspection. At module import time, the metric files initialize the TensorFlow/dnnlib stack and call a helper that downloads metric pickle files into `metrics/`. Use source reads, this reference, and `../scripts/check_metrics_stack.py` instead.

## Environment expectations

- Run native repository scripts from the ALAE repository root and set `PYTHONPATH` to include that checkout root.
- The README metric section asks for TensorFlow GPU 1.10, CUDA 9.0-era libraries, and StyleGAN `dnnlib`.
- Inspection verified TensorFlow 1.15-style APIs and `dnnlib.tflib` imports in a prepared environment, but TensorFlow GPU execution remained unverified because the legacy CUDA/cuDNN libraries were missing.
- PyTorch CUDA must also be visible because the ALAE model, encoder, decoder, and checkpoint loading paths use PyTorch on GPU.
- Metrics are optional legacy workflows; do not make them a hard gate for ordinary training, generation, or repo-skill use.

## Safe readiness command

From the ALAE repository root:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/check_metrics_stack.py --repo-root <ALAE-checkout> --config ffhq
```

Use a concrete config path or name when the metric target is not FFHQ:

```bash
python scripts/check_metrics_stack.py --repo-root <ALAE-checkout> --config celeba
python scripts/check_metrics_stack.py --repo-root <ALAE-checkout> --config configs/celeba-hq256.yaml
```

The checker imports only `torch`, `tensorflow`, and `dnnlib`; checks TensorFlow 1.x APIs; reports PyTorch CUDA visibility; checks metric pickle files; resolves the config path; and checks the configured or supplied checkpoint pointer. It does not import `metrics/*.py`, does not download, and does not run metrics.

## Native metric scripts

Only run these after the readiness checklist passes and the user accepts an expensive native run.

| Script | Metric | Default config in source | Main required artifacts | Sample cost in source | Output signal |
| --- | --- | --- | --- | --- | --- |
| `metrics/fid.py` | FID for generated samples | `configs/ffhq.yaml` | checkpoint under `OUTPUT_DIR`, `OUTPUT_DIR/last_checkpoint`, training TFRecords from `DATASET.PATH`, `metrics/inception_v3_features.pkl`, PyTorch CUDA, TensorFlow/dnnlib | 50,000 real activations plus 50,000 generated images, minibatch `16 * torch.cuda.device_count()` | `logger.info("Result = ...")` written to `metrics/fid_score.txt` |
| `metrics/fid_rec.py` | FID for reconstructions | `configs/ffhq.yaml` | checkpoint, training TFRecords from `DATASET.PATH`, `metrics/inception_v3_features.pkl`, PyTorch CUDA, TensorFlow/dnnlib | 50,000 real activations plus 50,000 reconstructed images, minibatch `16 * torch.cuda.device_count()` | `logger.info("Result = ...")` written to `metrics/fid_score-reconstruction.txt` |
| `metrics/ppl.py` | Perceptual Path Length on generations | `configs/ffhq.yaml` | checkpoint, `metrics/vgg16_zhang_perceptual.pkl`, PyTorch CUDA, TensorFlow/dnnlib | two 50,000-sample passes: `sampling='full'` and `sampling='end'`, minibatch `16 * torch.cuda.device_count()` | logs `Result full = ...` and `Result end = ...` to stdout because `write_log=False` |
| `metrics/lpips.py` | LPIPS reconstruction distance | `configs/experiment_celeba.yaml` in source, but that config is absent in this checkout | checkpoint, test TFRecords from `DATASET.PATH_TEST`, `metrics/vgg16_zhang_perceptual.pkl`, PyTorch CUDA, TensorFlow/dnnlib | 10,000 test reconstructions, minibatch `16 * torch.cuda.device_count()` | `logger.info("Result = ...")` written to `metrics/lpips_score.txt` |

`metrics/fid_sep.py` is excluded from executable routing. It imports `model_separate.py` and defaults to `configs/experiment_celeba_sep.yaml`; both are absent in this checkout.

## Native command templates

From the ALAE repository root with `PYTHONPATH` set:

```bash
python metrics/fid.py -c ffhq
python metrics/fid_rec.py -c ffhq
python metrics/ppl.py -c ffhq
python metrics/lpips.py -c celeba
```

The launcher accepts either a config name or config path. If the argument has no extension, it appends `.yaml` and searches `configs/`. The native scripts also accept trailing YACS override pairs, for example:

```bash
python metrics/fid.py -c ffhq DATASET.PATH your/tfrecord-pattern OUTPUT_DIR training_artifacts/your-run
```

Use overrides cautiously: changing model architecture fields can make checkpoints incompatible.

## Required artifacts checklist

1. **Config**: a real config file such as `configs/ffhq.yaml`, `configs/celeba.yaml`, `configs/celeba-hq256.yaml`, `configs/bedroom.yaml`, `configs/mnist.yaml`, or `configs/mnist_fc.yaml`.
2. **Checkpoint**: `OUTPUT_DIR/last_checkpoint` must exist, and its contents must point to a readable `.pth` file. Checkpoint creation or pretrained checkpoint download belongs to the root setup/generation route, not this metrics sub-skill.
3. **TFRecords**:
   - FID and reconstruction FID need training records from `DATASET.PATH`.
   - LPIPS needs test records from `DATASET.PATH_TEST`.
   - Dataset conversion, split, and layout validation belong to `../../data-preparation/SKILL.md`.
4. **Metric pickle files**:
   - `metrics/inception_v3_features.pkl` for FID and reconstruction FID.
   - `metrics/vgg16_zhang_perceptual.pkl` for PPL and LPIPS.
   The source scripts try to fetch these at import time. For safe inspection, place or verify them explicitly rather than importing a metric module.
5. **Runtime stack**: PyTorch CUDA visibility, TensorFlow 1.x APIs (`tf.Session`, `tf.python_io`), `dnnlib.tflib`, compatible legacy CUDA/cuDNN libraries if TensorFlow GPU execution is required.

## Skip and expense decisions

Skip or defer native metric execution when any of these are true:

- The user only wants readiness or command guidance.
- TensorFlow imports but lacks the old GPU libraries needed by the legacy metric stack.
- Metric pickle files are missing and network/download permission has not been granted.
- Checkpoint or TFRecord artifacts are absent.
- The user has not accepted 10k/50k-sample metric costs.
- The requested script is `metrics/fid_sep.py` or any separate-model ablation route.

When skipped, provide the readiness report, the missing artifact list, and the exact native command the user can run after resolving prerequisites.
