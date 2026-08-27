# Cog and API Reference

This file records the source Cog-style prediction surface for Photo2Cartoon. It is reference-only and does not require building Cog during skill drafting.

## Historical build snapshot

The source `cog.yaml` describes this runtime stack:

- Python 3.8
- system packages: `libgl1-mesa-glx`, `libglib2.0-0`
- pip packages: `cmake==3.21.1`, `torch==1.8.0`, `torchvision==0.9.0`, `numpy==1.19.2`, `ipython==7.21.0`, `opencv-python==4.3.0.38`, `face-alignment==1.3.4`, `tensorflow-gpu==2.5.0`
- `dlib` is pre-installed with `pip install dlib`

Treat that snapshot as the source deployment reference, not as the current construction environment.

## Predictor surface

The source predictor exposes:

- `class Predictor(cog.Predictor)`
- `setup(self)`; in the source file it is a no-op
- `predict(self, photo)`

The input annotation is:

```python
@cog.input("photo", type=Path, help="portrait photo (size < 1M)")
```

The predictor flow is:

1. Read the uploaded file with OpenCV.
2. Convert BGR to RGB.
3. Pass the image into the shared cartoon-generation helper.
4. Return the path to the generated image or `None` if no face is detected.

## Shared helper behavior

The source helper:

- builds `ResnetGenerator(ngf=32, img_size=256, light=True)`
- loads `photo2cartoon_weights.pt`
- loads `params['genA2B']`
- uses the preprocessing/segmentation pipeline before inference
- writes a temporary `out.png`

## Adaptation notes

- The source implementation reloads the model in the helper path because `setup()` is empty; moving checkpoint loading into `setup()` is a safe deployment optimization if the runtime allows it.
- Preserve the same return contract: path-like output or `None` on no-face failure.
- Keep the model-side normalization and postprocess identical to the direct recipe.
- When adapting away from Cog, keep the same color-order handling so the output stays consistent.

## Practical checks

- Verify the uploaded image decodes before running inference.
- Verify the output path exists before returning it.
- Verify the output file is a readable image file.
- If the face is missing or too small, return a no-face failure instead of a broken file.
