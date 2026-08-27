# Runtime Requirements

This reference summarizes the Pyserini 2.3.0 install/runtime stack and the dependency choices future agents should make before starting retrieval, evaluation, REST, or MCP work.

## Required Baseline

| Component | Required choice | Why it matters | Quick check |
| --- | --- | --- | --- |
| Python | Use Python 3.12 for the safest target. Pyserini metadata requires `>=3.12`. | The project docs and verified package facts are built around Python 3.12; newer versions can expose dependency wheel gaps. | `python -c "import sys; print(sys.version)"` |
| Java | Use JDK 21. | Pyserini talks to Anserini/Lucene through PyJNIus and Java-backed classes. | `java -version` |
| PyJNIus | Installed by Pyserini metadata as `pyjnius>=1.7.0`. | PyJNIus configures and starts the JVM for Lucene-backed imports. | `python -c "import jnius_config, jnius; print('pyjnius ok')"` |
| Torch | Installed by metadata as `torch>=2.9`; choose CPU or CUDA deliberately. | Encoder/model workflows import Torch, but sparse Lucene setup does not require GPU Torch. | `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"` |
| Transformers | Installed by metadata as `transformers>=5,<6`. | Encoder workflows and some dense retrieval paths depend on it. | `python -c "import transformers; print(transformers.__version__)"` |
| ONNX Runtime | Installed by metadata as `onnxruntime>=1.23`. | Lucene dense/HNSW ONNX encoder workflows can use it. | `python -c "import onnxruntime; print(onnxruntime.__version__)"` |
| Faiss | Optional; install only for Faiss-backed dense search/index/server paths. | Pyserini does not declare Faiss in core metadata because CPU/GPU packages differ by platform. | `python -c "import faiss; print('faiss ok')"` |
| REST/MCP deps | FastAPI, Uvicorn, FastMCP, PyYAML are core metadata dependencies. | Server import paths can also pull Faiss and Java-backed search classes depending on modules imported. | `python scripts/check_pyserini_runtime.py --check-server` |

## Install Profiles

### Core Sparse/Index/Search User

Use this profile when the user wants BM25/Lucene indexing/search/fetch and no GPU/model execution yet.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pyserini==2.3.0
python -m pip check
python scripts/check_pyserini_runtime.py --check-lucene
```

This installs Torch/Transformers/ONNX Runtime because they are core dependencies in current Pyserini metadata, but it does not require CUDA or Faiss.

### CPU-Only Dense Setup

Use this when the user wants dense retrieval or encoders on CPU, or wants to validate Faiss-backed paths without CUDA.

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install pyserini==2.3.0 faiss-cpu
python -m pip check
python scripts/check_pyserini_runtime.py --check-lucene --check-faiss
```

Set dense commands to CPU explicitly when the sibling dense workflow exposes a device flag, for example `--device cpu`. CPU-only installs are slower but avoid CUDA wheel/driver mismatches.

### CUDA Torch Or GPU Faiss Setup

Use this only when the user has a compatible GPU stack and requests GPU encoding/search. Choose packages from the platform's official channels instead of guessing.

- Install the Torch wheel matching the machine's CUDA runtime from the PyTorch selector.
- Prefer conda/mamba for GPU Faiss when PyPI wheels are missing or incompatible.
- Confirm the runtime before handing off to dense workflows:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
python -c "import faiss; print('faiss gpu helpers:', hasattr(faiss, 'StandardGpuResources'))"
python scripts/check_pyserini_runtime.py --check-faiss
```

If `torch.cuda.is_available()` is false, use CPU commands or fix the driver/wheel mismatch before running `--device cuda` workflows.

### REST/MCP Setup

REST and MCP server modules are included in the core dependency set, but server imports can pull searchers and optional resources.

```bash
python -m pip install pyserini==2.3.0
python -m pip install faiss-cpu  # when serving faiss indexes or when server imports require faiss
python scripts/check_pyserini_runtime.py --check-server
```

Configuration, auth, cache, and alias details are owned by `../../serving-and-agent-tools/SKILL.md`.

### Optional Multimodal/UniIR Setup

Use only when the user asks for optional multimodal search or the optional encoder modules.

```bash
python -m pip install 'pyserini[optional]'
```

If this extra conflicts with an existing model stack, install core Pyserini first, then add optional dependencies in a fresh environment or with explicit pins chosen for the target workflow.

## PyPI Versus Source Checkout

| Path | Best for | Hazards | Verification |
| --- | --- | --- | --- |
| PyPI package | Normal usage, reproducible skills, prebuilt package resources. | May still need Java 21 and optional Faiss. | `python scripts/check_pyserini_runtime.py --check-lucene` |
| Editable source checkout | Development, unreleased fixes, local source changes. | The checkout can lack Anserini fatjar resources and eval-tool artifacts until built/copied. | `python scripts/check_pyserini_runtime.py --check-lucene --check-server` |
| Source checkout with external Anserini fatjar | Temporary debugging when package resources are not yet present. | `ANSERINI_CLASSPATH` must point to a directory containing `anserini-*-fatjar.jar`; do not persist machine-specific paths into reusable docs. | `ANSERINI_CLASSPATH=/path/to/jars python scripts/check_pyserini_runtime.py --check-lucene` |

Pyserini's JVM setup looks for `anserini-*-fatjar.jar` under the directory named by `ANSERINI_CLASSPATH`, or under Pyserini package resources when the variable is unset. A source checkout installed with `pip install -e .` may not have that fatjar in package resources. Maintainer-oriented build/copy instructions belong in `../../repo-development/SKILL.md`.

## Minimal Smoke Checks

Use these checks before routing to a sibling workflow:

```bash
python -m pip check
python scripts/check_pyserini_runtime.py
python scripts/check_pyserini_runtime.py --check-lucene
```

Add optional checks only when the target workflow needs them:

```bash
python scripts/check_pyserini_runtime.py --check-faiss
python scripts/check_pyserini_runtime.py --check-server
```

Avoid benchmark-sized checks such as searching prebuilt MS MARCO indexes or downloading encoder models unless the user asks for end-to-end retrieval verification and accepts the downloads.

## Expected Healthy Signals

- `python -m pip check` reports no broken requirements.
- The runtime checker reports Python 3.12 or a compatible `>=3.12` interpreter.
- Java is found and reports major version 21.
- `import pyserini` succeeds and package metadata reports Pyserini 2.3.0 for repo-matched skills.
- `--check-lucene` imports `LuceneSearcher` without `No matching jar file found`, Java class, or PyJNIus startup errors.
- `--check-faiss` imports both `faiss` and `pyserini.search.faiss` when Faiss workflows are in scope.
- `--check-server` imports REST/MCP modules without missing Faiss, Java, or eval-resource errors.
