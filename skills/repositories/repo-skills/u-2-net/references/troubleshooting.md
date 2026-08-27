# U-2-Net Cross-Cutting Troubleshooting

## Script-style repository expectations

U-2-Net is a script-style PyTorch repository. The generated skill bundles model code and helper scripts so ordinary guidance does not require opening the original checkout. If a user intentionally validates a local checkout, use the bundled scripts' arguments and treat the checkout as user-supplied runtime input, not as part of the skill.

## Required Python packages

Core PyTorch workflows need:

- `torch`
- `torchvision`
- `numpy`
- `Pillow`
- `scikit-image`
- `opencv-python` or an equivalent `cv2` package for portrait own-image mode
- `matplotlib` for source training compatibility

Run the bundled environment checker:

```bash
python scripts/check_environment.py --check-cuda
```

## Missing pretrained weights

The generated skill does not bundle U-2-Net `.pth` checkpoints. Missing weights are expected in many checkouts. Ask for a local path or explicit download approval before running pretrained inference.

Weight families:

- `u2net.pth`: full salient object detection.
- `u2netp.pth`: lightweight salient object detection.
- `u2net_human_seg.pth`: human/person segmentation.
- `u2net_portrait.pth`: portrait drawing and compositing.

Use random smoke flags only to validate plumbing; never present random outputs as model predictions.

## CUDA and CPU

CUDA is optional for the generated skill's selected required verification scope. CPU can validate imports, architecture, preprocessing, and functional inference when weights are available. Use CUDA only when the user's runtime actually reports `torch.cuda.is_available()`.

## Optional PaddleHub/Gradio demo

The repository includes a PaddleHub/Gradio demo that downloads sample images and uses a PaddleHub `U2Net` module. Treat it as optional and network-bound. Do not install PaddlePaddle/PaddleHub or launch a web server unless the user explicitly asks for that demo.

## Data and training safety

The source training loop is long-running (`epoch_num=100000`) and data-dependent. Use data validators first and ask before downloading datasets, launching training, using GPUs, or overwriting checkpoints.
