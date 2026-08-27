# Towhee Triton workflows

This reference covers Triton configuration, model repository/image build planning,
and remote Triton pipeline calls. These operations can be large or
side-effectful; routine skill verification should stop before Docker, Triton
server startup, or GPU execution.

## Triton configuration objects

Towhee stores Triton serving choices on pipeline nodes through `AutoConfig`.
Use the config on model/operator nodes that should be exported or accelerated by
Triton.

Installed signature snapshot:

```python
AutoConfig.TritonCPUConfig(
    num_instances_per_device: int = 1,
    max_batch_size: int = None,
    batch_latency_micros: int = None,
    preferred_batch_size: list = None,
)

AutoConfig.TritonGPUConfig(
    device_ids: list = None,
    num_instances_per_device: int = 1,
    max_batch_size: int = None,
    batch_latency_micros: int = None,
    preferred_batch_size: list = None,
)
```

CPU example:

```python
from towhee import AutoConfig, pipe

cpu_triton = AutoConfig.TritonCPUConfig(
    num_instances_per_device=2,
    max_batch_size=32,
    batch_latency_micros=10000,
    preferred_batch_size=[8, 16],
)

p = (
    pipe.input("x")
        .map("x", "y", lambda x: x, config=cpu_triton)
        .output("y")
)
```

GPU example:

```python
from towhee import AutoConfig

gpu_triton = AutoConfig.TritonGPUConfig(
    device_ids=[0, 1],
    num_instances_per_device=1,
    max_batch_size=128,
    batch_latency_micros=100000,
    preferred_batch_size=[8, 16],
)
```

Important behavior:

- `TritonGPUConfig(device_ids=None)` defaults to `[0]`.
- CPU config sets no GPU device IDs, which produces CPU instance groups in
  generated Triton configs.
- `preferred_batch_size` and `batch_latency_micros` feed Triton's
  `dynamic_batching` block when supplied.
- Pipeline construction details belong elsewhere; use this reference only to
  attach serving configs and explain their consequences.

## Build a Triton model repository

Use `towhee.build_pipeline_model` to create a Triton model repository from a
RuntimePipeline without building a Docker image.

Installed signature snapshot:

```python
towhee.build_pipeline_model(
    dc_pipeline,
    model_root: str,
    format_priority: list,
    parallelism: int = 8,
    server: str = "triton",
)
```

Command shape:

```python
import towhee

ok = towhee.build_pipeline_model(
    dc_pipeline=p,
    model_root="models",
    format_priority=["onnx"],
    parallelism=4,
    server="triton",
)
```

Expected repository shape for a pipeline with one exportable ONNX operator:

```text
models/
├── exported-operator-name/
│   ├── 1/
│   │   └── model.onnx
│   └── config.pbtxt
└── pipeline/
    ├── 1/
    │   ├── model.py
    │   └── pipe.pickle
    └── config.pbtxt
```

Operational details:

- The pipeline model is always named `pipeline` by Towhee's Triton builder.
- Exportable neural operators are converted according to `format_priority`.
  ONNX is the documented and tested common path.
- If no requested format intersects an operator's supported formats, that
  operator is not exported as a standalone Triton model.
- The generated pipeline Python backend model uses the pickled pipeline DAG and
  can call exported submodels through Triton BLS when accelerator info is set.
- Existing destination directories may fail if a model subdirectory already
  exists; build into a fresh model root or clean intentionally.

## Build a Docker image

Use `towhee.build_docker_image` when the user explicitly wants an image that
contains the model repository and Triton runtime.

Installed signature snapshot:

```python
towhee.build_docker_image(
    dc_pipeline,
    image_name: str,
    cuda_version: str,
    format_priority: list,
    parallelism: int = 8,
    inference_server: str = "triton",
)
```

Command shape:

```python
import towhee

towhee.build_docker_image(
    dc_pipeline=p,
    image_name="clip:v1",
    cuda_version="11.7",
    format_priority=["onnx"],
    parallelism=4,
    inference_server="triton",
)
```

Docker build behavior:

- Towhee serializes the pipeline DAG and server config into a temporary
  workspace, selects a CUDA-specific Triton Dockerfile, and runs
  `docker build -t <image_name> .`.
- Supported CUDA selectors are `"11.3"`, `"11.4"`, `"11.6"`, `"11.7"`, and
  `"117dev"`.
- The bundled Dockerfiles use NVIDIA Triton base images, install Python/Torch,
  install ONNX tooling, install Towhee packages, and run the Triton builder
  inside the image to populate `/workspace/models`.
- Unsupported CUDA selectors return `False` before Docker build.

Do not run this in routine verification. It can download large base images,
install large ML packages, require Docker daemon access, and leave local images.

## Start Triton from built artifacts

Once a model repository exists and deployment is explicitly requested, Triton
startup shapes are:

```bash
tritonserver --model-repository "$(pwd)/models"
```

or, for a built image:

```bash
docker run -td --gpus=all --shm-size=1g \
  -p 8000:8000 -p 8001:8001 -p 8002:8002 \
  clip:v1 \
  tritonserver --model-repository=/workspace/models
```

Readiness log lines to expect:

```text
Started GRPCInferenceService at 0.0.0.0:8001
Started HTTPService at 0.0.0.0:8000
Started Metrics Service at 0.0.0.0:8002
```

## Remote Towhee Triton pipeline client

Towhee exposes a pipeline-oriented HTTP Triton client as `towhee.triton_client`.
It talks to the generated `pipeline` model by default.

Installed behavior snapshot:

```python
from towhee import triton_client

client = triton_client.Client(url="127.0.0.1:8000")
single = client("one-input")
batch = client.batch(["a", "b", "c"], batch_size=4, safe=False)
client.close()
```

Call shape details:

- `Client(url, model_name="pipeline")` constructs an async Triton HTTP client.
- `client(x)` serializes one pipeline input as a BYTES tensor named `INPUT0`
  with shape `[1, 1]`, calls Triton, deserializes `OUTPUT0`, and returns the
  first item of the deserialized batch.
- `client(a, b, ...)` treats multiple positional arguments as a single pipeline
  input tuple/list; use this for multi-input pipelines.
- `client.batch(pipe_inputs, batch_size=4, safe=False)` chunks the list of
  pipeline inputs, sends chunks concurrently, and flattens per-chunk results.
- With `safe=True`, a failed chunk logs the exception and returns `None` for each
  input in that chunk. With `safe=False`, the exception propagates.
- Use a context manager to guarantee close:

```python
from towhee import triton_client

with triton_client.Client("127.0.0.1:8000") as client:
    print(client("hello"))
    print(client.batch(["a", "b"], batch_size=2, safe=True))
```

## In-server BLS Triton client

Towhee also has an internal `TritonClient` for Python backend/BLS model code.
It is not the same as the remote pipeline client.

```python
from towhee.serve.triton.triton_client import TritonClient

model = TritonClient(
    model_name="exported_model",
    input_names=["input0"],
    output_names=["output0"],
)
outputs = model(torch_tensor)
```

Use it only inside Triton Python backend contexts where Triton's `pb_utils` is
available. It converts Torch tensors to Triton tensors, sends an
`InferenceRequest`, raises a Triton model exception on backend error, and returns
a Torch tensor for one output or a list of tensors for multiple outputs.

## Side-effect boundary checklist

Stop before executing build/start commands when any of these are true:

- the user only asked for a skill check, example, command plan, or code review;
- Docker daemon availability is unknown;
- GPU/CUDA/NVIDIA runtime compatibility is unknown;
- model/operator exports would download weights or large packages;
- a model repository/image already exists and overwrite policy is unclear;
- ports 8000, 8001, 8002, or requested service ports may be in use.
