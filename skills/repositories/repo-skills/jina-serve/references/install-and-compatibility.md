# Install and Compatibility

## Public installation choices

Use a public package install for normal work:

```bash
pip install -U jina
```

Use a pinned install when reproducing this skill baseline:

```bash
pip install "jina==3.34.1"
```

Jina-serve supports multiple dependency surfaces:

| Install surface | Command shape | Use when | Notes |
|---|---|---|---|
| Minimum/core | `JINA_PIP_INSTALL_CORE=1 pip install jina` | You only need basic Executor/Deployment functionality and want to avoid HTTP/WebSocket/Docker/Hub features. | Core dependencies include DocArray, numpy, grpc/protobuf, PyYAML, packaging, Hubble/JCloud/OpenTelemetry API pieces as defined by package metadata. |
| Perf | `JINA_PIP_INSTALL_PERF=1 pip install jina` | You want core plus performance/observability libraries such as uvloop or Prometheus/OpenTelemetry SDK pieces. | `uvloop` is skipped on Windows by package metadata. |
| Standard/default | `pip install jina` | Most users building local services, HTTP/WebSocket Gateways, Docker-related workflows, and JCloud/Hub operations. | This is the default dependency set in `setup.py`. |
| Development/test | `pip install "jina[devel]"` or CI-specific installs | You are maintaining Jina itself. | Do not install broad dev/test extras for ordinary package usage. |

Conda package variants also exist conceptually as `jina-core`, `jina-perf`, and `jina` in the recipe evidence. Prefer the pip commands above unless your environment already standardizes on Conda packages.

## Minimal import and CLI checks

```bash
python -c "from jina import Executor, Flow, Deployment, Client, requests; import jina; print(jina.__version__)"
jina --version
jina --help
```

For a JSON-style diagnostic, run:

```bash
python scripts/check_jina_install.py
```

## Dependency compatibility notes

- Jina imports DocArray and raises a runtime error when DocArray is not installed correctly. If this happens after an upgrade, reinstall DocArray in the target environment.
- This baseline verified `jina==3.34.1` with DocArray `0.41.0`, GRPC `1.68.0`, Protobuf `5.29.6`, and Pydantic `2.x` in a private inspection environment.
- Older CI paths pin DocArray/Pydantic/Protobuf combinations for compatibility testing. If a user's app must reproduce an older deployment, align all Jina, DocArray, Pydantic, Protobuf, and GRPC versions instead of upgrading one dependency in isolation.
- Some legacy Jina helper paths still import DocArray v1 classes such as `Document`, while the current package dependency range can install DocArray v2. If `Flow.profiling()` or Gateway schema helpers fail with `Cannot import name 'Document' from 'docarray'`, either align to the older compatible DocArray stack for that workflow or avoid claiming that helper as verified.
- `jina-hubble-sdk` may import `pkg_resources`. If imports fail with `ModuleNotFoundError: No module named 'pkg_resources'`, install or pin a setuptools release that still provides `pkg_resources`.
- Jina itself does not choose model-framework dependencies. Install PyTorch, TensorFlow, diffusers, transformers, GPU wheels, or data/model packages in the Executor project environment only when the Executor logic imports them.

## Platform notes

- Python 3.10 is a safe target for this baseline because repository CI exercised Python 3.10 and compiled dependency wheels are broadly available.
- Avoid assuming Python 3.13 compatibility for older Jina deployments or compiled dependency stacks unless you have tested every dependency.
- On macOS/fork-related failures, see the multiprocessing guidance in root and orchestration troubleshooting.
- On Windows, use WSL2 or pip for Jina if Conda install support is unavailable for the exact variant you need.

## Telemetry and privacy

Jina telemetry can report package/dependency versions and start events. To opt out:

```bash
export JINA_OPTOUT_TELEMETRY=1
```

Do not put cloud tokens, `JINA_AUTH_TOKEN`, private registry credentials, or project secrets in generated examples. Pass them through environment variables or secret managers when using JCloud, Hub, Docker, or Kubernetes workflows.
