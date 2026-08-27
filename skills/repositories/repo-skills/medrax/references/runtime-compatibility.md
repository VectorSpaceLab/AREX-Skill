# Runtime compatibility and resource plan

Read this reference before installing or changing dependencies. It records
public compatibility guidance distilled from the MedRAX package metadata and
its model-tool implementations; it does not prescribe a private environment.

## Package baseline

- Distribution: `medrax`, version `0.1.0` in the captured source revision.
- Python metadata: `>=3.10`; Python 3.10 or 3.11 is the conservative choice for
  the pinned Transformers revision and compiled ML wheels.
- Install the repository's declared dependency set with `python -m pip
  install -e .` in an isolated environment. Do not use a system Python or
  mutate a shared environment.
- The package declares a Git-pinned Transformers dependency. Its source imports
  Diffusers, TorchVision, TorchXRayVision, LangChain/LangGraph, Gradio,
  pydicom, bitsandbytes, and other compiled or remote-model packages. If a
  resolver selects an incompatible newest Diffusers/Transformers pair, pin a
  compatible pair based on the package revision and verify imports before
  constructing tools.
- The package metadata declares both `gradio>=3.0.0` and `gradio>=5.0.0`; use a
  Gradio version that is mutually compatible with the installed interface and
  test `create_demo` construction without launching a server.

## Backend profiles

| Profile | Suitable checks | Requirements and limits |
|---|---|---|
| CPU utility | imports, Pydantic schemas, fake-model graph, DICOM, image validation/visualization | no model quality or CUDA inference claim |
| CUDA model | classifier, segmentation, report, VQA, grounding, LLaVA-Med, generation | compatible CUDA Torch, driver, VRAM, model weights/cache; `nvcc` is not needed for pip CUDA wheels unless compiling extensions |
| Remote provider | ChatOpenAI agent and benchmark | OpenAI-compatible endpoint and secret key supplied only at runtime; network and spend approval required |

A CUDA-capable environment can also run CPU utility checks. A CPU import is
not a substitute for model-backed CUDA evidence when the selected tool's
weights, dtype, or implementation require GPU execution. Construct one model
at a time and use 8-bit/4-bit loading only after confirming bitsandbytes and
available memory.

## Model/resource map

| Tool | Default model/resource behavior | Operational rule |
|---|---|---|
| `ChestXRayClassifierTool` | TorchXRayVision DenseNet weights; CUDA default | preflight image and device; scores are likelihood-like outputs, not calibrated diagnoses |
| `ChestXRaySegmentationTool` | TorchXRayVision ChestX-Det PSPNet; writes an overlay | validate exact organ names; metrics use a fixed pixel-spacing assumption and are approximate for ordinary images |
| `ChestXRayReportGeneratorTool` | two Hugging Face vision-encoder-decoder models | expect two model downloads and substantial storage; preserve separate findings/impression sections |
| `XRayVQATool` | CheXagent 2-3B with remote code and bfloat16 default | verify remote-code and memory compatibility; input is a list of image paths plus a prompt |
| `XRayPhraseGroundingTool` | MAIRA-2 with optional 4/8-bit quantization | phrase is required; keep normalized/model boxes distinct from original-image boxes |
| `LlavaMedTool` | LLaVA-Med weights and CUDA-oriented loading | optional broad medical QA; not the preferred detailed CXR tool |
| `ChestXRayGeneratorTool` | manually supplied RoentGen directory | exclude unless weights are legitimately available; generated images are synthetic |
| `DicomProcessorTool` / `ImageVisualizerTool` | no model weights | safest first checks; keep outputs in caller-owned temporary storage |

## Environment smoke sequence

Run these in the target environment, from a neutral working directory:

```bash
python -m pip check
python -I -c "import medrax, medrax.agent; print('package imports')"
python -I -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
python sub-skills/agent-orchestration/scripts/check_medrax_import.py
python sub-skills/image-data-utilities/scripts/validate_image_input.py --help
```

For CUDA, additionally query `torch.cuda.get_device_name(0)` and allocate a
one-element CUDA tensor. Do not download weights merely to make an environment
smoke pass. Record missing caches, unavailable backends, and skipped remote
checks explicitly.
