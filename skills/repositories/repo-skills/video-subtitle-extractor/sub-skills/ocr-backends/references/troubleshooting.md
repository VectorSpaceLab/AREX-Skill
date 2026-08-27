# OCR and Backend Troubleshooting

## Paddle/PaddleOCR import errors

- Install PaddlePaddle first with the correct CPU/CUDA index.
- Keep Python version aligned with Paddle/PaddleOCR wheel support.
- If PaddleX performs model-host connectivity checks during import, disable
  that check only for inspection/probe commands; normal offline OCR should use
  bundled local model directories.

## Unsupported language or missing model

Run `scripts/model_config_probe.py` against the VSE source tree. If a language
maps to a directory that is absent, choose a language-group code whose bundled
recognizer exists or add the missing model assets before running extraction.

## Low confidence or missing text

- Check `dropScore` and subtitle-area deviation settings.
- Ensure the language code matches the subtitle script.
- For English mode, VSE strips CJK characters from OCR results.
- Try server/Accurate models only after confirming the correct area/backend.

## CUDA appears unavailable

- A visible NVIDIA GPU is not enough; verify the installed Paddle build is a GPU
  build and matches the driver/CUDA runtime.
- If `paddle.is_compiled_with_cuda()` is false, the environment has CPU Paddle.
- For new hardware requiring newer CUDA than Paddle supports, choose DirectML or
  CPU rather than claiming CUDA coverage.

## ONNX provider unsupported

`HardwareAccelerator` ignores CPU provider and prints unsupported providers.
Install a provider-specific ONNX Runtime package only when the user selected
that path and host support is known.
