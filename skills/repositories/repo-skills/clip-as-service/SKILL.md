---
name: clip-as-service
description: "Guides CLIP-as-service client, server, and CLIP search workflows
  for text/image embeddings, cross-modal ranking, and retrieval services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CLIP-as-service Repo Skill

Use this skill when a task involves the CLIP-as-service package family: `clip-client`, `clip-server`, or the combined `clip-as-service` distribution. It covers running a CLIP embedding service, using the Python client against that service, ranking image/text matches, and building CLIP + AnnLite retrieval flows.

## Quick routing

| User goal | Read |
| --- | --- |
| Connect to a running server, authenticate, call `Client.profile`, `encode`, `rank`, `index`, or `search`, or debug a client error | [client-api](sub-skills/client-api/SKILL.md) |
| Install/run `clip_server`, write a Flow YAML, choose PyTorch/ONNX/TensorRT, tune replicas/protocol/monitoring/TLS/Docker, or debug backend/model startup | [server-runtime](sub-skills/server-runtime/SKILL.md) |
| Build semantic or cross-modal search with CLIP embeddings plus AnnLite, validate `n_dim`, workspace, sharding/polling, and index/search behavior | [search-retrieval](sub-skills/search-retrieval/SKILL.md) |
| Diagnose package install/import, optional dependency, data/config, backend, model-download, or connectivity failures across workflows | [references/troubleshooting.md](references/troubleshooting.md) |
| Check whether this generated skill matches a checkout or package version | [references/repo-provenance.md](references/repo-provenance.md) |
| Check package names, extras, and safe import probes | [references/install-and-package-map.md](references/install-and-package-map.md) and [scripts/check_install.py](scripts/check_install.py) |

## Package layout and install basics

CLIP-as-service is split into independently installable packages:

```bash
pip install clip-client          # client-only machine
pip install clip-server          # PyTorch-backed server package
pip install "clip-server[onnx]"  # optional ONNX Runtime support
pip install "clip-server[tensorrt]"  # optional NVIDIA TensorRT support
pip install "clip-server[search]"    # optional AnnLite search indexer support
```

Install `clip-client` where requests are sent from. Install `clip-server` where the long-running embedding service runs. They do not need to be installed on the same host unless the user is developing or testing both locally.

Minimal import check:

```bash
python - <<'PY'
import clip_client, clip_server
print(clip_client.__version__, clip_server.__version__)
PY
```

To avoid background version-check network calls during automated probes, set `NO_VERSION_CHECK=1` before importing these packages.

## Core operating model

- `clip_server` starts a Jina Flow that receives text/image `Document` objects and returns CLIP embeddings or ranking scores.
- `clip_client.Client` sends requests to a server URI such as `grpc://host:port`, `http://host:port`, or TLS variants such as `grpcs://host:port`.
- Encoding accepts text strings, image URIs, data URIs, local image paths, or DocArray `Document` objects. Ranking expects each root `Document` to contain cross-modal candidates in `.matches` or another configured source.
- Search requires a Flow with a CLIP encoder plus a vector indexer such as AnnLite. Plain encoder-only servers do not own an index.

## Backend boundary

Base PyTorch server usage can run on CPU or CUDA. ONNX, TensorRT, multilingual M-CLIP, Chinese CLIP, search indexing, and flash attention are optional surfaces with separate dependency requirements. Do not claim an optional backend has been verified just because base imports work. Use the nearest sub-skill troubleshooting reference when a backend import or runtime startup fails.

## Safety and self-containment

This skill is self-contained for future agents. Use bundled references and scripts here instead of opening original repository docs, tests, or scripts. The bundled scripts are safe by default: they validate imports, signatures, YAML, or CLI arguments without starting model downloads, contacting servers, or mutating external state unless the user explicitly supplies runtime options.
