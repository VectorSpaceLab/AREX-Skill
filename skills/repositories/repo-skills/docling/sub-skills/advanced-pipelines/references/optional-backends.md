# Optional Backends and Deployment Planning

Advanced Docling pipelines depend on optional Python extras, system binaries, model artifacts, accelerators, and sometimes remote model APIs. Separate read-only preflight from conversion so checks do not accidentally download models or send data over the network.

## Installation Extras

Use public package extras for the feature being configured:

```sh
pip install "docling[asr]"   # ASR/audio/video transcription
```

VLM, GPU, MLX, OCR, and backend-specific dependencies vary by package version and platform. Prefer the project's current install guidance for the target environment, then run the bundled checker to see which imports are available.

## Safe Preflight Script

The bundled script checks optional imports and binaries without model downloads:

```sh
python scripts/check_optional_backends.py
python scripts/check_optional_backends.py --as-json
```

It intentionally does not:

- instantiate `DocumentConverter` pipelines,
- load Hugging Face or API models,
- call remote model endpoints,
- download model weights,
- convert input documents.

## ASR Requirements

ASR needs both Python packages and the `ffmpeg` executable.

Checklist:

- `docling.pipeline.asr_pipeline.AsrPipeline` imports successfully.
- `docling.datamodel.asr_model_specs` imports successfully.
- `ffmpeg` is on `PATH`.
- The first real conversion can access model artifacts or download from the configured model host.
- Video files contain a decodable audio track.

If `ffmpeg` is missing, install it with the system package manager before debugging Docling code.

## Local VLM Backends

Local VLM conversion commonly uses Transformers or MLX.

Transformers planning:

- Verify `torch`, `torchvision`, and `transformers` import successfully.
- Confirm CUDA only if the installed PyTorch build reports `torch.cuda.is_available()`.
- Expect CPU fallback to be slow for larger models.
- Some model families need compatible Transformers versions or optional libraries.

MLX planning:

- Use only on Apple Silicon (`Darwin` plus `arm64`).
- Verify MLX-related packages import before selecting `MlxVlmEngineOptions`.
- Do not select MLX on Linux, Windows, or Intel macOS.

## GPU and Throughput Planning

For local standard pipeline GPU selection, route ordinary accelerator setup to `pipeline-configuration`. For advanced VLM throughput, consider remote/server runtimes when a GPU server is available.

For VLM API/server throughput:

- Start the inference server separately, such as vLLM, LM Studio, Ollama, or another OpenAI-compatible endpoint.
- Configure `ApiVlmEngineOptions` or a version-compatible API engine option.
- Set `enable_remote_services=True` in `VlmPipelineOptions` only after explicit opt-in.
- Tune API concurrency and Docling page batch size together when the installed version exposes those controls.
- Validate on one page before increasing concurrency.

## Remote Model APIs

Remote model APIs inside a local Docling pipeline differ from the Docling service client:

- They are configured as pipeline engine options.
- They usually expose chat-completions endpoints.
- They may require API keys, headers, model names, timeout, and concurrency settings.
- They may receive page images or document content; confirm data handling before use.
- They require `enable_remote_services=True` or Docling may reject the operation.

For remote `docling-serve` conversion services and `DoclingServiceClient`, use the remote-service-client sub-skill when available.

## Model Downloads and Offline Artifacts

Advanced models usually resolve artifacts at first use. Offline-safe workflow:

1. On a connected machine, prefetch model artifacts with public Docling tooling or the model host's approved mechanism.
2. Copy the complete artifact cache to the target environment.
3. Set `DOCLING_ARTIFACTS_PATH` or a pipeline `artifacts_path` to the copied directory where supported.
4. Run a one-page or short-audio smoke test only after the user approves model execution.

Example environment-level configuration:

```sh
export DOCLING_ARTIFACTS_PATH=/opt/docling-models
```

Never hard-code a local checkout path, conda prefix, or user-specific cache path into reusable skill content.

## Backend Decision Matrix

| Need | Prefer | Avoid |
| --- | --- | --- |
| Portable no-GPU validation | one-page CPU/Transformers smoke after preflight | large multi-page VLM jobs |
| Apple Silicon local VLM | MLX runtime when installed | MLX on non-Apple platforms |
| NVIDIA throughput | API/vLLM or compatible local Transformers with CUDA | assuming CUDA from GPU hardware alone |
| Air-gapped production | prefetched artifacts plus explicit artifact path | first-use downloads |
| Audio/video transcript | ASR extra plus `ffmpeg` | debugging ASR before checking `ffmpeg` |
| Private documents with API VLM | local inference or approved internal endpoint | enabling remote services without approval |

## Suggested Preflight-to-Run Sequence

1. Run `check_optional_backends.py --as-json`.
2. Confirm missing extras/binaries with the user.
3. Confirm model download, GPU/API cost, and remote data policy.
4. Configure the smallest representative conversion.
5. Scale pages, concurrency, and model size only after the small run succeeds.
