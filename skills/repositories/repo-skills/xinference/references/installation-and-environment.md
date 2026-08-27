# Installation and Environment

Read this when a task starts with installing Xinference, checking package health,
choosing optional extras, or working from an editable source checkout.

## Package installation patterns

| Need | Install pattern | Notes |
| --- | --- | --- |
| Base service/API/CLI surface | `pip install xinference` | Installs the package and base dependencies, including service and client surfaces. |
| Source checkout for inspection or lightweight development | `NO_WEB_UI=1 pip install -e .` | Skips the in-tree Web UI build when Python-only package inspection is enough. |
| Documentation build | `pip install "xinference[doc]"` | Use only for docs tasks. |
| vLLM backend | `pip install "xinference[vllm]"` | Linux/CUDA-oriented; verify model-family support before launch. |
| SGLang backend | `pip install "xinference[sglang]"` | Kept separate from `all` because of dependency conflicts. |
| MLX backend | `pip install "xinference[mlx]"` | macOS arm64 / Apple silicon only. |
| Embedding or rerank models | `pip install "xinference[embedding]"` or `pip install "xinference[rerank]"` | Pulls family-specific dependencies; still may need model downloads. |
| Image, video, or audio families | `pip install "xinference[image]"`, `"xinference[video]"`, or `"xinference[audio]"` | Large optional stacks; select only when the workflow needs them. |
| OpenTelemetry | `pip install "xinference[otel]"` | Observability add-on, not a model backend. |
| All common model extras | `pip install "xinference[all]"` | Heavy; does not include SGLang. Prefer scoped extras. |

## Environment selection rules

- Python support is `>=3.10`. Use a supported Python whose wheel ecosystem
  matches the chosen backend.
- Install the smallest extra set that covers the selected model families and
  required backends. Do not use `all` as a troubleshooting shortcut before the
  missing family/backend is identified.
- A package import or CLI `--help` check proves only the package surface. It does
  not prove model downloads, GPU kernels, vLLM/SGLang/MLX runtime health, or a
  specific model family launch.
- For source checkouts, editable install builds can invoke the Web UI staging
  path. Use `NO_WEB_UI=1` when the task is Python-only and static Web UI assets
  are irrelevant.
- Model virtual environments are a runtime feature for model dependency
  isolation. They are not a substitute for selecting compatible package extras
  in the host service environment.

## Safe smoke checks

Prefer the bundled helper first because it checks importability, client aliases,
and console entry points without starting services:

```bash
python scripts/check_xinference_install.py --run-cli-help
```

The manual equivalent is:

```bash
python - <<'PY'
import xinference
from xinference.client import Client, AsyncClient, RESTfulClient
print(getattr(xinference, "__version__", "unknown"))
print(Client, AsyncClient, RESTfulClient)
PY

xinference --help
xinference-local --help
xinference-supervisor --help
xinference-worker --help
```

Use `scripts/inspect_xinference_interfaces.py` when you need concrete public
signatures for `Client.launch_model`, `register_model`, model handles, or API
helpers.

## Backend preparation checklist

1. Identify the model family and task: LLM, embedding, rerank, image, audio,
   video, flexible, or multimodal.
2. Check whether the model requires a local path, a model hub download, or a
   custom registration file.
3. Select the backend or engine (`transformers`, `llama_cpp`, `vllm`, `sglang`,
   `mlx`, diffusers/audio family engines, etc.).
4. Confirm platform gates: Linux/CUDA for vLLM or SGLang, macOS arm64 for MLX,
   vendor hardware for Intel/MUSA/NPU paths, and enough memory for the model.
5. Install only the extra group and runtime wheels needed by that path.
6. Run backend-specific smoke tests only after credentials, model source,
   network, and hardware are available.

## Source checkout build gotchas

- Editable installs can try to build or stage the Web UI. `NO_WEB_UI=1` avoids
  the frontend build for Python-only inspection.
- If a wheel/sdist build must include the Web UI, Node dependencies and the
  frontend build chain become part of the package build, not part of ordinary
  runtime usage.
- Do not publish local build directories, cache paths, or environment prefixes
  in user-facing instructions.

## When to route onward

- CLI command construction or service startup: `sub-skills/serving-and-cli/`.
- Python clients or HTTP/OpenAI-compatible requests: `sub-skills/client-and-api/`.
- Model family, backend, custom model JSON, LoRA, virtualenv, or memory choices:
  `sub-skills/models-and-backends/`.
- Auth, metrics, logging, persistence, Web UI serving, Docker, Kubernetes, or
  network exposure: `sub-skills/operations-and-security/`.
