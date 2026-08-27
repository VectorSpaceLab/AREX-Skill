# Model Zoo Troubleshooting

## Unsupported `-net` value

**Symptom:** `utils.get_network` prints `the network name you have entered is not supported yet` and exits, or a bundled command builder rejects the model name.

**Likely causes:**

- The token is a family label such as `resnet` instead of an exact key such as `resnet18`.
- The token uses README prose rather than the factory token, e.g. `wideresnet-40-10` instead of `wideresnet`.
- The model exists in source but is not wired into `utils.get_network`, e.g. `resnet_in_resnet` or `stochastic_depth_resnet152`.

**Recovery:**

1. Read `model-catalog.md` or run `scripts/model_smoke.py --list`.
2. Use the exact lowercase token in `train.py -net` or `test.py -net`.
3. If you intentionally add a new model, update the source factory and refresh this skill.

## Import path failures

**Symptom:** `ModuleNotFoundError: No module named 'utils'` or `No module named 'models'`.

**Likely cause:** The repository is script-based and expects commands to run with the checkout root on `PYTHONPATH` or as the current working directory.

**Recovery:** Run commands from the checkout root, or use `scripts/model_smoke.py --repo-root <checkout>` so the helper adds the checkout to `sys.path` before importing `utils`.

## CUDA flag misuse

**Symptom:** CUDA-related assertion/runtime errors appear immediately when constructing a model.

**Likely cause:** `args.gpu=True` causes `get_network` to call `.cuda()` before data loading or training starts.

**Recovery:** Use CPU mode for inspection. Only use `-gpu` or `--device cuda` after `torch.cuda.is_available()` is true and the installed PyTorch build matches the host driver.

## Input or output shape mismatch

**Symptom:** convolution or classifier errors mention channel/shape mismatches, or downstream code expects a non-100-class output.

**Likely cause:** These architectures are adapted for CIFAR-100 images: 3 color channels, 32x32 spatial size, and 100 logits.

**Recovery:** Smoke the model with `scripts/model_smoke.py --net <name> --batch-size 1`. If you need another dataset or class count, modify the source model head directly and treat that as repository development, not ordinary use of the existing skill.

## Memory or runtime surprises

**Symptom:** large architectures are slow or run out of memory during smoke, training, or evaluation.

**Likely cause:** families such as attention, Inception-ResNet, WideResNet, and deep residual variants are much larger than SqueezeNet/MobileNet.

**Recovery:** Start with `squeezenet`, `mobilenetv2`, or `resnet18` for smoke checks. Reduce batch size in `training` or `evaluation` before switching to GPU or larger models.
