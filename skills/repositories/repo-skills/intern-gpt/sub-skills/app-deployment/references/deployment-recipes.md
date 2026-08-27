# Deployment recipes

Run these commands from the InternGPT application working directory that contains `app.py`, `model_zoo/`, `certificate/` when HTTPS is enabled, and the installed runtime environment. Replace ports, device ids, and load strings to match the target machine.

## Preflight sequence

1. Decide the smallest tab set and direct load list for the user's task.
2. Validate the plan with `python scripts/validate_load_plan.py ...` from this sub-skill directory.
3. Confirm CUDA and VRAM are suitable for the selected classes. The basic Husky/SAM/OCR set needs a large CUDA GPU; full multimodal launch is much heavier.
4. Confirm `model_zoo/` and any model caches needed by the selected classes are present.
5. If `--https` is used, confirm `certificate/cert.pem` and `certificate/key.pem` exist.
6. Decide how the OpenAI key will be supplied: UI login field, environment variable, or an operator-managed secret injection mechanism.

## Basic image-dialogue service

Use this for image upload, Husky VQA/captioning, SAM click segmentation, and OCR:

```bash
python -u app.py \
  --load "HuskyVQA_cuda:0,SegmentAnything_cuda:0,ImageOCRRecognition_cuda:0" \
  --port 3456 \
  -e
```

Add HTTPS when browser microphone support or remote browser trust requires it:

```bash
python -u app.py \
  --load "HuskyVQA_cuda:0,SegmentAnything_cuda:0,ImageOCRRecognition_cuda:0" \
  --port 3456 \
  --https \
  -e
```

## Full multimodal demo

This enables many image, video, ImageBind, and DragGAN capabilities, but it is dependency-heavy and should not be the default recommendation for a small task:

```bash
python -u app.py \
  --load "ImageOCRRecognition_cuda:0,Text2Image_cuda:0,SegmentAnything_cuda:0,ActionRecognition_cuda:0,VideoCaption_cuda:0,DenseCaption_cuda:0,ReplaceMaskedAnything_cuda:0,LDMInpainting_cuda:0,SegText2Image_cuda:0,ScribbleText2Image_cuda:0,Image2Scribble_cuda:0,Image2Canny_cuda:0,CannyText2Image_cuda:0,StyleGAN_cuda:0,Anything2Image_cuda:0,HuskyVQA_cuda:0" \
  -p 3456 \
  --https \
  -e
```

Use the full command only after staging the full model-zoo/cache set and confirming detectron2, OpenCV, ffmpeg, speech, OpenAI, Stable Diffusion/ControlNet, ImageBind, GRiT, Tag2Text, and action-recognition dependencies.

## Low-memory DragGAN-only HTTPS launch

Use this when the user says "load only DragGAN" or wants the smallest service for the DragGAN tab:

```bash
python -u app.py \
  --load "StyleGAN_cuda:0" \
  --tab "DragGAN" \
  --port 3456 \
  --https \
  -e
```

Notes:

- The DragGAN tab uses `StyleGAN`; do not use `DragGAN_cuda:0` in `--load`.
- `-e` reduces model residency but still expects CUDA and a valid StyleGAN checkpoint.
- The app initializes a speech model on `cuda:0` during startup, so a DragGAN-only plan is lower-memory, not CPU-only.
- HTTPS requires `certificate/cert.pem` and `certificate/key.pem`.

## HTTPS certificate generation

For a self-signed local certificate, create the expected directory and files in the application working directory:

```bash
mkdir -p certificate
openssl req \
  -x509 \
  -newkey rsa:4096 \
  -keyout certificate/key.pem \
  -out certificate/cert.pem \
  -sha256 \
  -days 365 \
  -nodes
```

The app uses `ssl_certfile="./certificate/cert.pem"`, `ssl_keyfile="./certificate/key.pem"`, and disables certificate verification inside Gradio. A browser may still warn about a self-signed certificate.

## OpenAI key and API base

The UI login path expects an OpenAI API key-like string, stores it in `OPENAI_API_KEY`, sets `openai.api_key`, and performs a small validation call. The app also reads `OPENAI_API_BASE` at import time; set it before starting the process if a proxy, compatible endpoint, or private gateway is required.

Example with an operator-managed environment variable:

```bash
export OPENAI_API_BASE="https://your-compatible-api-base"
python -u app.py --load "StyleGAN_cuda:0" --tab "DragGAN" --https -e
```

Do not hard-code real API keys in shell history, compose files, public logs, or generated skill files. Prefer runtime secret injection or the UI password field.

## Docker GPU deployment pattern

The project evidence uses GPU-enabled compose services with NVIDIA device reservations and model/certificate volumes. Treat source compose files as templates because placeholder host paths must be replaced before use.

A safe deployment template shape is:

```yaml
services:
  igpt:
    image: igpt
    build:
      context: .
    container_name: igpt
    restart: unless-stopped
    ports:
      - "7862:7862"
    volumes:
      - "<host-model-zoo>:/InternGPT/model_zoo:ro"
      - "<host-certificate>:/InternGPT/certificate:ro"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    entrypoint: "python"
    command:
      - "-u"
      - "app.py"
      - "--port"
      - "7862"
      - "--load"
      - "StyleGAN_cuda:0"
      - "--tab"
      - "DragGAN"
      - "--https"
      - "-e"
```

Docker checklist:

- Replace `<host-model-zoo>` and `<host-certificate>` with real host directories; do not leave placeholder values.
- Install and verify the NVIDIA container runtime/toolkit on the host before expecting `cuda:0` inside the container.
- Make sure the container working directory contains `app.py`, and that mounted volumes land exactly where the app expects `model_zoo/` and `certificate/`.
- Pin or rebuild dependency images intentionally. The historical Docker patterns install broad Python/CUDA dependencies and may need adjustment for modern base images.
- If the compose implementation ignores `deploy.resources` outside swarm-like contexts, add the runtime's supported GPU flags or equivalent host configuration.
