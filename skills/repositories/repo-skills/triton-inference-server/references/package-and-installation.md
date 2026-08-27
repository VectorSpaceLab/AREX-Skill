# Package and Installation Guide

## Which Triton surface do you need?

| Need | Preferred surface | Notes |
| --- | --- | --- |
| Production server, model loading, GPU inference, metrics, repository management | NGC `nvcr.io/nvidia/tritonserver:<YY.MM>-py3` container | The container is the normal server delivery vehicle and contains server binary, backends, metrics, and runtime libraries. |
| Client requests to an existing Triton server | `pip install tritonclient[http,grpc]` or container SDK image | `tritonclient` does not start a server; it sends HTTP/gRPC requests. |
| Embedded Python server process | `tritonserver` plus matching native libraries | Import checks are not enough; model load/infer still need the target runtime. |
| Python KServe/Metrics frontends over an embedded server | `tritonfrontend` plus compatible `tritonserver` | `KServeHttp`, `KServeGrpc`, and `Metrics` option classes are optional native bindings. |
| OpenAI-compatible LLM serving | Triton LLM container variant plus OpenAI frontend dependencies | vLLM/TensorRT-LLM backends require GPU runtime, tokenizer/model artifacts, and often Hugging Face access. |

## Version alignment

- Align server container tag, Python wheel versions, backend libraries, and client versions when debugging ABI or protocol issues.
- A `tritonclient` version that is close to the server version is recommended, but protocol compatibility is broader than native-library ABI compatibility.
- Native Python imports can fail when shared libraries are absent or mismatched. Treat errors such as `libtritonserver.so` missing, undefined symbols, or backend load errors as version/runtime alignment problems.

## Read-only preflight

Run the bundled checker before deciding which sub-skill to load:

```bash
python3 scripts/check_triton_environment.py --json
python3 scripts/check_triton_environment.py --url http://localhost:8000 --json
```

The checker imports public packages, probes optional commands, and optionally checks `/v2/health/ready`. It never starts Triton, pulls images, downloads models, or writes outside temporary process memory.

## Safe installation boundaries

- Do not install every backend or test requirement by default. Install only the client/runtime package needed for the chosen workflow.
- Do not mutate an existing production environment to repair native Triton packages without the user's permission.
- Do not copy local environment activation paths into answers. Give portable commands or runtime assumptions instead.
- Treat model repositories, Python backend models, custom backends, repository agents, cache plugins, and cloud credential files as trusted code/data boundaries.
