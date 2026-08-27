# Cross-Cutting Troubleshooting

## When to read

Read this for failures that span client, server, search, installation, optional dependencies, model caches, or backend availability. For workflow-specific details, continue into the nearest sub-skill troubleshooting file.

## Symptom matrix

| Symptom or error fragment | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'clip_client'` | `clip-client` is not installed in the Python environment running the caller. | Install `clip-client`; run `python scripts/check_install.py --client-only`. |
| `ModuleNotFoundError: No module named 'clip_server'` | Server package is missing, or a client-only environment is being used to start a server. | Install `clip-server`; run `python scripts/check_install.py --server-only`. |
| `ModuleNotFoundError: No module named 'pkg_resources'` | Environment has a setuptools version without the legacy `pkg_resources` module. | Install a compatible setuptools release such as `python -m pip install "setuptools<81"`; rerun import checks. |
| `No module named 'onnxruntime'` when importing ONNX executor | ONNX optional extra was not installed. | Install `clip-server[onnx]`; if using CUDA, ensure the ONNX Runtime GPU wheel matches the driver/runtime. |
| TensorRT import error says TensorRT is not installed | TensorRT optional extra or system runtime is missing. | Install NVIDIA TensorRT and `clip-server[tensorrt]` on a CUDA-capable host. Do not treat CPU import checks as TensorRT verification. |
| `No module named 'transformers'` or `No module named 'cn_clip'` | Optional M-CLIP or CN-CLIP model families were selected without extras. | Install `clip-server[transformers]` or `clip-server[cn_clip]`, or choose an OpenCLIP model supported by the base server package. |
| First server startup appears slow or silent | Model weights are downloading or Docker hides progress bars. | Check cache volume and logs. Use a smaller model for smoke tests. Avoid assuming the service is hung until model download/cache status is known. |
| MD5 mismatch or repeated model download failures | Partial/corrupt cache file, network failure, or stale `.part` file. | Remove the affected cached model file and retry with stable network. Do not delete unrelated model caches. |
| `AioRpcError`, `StatusCode.UNAVAILABLE`, or `failed to connect to all addresses` | Server is down, wrong host/port/protocol/TLS mode, firewall/security-group issue, or client/server are on different networks. | Use the client sub-skill connectivity workflow; verify server URI, protocol, TLS suffix, port exposure, and `Client.profile()` against the correct endpoint. |
| Empty embedding returned from the server | Server misconfiguration, wrong port, wrong endpoint, or stale failed server process. | Restart server, confirm Flow has a CLIP encoder, and call `profile()` before a large encode. |
| Search/index endpoint fails but encode works | Server Flow has only an encoder and no indexer, or AnnLite extra is missing. | Use the search-retrieval sub-skill to validate Flow YAML and install `clip-server[search]`. |
| OOM during serving or ranking | Model is too large, replicas/minibatch/prefetch are too high, or TensorRT engine build workspace is too large. | Reduce `minibatch_size`, `replicas`, or Flow `prefetch`; choose a smaller model; for TensorRT, lower batch/profile sizes only if you understand the engine trade-off. |
| Wrong model output dimension breaks retrieval | Search index `n_dim` no longer matches selected CLIP model output dimension. | Validate the search Flow with `sub-skills/search-retrieval/scripts/check_search_config.py --model-name <name>`. Rebuild the index if dimensions changed. |
| `Content must be an Iterable` when calling `encode`, `rank`, `index`, or `search` | A single string was passed directly instead of a list/iterable of strings or Documents. | Wrap one item in a list, e.g. `client.encode(["hello"])`. Ranking requires `Document` roots with `.matches`. |
| Generated skill seems stale | Current checkout or package version differs from provenance. | Read `references/repo-provenance.md` and run `refresh-repo-skill` if commit, package metadata, or public APIs changed. |

## Stop conditions

Stop and ask for explicit user approval before running commands that download large model weights, start a long-running public service, require credentials/tokens, mutate cloud resources, publish packages, delete caches broadly, or run TensorRT engine builds with large GPU memory requirements.
