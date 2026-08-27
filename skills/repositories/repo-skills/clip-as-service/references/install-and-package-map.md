# Install and Package Map

## When to read

Read this before choosing which CLIP-as-service packages or extras to install, before diagnosing imports, or before running a bundled check script.

## Distribution and import names

| Distribution | Import name(s) | Purpose | Base requirements from package metadata |
| --- | --- | --- | --- |
| `clip-client` | `clip_client` | Python client that sends requests to a running CLIP-as-service server. | `jina>=3.12.0`, `docarray[common]>=0.19.0,<0.30.0`, `packaging` |
| `clip-server` | `clip_server` | Jina Executor and Flow resources for serving CLIP embeddings/ranking. | `torch`, `torchvision`, `jina>=3.12.0`, `docarray==0.21.0`, `open_clip_torch>=2.8.0,<2.9.0`, `ftfy`, `regex`, `prometheus-client`, `pillow-avif-plugin` |
| `clip-as-service` | `clip_client`, `clip_server` | Convenience distribution depending on both client and server. | `clip-server`, `clip-client` |

The packages can be installed independently. Put `clip-server` on the serving host and `clip-client` on the caller host; install both only for local development, tests, or single-machine demos.

## Optional extras

| Extra | Install command | Enables | Notes |
| --- | --- | --- | --- |
| ONNX | `pip install "clip-server[onnx]"` | `clip_server.executors.clip_onnx` and ONNX model sessions. | Requires `onnx`, `onnxmltools`, and `onnxruntime`/`onnxruntime-gpu`. Custom ONNX model directories must contain `textual.onnx` and `visual.onnx`. |
| TensorRT | `pip install "clip-server[tensorrt]"` plus NVIDIA runtime prerequisites | `clip_server.executors.clip_tensorrt`. | CUDA-only. CPU cannot validate TensorRT. Engine building may require large GPU workspace. |
| Transformers | `pip install "clip-server[transformers]"` | Multilingual CLIP text encoders. | May load Hugging Face tokenizers/models and require network or cache. |
| Search | `pip install "clip-server[search]"` | AnnLite indexer integration for CLIP Search. | In the source metadata this extra selects `annlite>=0.3.10`. |
| Chinese CLIP | `pip install "clip-server[cn_clip]"` | CN-CLIP model family. | Requires `cn_clip`; treat as optional model-family support. |
| Flash attention | `pip install "clip-server[flash-attn]"` | Optional attention implementation. | Backend-specific; do not install unless the task explicitly needs it. |

## Safe import and environment checks

Use the bundled root script for non-destructive checks:

```bash
python scripts/check_install.py
python scripts/check_install.py --check-search
python scripts/check_install.py --check-cuda
```

The script sets `NO_VERSION_CHECK=1` by default so package imports do not start a background PyPI version check. It does not download CLIP model weights, start a server, or contact an endpoint.

## Known compatibility pitfall

`clip_server.helper` imports `pkg_resources`. Some future Python environments may install a `setuptools` release where `pkg_resources` is unavailable or scheduled for removal. If `ModuleNotFoundError: No module named 'pkg_resources'` appears during import, install a compatible setuptools release, for example:

```bash
python -m pip install "setuptools<81"
```

Record this as an environment compatibility repair, not a CLIP-as-service API change.
