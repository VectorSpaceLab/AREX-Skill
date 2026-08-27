# OCR Inference Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| First prediction downloads weights | Default checkpoint file is absent. | Pre-download intentionally, pass `--checkpoint`, or postpone model construction until network is allowed. |
| `torch.cuda.is_available()` false despite GPU | CPU-only PyTorch installed or driver/runtime mismatch. | Install a matching CUDA PyTorch/TorchVision pair; otherwise use `--no-cuda`. |
| `operator torchvision::nms does not exist` or `timm` import fails | Mismatched Torch/TorchVision wheel variants. | Reinstall Torch and TorchVision from the same CPU or CUDA index. |
| Prediction changes between retries | Sampling temperature and model uncertainty. | Lower `--temperature`, crop the image better, or use a clearer capture. |
| Empty output when no image provided | Clipboard unsupported or no previous image. | Pass a file path explicitly or copy a valid image first. |
| `--show` fails | XeLaTeX/ImageMagick/preview rendering stack missing. | Use `--katex` or inspect raw LaTeX; install TeX rendering tools only if needed. |
| Clipboard copy warning/failure | Headless environment or clipboard backend unavailable. | Ignore if stdout has the prediction; use CLI file mode in headless jobs. |

Stop before full inference when downloads, large model loading, GPU allocation,
or external rendering are outside the user's permission or budget.
