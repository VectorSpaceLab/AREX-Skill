# Install And Runtime Troubleshooting

Use this reference to map common Pyserini setup symptoms to safe diagnosis and recovery steps. Keep recovery focused on the environment first; hand off actual indexing/search/eval/server workflows to sibling sub-skills after imports are healthy.

## Fast Triage

Run checks in this order:

```bash
python --version
java -version
python -m pip show pyserini
python -m pip check
python scripts/check_pyserini_runtime.py
```

Then add only the checks relevant to the failing workflow:

```bash
python scripts/check_pyserini_runtime.py --check-lucene
python scripts/check_pyserini_runtime.py --check-faiss
python scripts/check_pyserini_runtime.py --check-server
```

## Symptom Matrix

| Symptom | Likely cause | Confirm with | Recovery |
| --- | --- | --- | --- |
| `ERROR: Package 'pyserini' requires a different Python` or dependency wheels are unavailable. | Interpreter is older than Pyserini metadata, or a newer interpreter lacks matching binary wheels. | `python --version`; `python -m pip debug --verbose`. | Create a fresh Python 3.12 environment and reinstall. Avoid Python 3.13+ unless the user's stack is already verified. |
| `java: command not found` or Java command fails. | No JDK on `PATH`. | `java -version`. | Install JDK 21 through the user's package manager or conda/mamba, then reopen/refresh the shell. |
| Java version is not 21. | Wrong JDK selected by `PATH` or `JAVA_HOME`. | `java -version`; `echo "$JAVA_HOME"`. | Select JDK 21. If setting `JAVA_HOME`, use the user's actual JDK location and do not hard-code it into reusable files. |
| `ModuleNotFoundError: No module named 'jnius'` or `jnius_config`. | PyJNIus missing or installed in a different Python environment. | `python -m pip show pyjnius`; `python -c "import jnius_config"`. | Activate the intended environment and reinstall Pyserini or `pyjnius>=1.7.0` with `python -m pip`. |
| `No matching jar file found in ...` from `pyserini._jvm.configure_classpath`. | Java-backed Pyserini import cannot find an `anserini-*-fatjar.jar`. This is common in editable source checkouts before Anserini resources are built/copied. | `python scripts/check_pyserini_runtime.py --check-lucene`; inspect whether Pyserini package resources contain an `anserini-*-fatjar.jar`; check whether `ANSERINI_CLASSPATH` points to a directory with the fatjar. | For normal use, install the PyPI package. For source development, build/copy the Anserini fatjar into Pyserini package resources or set `ANSERINI_CLASSPATH` for the current process to a directory containing the fatjar. Route maintainer build steps to `../../repo-development/SKILL.md`. |
| `ImportError`, `ClassNotFoundException`, or Java class errors during `from pyserini.search.lucene import LuceneSearcher`. | Fatjar version mismatch, missing fatjar, or JVM started before Pyserini added its classpath. | Run the Lucene check in a fresh Python process; check whether another package started the JVM first. | Start Pyserini/Lucene imports before other PyJNIus users in the process. Use a fresh shell or process after fixing `ANSERINI_CLASSPATH` or package resources. |
| `ModuleNotFoundError: No module named 'faiss'`. | Faiss is optional and not installed by Pyserini metadata. | `python scripts/check_pyserini_runtime.py --check-faiss`. | Install `faiss-cpu` for CPU workflows or a platform-compatible GPU Faiss package when the user explicitly needs GPU Faiss. |
| `AttributeError: module 'faiss' has no attribute 'StandardGpuResources'` or GPU Faiss calls fail. | CPU-only Faiss installed but the workflow requests GPU Faiss. | `python -c "import faiss; print(hasattr(faiss, 'StandardGpuResources'))"`. | Use CPU mode or install a GPU-capable Faiss build that matches the CUDA/runtime stack. |
| `torch.cuda.is_available()` is false but a command uses `--device cuda`. | CPU Torch wheel, missing driver, wrong CUDA wheel, or no GPU. | `python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"`. | Use `--device cpu` or reinstall Torch from the PyTorch selector for the machine's CUDA runtime. |
| `pip check` reports version conflicts involving Torch, Transformers, ONNX Runtime, FastAPI, or OpenAI. | Existing environment contains incompatible pins. | `python -m pip check`; `python -m pip freeze`. | Prefer a fresh Python 3.12 environment. If the user must reuse the environment, change only the packages required by the target workflow and report the risk first. |
| REST or MCP import fails with `faiss` missing. | Server modules import searcher registries that include Faiss searchers. | `python scripts/check_pyserini_runtime.py --check-server`. | Install `faiss-cpu` or a matching GPU Faiss build even if the immediate server alias is sparse-only, then retry server import checks. |
| REST/MCP source checkout import fails with missing eval jar/resource errors. | Editable checkout lacks packaged resource artifacts needed by evaluation/server paths. | `python scripts/check_pyserini_runtime.py --check-server`; run the failure in a fresh process. | For normal server use, prefer the PyPI package. For development, initialize/build required source resources and route details to `../../repo-development/SKILL.md`. |
| Encoder command unexpectedly downloads a model or asks for credentials. | Dense workflow uses a Hugging Face/OpenAI-backed encoder rather than local encoded queries. | Inspect the dense command for `--encoder`, `--encoder-class`, OpenAI model names, or missing `--encoded-queries`. | Route to `../../dense-encoding/SKILL.md`. Use pre-encoded queries or local/cached models when offline. Set credentials only when the user explicitly authorizes external API use. |
| `openai` authentication errors. | OpenAI-backed encoder path selected without credentials. | Look for OpenAI encoder settings; check environment only if the user asks. | Switch to a local encoder/pre-encoded query workflow or ask the user to provide credentials through their normal secret-management path. Do not print or store keys in skill files. |

## Source Checkout Missing Fatjar Case

A common difficult failure is an editable source checkout where `import pyserini` works but Lucene-backed imports fail:

```text
Exception: No matching jar file found in .../pyserini/resources/jars
```

Do not treat this as a Python package install failure. The Python package is present; the Java resources are missing.

Recovery choices:

1. If the user just wants to use Pyserini, install the PyPI package in a clean environment and rerun `python scripts/check_pyserini_runtime.py --check-lucene`.
2. If the user is developing Pyserini, build the matching Anserini fatjar and make it available to Pyserini package resources, or set `ANSERINI_CLASSPATH` for the process to a directory containing `anserini-*-fatjar.jar`.
3. If the same Python process already started a JVM before the classpath was fixed, restart the process before retrying.

Keep machine-specific fatjar paths out of reusable instructions. Use placeholders in user-facing commands and ask the user to substitute their actual build output directory.

## CPU-Only Dense Retrieval Case

When a user wants dense retrieval on a CPU-only machine, do not install CUDA by default.

Recommended setup:

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install pyserini==2.3.0 faiss-cpu
python scripts/check_pyserini_runtime.py --check-faiss
python -c "import torch; print('cuda available:', torch.cuda.is_available())"
```

Then route dense command construction to `../../dense-encoding/SKILL.md` and ensure device flags are CPU-oriented. If the user asks for GPU acceleration later, change Torch/Faiss packages deliberately rather than mixing CPU and GPU wheels in the same environment.

## Safe Reporting

When handing a runtime issue back to the user, include:

- Python major/minor version, not the local interpreter path.
- Java major version and whether `java` is found, not private JDK paths unless the user explicitly needs local shell debugging.
- Pyserini version and whether it is PyPI or editable/source.
- Which optional checks were run: Lucene, Faiss, server.
- The exact symptom and the next recovery command.

Do not include local checkout paths, private environment prefixes, downloaded private jar locations, API keys, or hidden cache paths in reusable runtime skill content.
