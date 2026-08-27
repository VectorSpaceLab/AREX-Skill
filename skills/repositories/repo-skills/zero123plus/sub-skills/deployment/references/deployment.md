# Zero123Plus deployment surfaces

This reference summarizes the repo's demo and serving surfaces so a future agent
can adapt them without reopening the source UI or deployment files. It is scoped
to deployment behavior only. For the model call, scheduler, ControlNet variants,
output camera layout, and batch/image-generation commands, use the sibling
[`generation` sub-skill](../../generation/SKILL.md).

## Surface summary

| Surface | Intended use | Runtime shape | Important caveats |
| --- | --- | --- | --- |
| Streamlit demo | Local interactive demo | `streamlit run` launches a UI with upload, example buttons, preprocessing toggles, progress, and a grid result. | The source module has top-level side effects: dependency checks, model loading, SAM initialization, and possible downloads happen during app startup/import. Do not use it as a cheap import smoke test. |
| Gradio demo | Local or hosted interactive demo | A Gradio Blocks app loads the pipeline and SAM once, exposes advanced preprocessing sliders/options, queues work, and displays six tiles. | The source launcher defaults to a public share tunnel and a fixed CUDA device. SAM checkpoint must already exist or be prepared during build/setup. |
| Bundled Gradio template | Safer adaptation starting point | [`../scripts/launch_gradio_demo.py`](../scripts/launch_gradio_demo.py) provides a minimal upload/steps/guidance/seed UI and six-view gallery. | It intentionally omits SAM/rembg preprocessing and blocks downloads unless `--allow-download` is passed. Use it for controlled demos or CI-friendly templates. |
| Cog/Replicate predictor | API-style prediction service | Cog calls `Predictor.setup()` once, then `predict(image, remove_background, return_intermediate_images)` per request. | The source predictor used a fixed container cache and `pget`. The bundled template makes model/cache paths configurable and avoids model loading on import. |
| Docker image | GPU demo container | CUDA/cudnn Ubuntu base, Python/pip dependencies, non-root user, build-time checkpoint/model cache warmup, Gradio command. | Build-time downloads are large and should be explicitly approved. The image is tailored to a GPU runtime. |
| Gitpod workspace | Lightweight workspace bootstrap evidence | Installs requirements and attempts to run the app. | Treat it as bootstrap evidence, not the canonical Streamlit launch recipe; a Streamlit app should normally be started with `streamlit run`. |

## Dependency and bootstrap pattern

The README-level local path is:

1. Install the extra demo dependencies with the repo requirements.
2. Launch Streamlit with `streamlit run` or Gradio with Python.
3. Ensure a CUDA-enabled PyTorch runtime before attempting a real generation-backed demo.
4. Pre-stage model and checkpoint caches when the environment must run without network access.

The dependency evidence includes:

- Core generation/runtime: `torch`, `torchvision`, `diffusers==0.20.2`,
  `transformers==4.29.2`, `numpy`, `huggingface_hub`.
- Demo/UI: `streamlit==1.22.0`, `altair<5`, `gradio>=3.50`, `fire`.
- Background removal: `rembg`, `opencv-contrib-python`, and
  `segment_anything` plus the SAM ViT-H checkpoint.
- Cog package set: GPU enabled, Python 3.11, pinned `accelerate`, `diffusers`,
  `huggingface-hub==0.18.0`, `numpy`, `rembg`, `torch==2.0.1`,
  `torchvision==0.15.2`, and `transformers==4.29.2`; `pget` is installed in
  the Cog build for archive downloads.

Prefer pinned or known-compatible versions when adapting old demo code. The
verified inspection environment showed the repo's demo/Cog imports working with
`diffusers==0.20.2`, `huggingface_hub==0.18.0`, `streamlit==1.22.0`,
`gradio==3.50.2`, `rembg==2.0.51`, and CUDA-capable `torch==2.0.1`.

## Streamlit behavior

The Streamlit surface is the simplest local README path, but it is not a library
module:

- Startup performs dependency checks and then loads the Zero123Plus pipeline.
- If an `HF_TOKEN` environment variable is present, the app logs in to
  Hugging Face before model loading.
- SAM is initialized as a cached resource and may download the SAM ViT-H
  checkpoint into a local temporary checkpoint directory if absent.
- A global lock serializes generation work so simultaneous UI actions do not
  run the same pipeline concurrently.
- Progress messages cover queue wait, input preparation, diffusion steps, and
  post-processing.

Use Streamlit when the user wants the source-like UI semantics and accepts the
startup side effects. Do not import the source Streamlit module just to inspect
functions; use this skill's references and the bundled templates instead.

## Gradio behavior

The Gradio surface is more structured for hosted demos:

- Startup loads the v1.1 base pipeline, configures the trailing Euler ancestral
  scheduler, moves the pipeline to CUDA device 0, and initializes a SAM
  predictor from a local checkpoint.
- The UI has a main image upload, example images, an advanced-options accordion,
  a generate button, a processed-image preview, and six output image tiles.
- Generation is queued and launched with sharing enabled in the source demo.
- Input preprocessing can remove the background and rescale/recenter the object;
  output post-processing can remove backgrounds from the generated views.

Use the bundled Gradio launcher for controlled deployments because it exposes
host/port/share options and blocks downloads by default. Use the source Gradio
behavior from this reference only when intentionally recreating the full UI.

## Cog predictor behavior

The Cog surface is an API template rather than a browser UI:

- `setup()` is responsible for preparing weights, loading the local pipeline,
  setting the scheduler, and moving the pipeline to CUDA.
- The prediction API preserves three inputs:
  - `image`: input image path; aspect ratio should be square and recommended
    resolution is at least 320 x 320.
  - `remove_background`: when true, `rembg` is applied to the input image before
    inference.
  - `return_intermediate_images`: when true, the processed input image is saved
    and prepended to the returned output list.
- The source predictor downloads an archive with `pget` when weights are absent,
  loads with `local_files_only=True`, runs 75 inference steps, saves outputs to a
  temporary output directory, and returns paths.

Use [`../scripts/cog_predictor.py`](../scripts/cog_predictor.py) as the starting
point for new Cog deployments. Its environment variables let the future agent
choose a local weights directory, a model source, a custom pipeline source, a
scratch directory, an output directory, and whether downloads are allowed.

## Docker and Gitpod evidence

The Dockerfile evidence shows a GPU-oriented hosted-demo image:

- CUDA 12.1/cudnn8 Ubuntu base.
- System packages: compiler toolchain, Python 3.9, pip, git, and ffmpeg.
- Requirements are installed before copying the app as a non-root user.
- A build step warms/places checkpoints and model cache.
- The container command runs the Gradio demo.

The Gitpod evidence is much lighter: it installs requirements and executes the
app file directly. For reliable remote preview, translate that intent into an
explicit Streamlit or Gradio launch command with host/port settings rather than
assuming direct Python execution starts a web server.

## Download posture

Classify downloads explicitly before launching anything:

- Hugging Face model/custom-pipeline downloads: triggered by
  `DiffusionPipeline.from_pretrained` unless local-only loading is used.
- SAM checkpoint download: needed for the full source background-removal path.
- rembg/ONNX model downloads: may occur on first background-removal use.
- Cog weight archive download: performed with `pget` only when the predictor
  setup path is configured to allow it and the weights directory is missing.

`download_checkpoints.py` is **reference-only**. It demonstrates build-time cache
warming by downloading the SAM checkpoint and causing the Diffusers pipeline to
resolve weights, but it mutates local caches and performs network access.

`util/download_weights.py` is **excluded/buggy** for runtime guidance. It uses an
invalid path-existence expression and is incomplete relative to the safer bundled
Cog/Gradio templates. Do not tell users to rely on it unless they first repair
and validate it outside the generated skill.

## Policy note for deployments

The repository evidence states that code is Apache-2.0 but released model
weights are CC-BY-NC 4.0. For commercial or hosted product deployments, flag the
non-commercial weight license before giving implementation steps.
