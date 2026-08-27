# Installation and Runtime Reference

## Repository shape

VSE is a Python application/source tree. The evidence baseline used by this
skill exposes `backend`, `ui`, `gui.py`, `requirements.txt`,
`requirements_directml.txt`, bundled PaddleOCR V5 model directories, and
platform-specific VideoSubFinder binaries. There is no `pyproject.toml` or
`setup.py`, so future agents should not claim `pip install video-subtitle-extractor`
installs the application.

## Python and base dependencies

The public README states Python 3.12+ for current source runs. The baseline CPU
path is:

```bash
python -m venv videoEnv
# activate the environment using the platform's normal venv command
pip install paddlepaddle==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
pip install -r requirements.txt
```

The requirements include OpenCV, PaddleOCR, PaddlePaddle, PySide6,
qfluentwidgets, pysrt, wordsegment, scikit-image, Levenshtein, shapely, and
imageio-ffmpeg. Because the app is source-run, launch commands normally run
from a VSE source checkout.

## Backend variants

### CPU baseline

Use CPU when the user has no verified accelerator, wants portable behavior, or
is only inspecting/configuring the application. CPU can run Fast/Auto mode but
may use smaller models and be slower.

### CUDA / NVIDIA GPU

The README documents PaddlePaddle GPU installs via backend-specific indexes,
for example CUDA 11.8:

```bash
pip install paddlepaddle-gpu==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
pip install -r requirements.txt
```

Validate the NVIDIA driver, CUDA wheel tag, Paddle version, and GPU visibility
before claiming GPU acceleration. New NVIDIA 50-series hardware may require a
newer CUDA runtime than current Paddle support; the upstream README recommends
DirectML universal builds for that case.

### DirectML / ONNX providers

For Windows AMD/Intel/NVIDIA DirectML acceleration, the README path is:

```bash
pip install paddlepaddle==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
pip install -r requirements.txt
pip install -r requirements_directml.txt
```

`requirements_directml.txt` contains `paddle2onnx` and `onnxruntime-directml`.
Other ONNX providers such as CoreML, ROCm, OpenVINO, Metal, or CUDA are treated
as advanced/partly untested paths; select provider wheels that match the host.

## Launch commands

```bash
# GUI extraction and Sync Timeline page
python gui.py

# interactive hard-subtitle extraction CLI
python -m backend.main

# Sushi timeline synchronization CLI
python -m backend.sushi --src source_video.mkv --dst destination_video.mkv --script source_subtitle.srt -o synced.srt
```

`backend.main` prompts for a video path and subtitle area. For non-interactive
planning, use the bundled helper
`sub-skills/extraction-workflows/scripts/vse_cli_plan.py` rather than trying to
feed prompts blindly.

## Minimal verification commands

From a prepared VSE source-run environment:

```bash
python scripts/vse_environment_probe.py --repo-root /path/to/vse --json
python -m backend.sushi --help
```

If imports trigger PaddleX/PaddleOCR model-host checks during inspection, set
`PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` for the probe only; do not present
that as a universal runtime requirement.
