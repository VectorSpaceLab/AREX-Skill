# Cross-cutting Troubleshooting

## Import failures from the wrong directory

**Symptom:** `ModuleNotFoundError` for `utils`, `conf`, or `models`.

**Cause:** The repo is not installed as a package; scripts expect the checkout root to be the working directory or import path.

**Recovery:** Run repo commands from the checkout root. For bundled skill helpers, pass `--repo-root <checkout>` when available.

## Missing PyTorch/TorchVision or mismatched wheels

**Symptom:** imports fail for `torch`/`torchvision`, TorchVision custom ops fail, or CUDA appears unavailable despite a visible GPU.

**Cause:** The environment lacks compatible PyTorch/TorchVision wheels or the CUDA build does not match the host driver.

**Recovery:** Install a compatible PyTorch/TorchVision pair for the chosen Python version and backend. Re-run `scripts/check_environment.py --repo-root <checkout> --net resnet18` before launching training or evaluation.

## TensorBoard import problems

**Symptom:** `train.py -h` or `train.py` fails near `from torch.utils.tensorboard import SummaryWriter`.

**Cause:** TensorBoard is not installed even though it is described as optional for visualization. In practice, `train.py` imports `SummaryWriter` at module import time.

**Recovery:** Install TensorBoard or patch the training script for a no-TensorBoard mode before using this workflow.

## CIFAR-100 download or data-location surprises

**Symptom:** A training/evaluation command tries to reach the network, creates `./data`, or fails with dataset download errors.

**Cause:** Both current dataloaders call `torchvision.datasets.CIFAR100(root='./data', download=True)`.

**Recovery:** Pre-stage CIFAR-100 in TorchVision's expected `./data` location, allow the download deliberately, or adapt the dataloader for an existing dataset path. Do not run full training/evaluation as a quick smoke check.

## CUDA unavailable or out of memory

**Symptom:** `.cuda()` errors, `torch.cuda.is_available()` is false, or CUDA OOM appears soon after launch.

**Cause:** The `-gpu` flag moves the model and tensors to CUDA. Large architectures or batches can exceed memory.

**Recovery:** Omit `-gpu` for CPU inspection; verify the CUDA build and driver; reduce batch size; start with smaller networks such as `squeezenet`, `mobilenetv2`, or `resnet18`.

## Checkpoint path or architecture mismatch

**Symptom:** evaluation fails with missing file, unexpected/missing state-dict keys, size mismatch, or top-k shape problems.

**Cause:** `test.py` requires a user-supplied state dict that matches the selected architecture token and CIFAR-100 100-class head.

**Recovery:** Use the same `-net` value that produced the checkpoint; prefer `*-best.pth` for best validation checkpoints; read `sub-skills/evaluation/references/checkpoints.md` for naming and mismatch handling.

## Optional utility dependencies

**Symptom:** `lr_finder.py` fails on `cv2`, or `dataset.py` fails on `skimage`.

**Cause:** These are optional/legacy surfaces, not required for the primary train/eval/model routes.

**Recovery:** Install OpenCV only when intentionally using the LR finder; install scikit-image only when importing or adapting the legacy pickle dataset module.
