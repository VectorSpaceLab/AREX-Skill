# Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| No CUDA device, or `--gpu_ids -1` | The repo's training path is CUDA-first and calls `.cuda()` in multiple places. | Use a CUDA-enabled wheel and a GPU host. CPU training is not a supported target here.
| OOM on 1024p or full-resolution runs | The 24G/full-res recipes are much larger than the 512p baseline. | Prefer the 12G cropped recipe first, reduce `batchSize`, or lower `ngf` / `num_D` if you are still experimenting.
| OOM on feature-conditioned 1024p | Feature conditioning adds extra network and cache pressure. | Use the 12G cropped feature recipe first and confirm the feature-cache workflow separately.
| Missing checkpoint, or resume loads the wrong weights | Wrong `--name`, `--which_epoch`, or `--load_pretrain` path. | Check `checkpoints/<name>/`, verify whether you want `continue_train` versus `load_pretrain`, and use `latest` only when the file exists.
| FP16 import failure | The published FP16 path depends on NVIDIA Apex. | Install Apex or drop `--fp16` and run full precision.
| Multi-GPU behaves strangely | The model uses `DataParallel`, not a full DDP path, and the README says multi-GPU was not fully tested. | Keep the published recipe simple, avoid `pool_size > 0` with multiple GPUs, and expect legacy `torch.distributed.launch` behavior for FP16 recipes.
| VGG download during the first run | `VGGLoss` instantiates `torchvision.models.vgg19(pretrained=True)` unless you disable it. | Use `--no_vgg_loss` for offline smoke tests, or allow the download when you want the full loss term.
| `resize_and_crop` crashes on current torchvision | `data/base_dataset.py` still uses `transforms.Scale`, which is absent in torchvision 0.28.0. | Use `scale_width`, `scale_width_and_crop`, `crop`, or `none` unless you patch the legacy transform path.
| `AttributeError: module 'fractions' has no attribute 'gcd'` | The inspected Python 3.13 runtime removed `fractions.gcd`, but `train.py` still calls it inside `lcm()`. | Patch the helper to use `math.gcd` or run with a compatible Python version before launching training.
| `NotImplementedError: Fake Pool Not Implemented for MultiGPU` | `pool_size > 0` combined with multiple GPUs. | Leave `--pool_size 0` when using multi-GPU training.

## Quick safe defaults

- Start with `512p` before 1024p.
- Add `--no_vgg_loss` for the first smoke unless you specifically want to test the VGG dependency.
- Use `scripts/inspect_training_setup.py` before any manual launch.
- Treat FP16 and multi-GPU as optional, legacy, or environment-sensitive paths.
