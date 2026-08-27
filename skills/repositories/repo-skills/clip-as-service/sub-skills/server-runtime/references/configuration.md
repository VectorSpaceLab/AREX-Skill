# Server Configuration

## Installation variants

```bash
pip install clip-server
pip install "clip-server[onnx]"
pip install "clip-server[tensorrt]"
pip install "clip-server[transformers]"
pip install "clip-server[cn_clip]"
pip install "clip-server[search]"
```

Install only the extras needed by the selected runtime or workflow. TensorRT has system/runtime prerequisites beyond Python wheels; do not install it for CPU-only use.

## CLI contract

`clip_server` is started through Python module execution:

```bash
python -m clip_server
python -m clip_server my-flow.yml
cat my-flow.yml | python -m clip_server -i
```

If no argument is supplied, the package loads the built-in PyTorch Flow. A single non-`-i` argument is interpreted as a Flow YAML path or a package resource name such as `onnx-flow.yml`. Put model and server settings in YAML; the CLI itself is intentionally small.

Set `NO_VERSION_CHECK=1` in automated or offline contexts to skip background version checks.

## Built-in Flow shape

PyTorch template:

```yaml
jtype: Flow
version: '1'
with:
  port: 51000
executors:
  - name: clip_t
    uses:
      jtype: CLIPEncoder
      metas:
        py_modules:
          - clip_server.executors.clip_torch
    timeout_ready: 3000000
    replicas: 1
```

ONNX and TensorRT templates are the same shape but use `clip_server.executors.clip_onnx` or `clip_server.executors.clip_tensorrt`. Bundled copies live under this sub-skill's `scripts/` directory.

## CLIPEncoder runtime parameters

Common parameters across runtimes:

| Parameter | Meaning |
| --- | --- |
| `name` | Model name. Default is `ViT-B-32::openai`. Runtime support differs by model. |
| `num_worker_preprocess` | CPU workers used before inference. Default 4. |
| `minibatch_size` | Minibatch size for preprocessing/encoding. Default 32; reduce for OOM. |
| `access_paths` | DocArray access paths to traverse. Default `@r`. `traversal_paths` is deprecated but still accepted as a warning path. |

PyTorch-specific parameters:

| Parameter | Meaning |
| --- | --- |
| `device` | `cpu` or `cuda`; default auto-detects CUDA availability. |
| `jit` | Enable JIT compilation. Default false. |
| `dtype` | `fp32`, `fp16`, `bf16`, or torch dtype. Defaults to `fp32` on CPU and `fp16` on non-CPU devices. |

ONNX-specific parameters:

| Parameter | Meaning |
| --- | --- |
| `device` | `cpu` or `cuda`; default auto-detects CUDA availability. |
| `model_path` | Optional directory containing `textual.onnx` and `visual.onnx`. |
| `dtype` | `fp32` on CPU by default, `fp16` on CUDA by default. |

TensorRT-specific parameters:

| Parameter | Meaning |
| --- | --- |
| `device` | Must start with `cuda`; TensorRT executor asserts CUDA availability. |

## Custom model/config examples

Force CPU PyTorch and smaller minibatches:

```yaml
jtype: Flow
version: '1'
with:
  port: 51000
  protocol: grpc
  prefetch: 4
executors:
  - name: clip_t
    uses:
      jtype: CLIPEncoder
      with:
        name: ViT-B-32::openai
        device: cpu
        jit: false
        minibatch_size: 8
      metas:
        py_modules:
          - clip_server.executors.clip_torch
```

Use ONNX with a custom exported model directory:

```yaml
jtype: Flow
version: '1'
with:
  port: 51000
executors:
  - name: clip_o
    uses:
      jtype: CLIPEncoder
      with:
        name: ViT-B/32
        model_path: custom-model
      metas:
        py_modules:
          - clip_server.executors.clip_onnx
```

The ONNX model directory must contain `textual.onnx` and `visual.onnx`, and `name` must match the model family used to export those files.

## Flow-level settings

| Setting | Location | Meaning |
| --- | --- | --- |
| `port` | top-level `with` | Gateway port exposed to clients. |
| `protocol` | top-level `with` | `grpc`, `http`, or `websocket`. Client URI must match. |
| `cors` | top-level `with` | Adds CORS middleware for HTTP. |
| `prefetch` | top-level `with` | Limits in-flight streamed requests; lower values can reduce OOM. |
| `replicas` | executor item | Runs multiple CLIP executor replicas for horizontal scaling. |
| `monitoring`, `port_monitoring` | Flow/executor | Exposes Prometheus metrics. |
| `ssl_certfile`, `ssl_keyfile`, `uvicorn_kwargs` | Flow | TLS certificate/key configuration. |

## GPU assignment

Use `CUDA_VISIBLE_DEVICES` normally to restrict GPUs. The documented round-robin form `CUDA_VISIBLE_DEVICES=RR` assigns replicas across visible GPUs in a rotating pattern. `CUDA_VISIBLE_DEVICES=RR0:2` restricts round-robin to a slice of devices.

## Docker pattern

A typical server container maps the external port and preserves model cache:

```bash
docker run -p 51009:51000 -v "$HOME/.cache:/home/cas/.cache" --gpus all jinaai/clip-server
```

Use backend-specific image tags or command arguments for ONNX/TensorRT. Docker startup may be quiet while model weights are downloaded.

## Static validation

Before starting a long-running service or triggering model downloads, validate YAML shape:

```bash
python sub-skills/server-runtime/scripts/check_server_config.py my-flow.yml --expected-runtime torch
```
