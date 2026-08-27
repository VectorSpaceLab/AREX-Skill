# Runtime and Installation

## When to read

Read this before installing dependencies, downloading VGG weights, choosing CPU/GPU, or deciding whether a machine can run `neural_style.py`. The repository is a legacy script application, not a pip-installable package.

## Dependency model

The inspected commit has no package metadata or requirements file. Public setup evidence lists:

- TensorFlow;
- OpenCV for Python;
- optional/recommended CUDA and cuDNN for GPU acceleration;
- external VGG-19 MatConvNet weights named `imagenet-vgg-verydeep-19.mat`.

Source and verification facts add these constraints:

- `neural_style.py` uses TensorFlow 1.x APIs: `tf.Session`, `tf.global_variables_initializer`, `tf.train.AdamOptimizer`, and `tf.contrib.opt.ScipyOptimizerInterface`.
- TensorFlow 2.x is not a drop-in runtime because `tf.contrib` is removed.
- A TensorFlow 1.15 CPU-style environment can satisfy CLI help, static checks, and small CPU experiments when paired with OpenCV, SciPy, NumPy, and a protobuf version compatible with TensorFlow 1.x.
- Full rendering also requires the VGG-19 `.mat` model file; the generated skill does not bundle or download it.

## Practical environment guidance

For a disposable CPU-compatible inspection or tiny smoke environment, a modern operator can usually start from Python 3.7 with versions like:

```bash
python -m pip install \
  "tensorflow==1.15.5" \
  "opencv-python-headless==4.5.5.64" \
  "scipy==1.7.3" \
  "protobuf<3.21,>=3.20.3"
```

Use a private virtual environment or conda/micromamba prefix. Do not install these legacy packages into a shared project environment unless the user explicitly wants that mutation.

For GPU rendering, match TensorFlow 1.x, CUDA, cuDNN, Python, driver, and GPU architecture deliberately. The original README's implementation notes mention old Linux, Python 2.7, TensorFlow 0.10, OpenCV 2.4, CUDA 8, and cuDNN 5-era hardware. Newer GPUs can be visible to the host but still incompatible with old TensorFlow GPU wheels. If GPU support is required, verify it with TensorFlow itself before promising a video render.

## VGG-19 weights

`neural_style.py` defaults to:

```text
--model_weights imagenet-vgg-verydeep-19.mat
```

The file is loaded by `scipy.io.loadmat`. Keep it outside generated skills and point `--model_weights` at its actual location. For smoke tests, fail early if the file is missing rather than waiting for graph construction.

## Runtime check helper

Run the bundled runtime checker from the target Python environment:

```bash
python scripts/check_runtime.py --script neural_style.py --model-weights imagenet-vgg-verydeep-19.mat --check-ffmpeg
```

Useful modes:

- omit `--model-weights` when only checking imports and CLI help;
- add `--check-ffmpeg` for video planning;
- add `--check-gpu` only when the user expects TensorFlow GPU execution.

The checker reports TensorFlow version, whether required TensorFlow 1.x symbols are present, OpenCV/SciPy/NumPy imports, script help behavior, VGG file existence, and optional video tool availability.

## Minimal no-render checks

When VGG weights are unavailable, still verify the script surface without rendering:

```bash
python neural_style.py --help
python scripts/inspect_cli_defaults.py --script neural_style.py --format table
```

These checks do not prove a full stylized output will be produced, but they confirm the parser and runtime imports are aligned enough for command construction.

## Safe render smoke pattern

When VGG weights and a compatible runtime are available, use a tiny, disposable CPU smoke before a real run:

```bash
python neural_style.py \
  --content_img lion.jpg --content_img_dir ./image_input \
  --style_imgs kandinsky.jpg --style_imgs_dir ./styles \
  --model_weights imagenet-vgg-verydeep-19.mat \
  --device /cpu:0 --optimizer adam --max_iterations 1 --max_size 64 \
  --img_output_dir ./image_output_smoke --img_name smoke
```

Expected output directory shape:

```text
image_output_smoke/smoke/
  smoke.png
  content.png
  init.png
  style_0.png
  meta_data.txt
```

Do not use a one-iteration smoke to judge artistic quality; it only checks data loading, model loading, graph construction, optimizer execution, and output writing.
