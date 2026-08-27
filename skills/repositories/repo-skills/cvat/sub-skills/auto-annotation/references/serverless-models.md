# CVAT serverless model deployment

CVAT documents built-in serverless model examples as Nuclio functions. Treat those examples as deployment patterns: a future operator must provide an official CVAT deployment bundle or equivalent function directory; this generated skill does not bundle model weights, Docker build contexts, or Nuclio function code.

## Deployment patterns

| Pattern | Typical use | Notes |
|---|---|---|
| CPU function deployment | Deploy CPU-optimized functions | Often builds an OpenVINO-style base image and deploys `function.yaml` configurations. |
| GPU function deployment | Deploy GPU-optimized functions | Uses `function-gpu.yaml` configurations and assumes a compatible GPU/NVIDIA runtime. |
| Serverless compose overlay | Enable Nuclio/serverless infrastructure in a CVAT compose stack | Usually combined with the main CVAT compose files from an operator-owned deployment bundle. |

## Built-in function families

The repository documents built-in model families for detection, segmentation, pose, tracking, and interaction across frameworks such as PyTorch, OpenVINO, and TensorFlow. Common examples include SAM, TransT, YOLO-family detectors, HRNet pose estimation, and IOG-style interaction functions.

Treat these as deployment targets, not as runtime skill dependencies.

## CPU versus GPU guidance

- Use CPU deployment patterns for OpenVINO-optimized functions when GPU hardware is unavailable or unnecessary.
- Use GPU deployment only when the function or model is explicitly optimized for GPU and the host has a compatible NVIDIA driver/runtime.
- Do not assume a CPU deployment proves a GPU deployment is viable.
- If a function has both CPU and GPU YAML files, prefer the configuration that matches the host and model requirement.

## Typical Nuclio command shape

A deployment helper usually wraps commands like:

```bash
nuctl create project cvat --platform local
nuctl deploy --project-name cvat --path <function-dir> --file <function-config.yaml> --platform local
nuctl get function --platform local
```

The exact function directory and YAML file depend on the model family and must come from the operator's CVAT deployment assets.

## Safe operator checklist

- Confirm Docker, Nuclio, and network access before attempting deployment.
- Confirm the function directory contains the YAML file expected by the deployment plan.
- Confirm the function name, labels, and model type match the intended UI use.
- Confirm the serverless network hooks and Redis variables match the CVAT deployment.
- Keep heavyweight model downloads and build contexts out of the runtime skill; use only reviewable command shapes here.
