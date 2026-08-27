---
name: install-and-runtime
description: "Install Pyserini, select Python/Java/Torch/Faiss/runtime options,
  and diagnose import, JVM, and optional dependency failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pyserini Install And Runtime

## When To Use

Use this sub-skill when the task is about installing Pyserini, preparing a safe runtime environment, or diagnosing failures before an indexing, search, dense retrieval, evaluation, REST, or MCP workflow can start.

Natural triggers include `install Pyserini`, Python version errors, Java/JVM errors, `pyjnius` failures, `No matching jar file found`, missing `faiss`, Torch/CUDA mismatch, source checkout setup, `pip check` conflicts, or REST/MCP imports failing before a server starts.

## Quick Decisions

- Prefer Python 3.12 and Java 21. Pyserini 2.3.0 requires Python `>=3.12`, but the project is built and documented around Python 3.12 with Java 21.
- Use the PyPI package for normal usage; use an editable source checkout only when the user needs unreleased changes or development.
- Install Torch deliberately: CPU wheels are sufficient for CPU-only sparse search, Lucene dense checks, and many setup tasks; CUDA wheels are only needed when the user will run GPU encoders or GPU Faiss.
- Install Faiss separately only when needed. Pyserini metadata does not include Faiss because users must choose `faiss-cpu`, a conda Faiss package, or a GPU build that matches their platform.
- Do not run large prebuilt-index, model-download, or benchmark commands as installation checks unless the user explicitly asks for functional retrieval verification.

## Safe Install Recipes

### Minimal PyPI Environment

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pyserini==2.3.0
python -m pip check
```

If the user wants a current PyPI release instead of the repo-matched version, omit the version pin after confirming reproducibility is not required.

### Conda-Friendly Binary Stack

```bash
conda create -n pyserini python=3.12 -y
conda activate pyserini
conda install -c conda-forge openjdk=21 -y
python -m pip install --upgrade pip
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install pyserini==2.3.0
```

For CUDA, replace the CPU Torch command with the PyTorch command matching the machine's CUDA runtime. Do not install CUDA wheels just because Pyserini imports; install them only for GPU encoding/search tasks.

### Faiss When Needed

```bash
python -m pip install faiss-cpu
python -m pip check
```

If `faiss-cpu` wheels are unavailable or the user needs GPU Faiss, prefer a conda/mamba environment with a platform-compatible Faiss package. After installing Faiss, run the bundled checker with `--check-faiss`.

### Optional Multimodal Extra

```bash
python -m pip install 'pyserini[optional]'
```

Use the optional extra only when the user asks for the optional multimodal/UniIR paths. Core Lucene search, most dense setup, evaluation, REST, and MCP setup do not require the extra.

### Editable Source Checkout

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip check
```

A source checkout can import the Python package while still failing Lucene-backed imports if package resources are missing. Source-development setup may also require the evaluation tools submodule and an Anserini fatjar; see `../repo-development/SKILL.md` for maintainer build/test workflows.

## Verify Before Workflow Handoff

Run the bundled checker from this sub-skill directory or copy it into the target environment:

```bash
python scripts/check_pyserini_runtime.py --help
python scripts/check_pyserini_runtime.py
python scripts/check_pyserini_runtime.py --check-lucene
python scripts/check_pyserini_runtime.py --check-faiss --check-server
```

Interpretation:

- Default checks confirm Python version, Java version, package metadata, importability, PyJNIus configuration, and core neural dependencies without starting retrieval jobs.
- `--check-lucene` starts the Java-backed Lucene import path and catches missing Java, PyJNIus, and Anserini fatjar problems.
- `--check-faiss` verifies the optional Faiss Python package and Pyserini Faiss search import path.
- `--check-server` verifies REST/MCP import dependencies without binding ports or opening indexes.

Use `references/runtime-requirements.md` for dependency choices and source checkout caveats. Use `references/troubleshooting.md` for symptom-to-recovery guidance.

## Route After Runtime Is Healthy

- Lucene indexing, sparse search, fetching, analyzers, query builders, and index readers: `../index-search-fetch/SKILL.md`.
- Dense encoders, Faiss search, GPU/device choices inside retrieval commands, OpenAI/Hugging Face model behavior, and hybrid search: `../dense-encoding/SKILL.md`.
- Run evaluation, qrels, TREC/MS MARCO/KILT formats, fusion, and reproduction matrices: `../evaluation-and-fusion/SKILL.md`.
- REST API, MCP server, API keys, cache/load shedding, and server config aliases: `../serving-and-agent-tools/SKILL.md`.
- Source checkout maintenance, submodules, Anserini/eval tool builds, and test selection: `../repo-development/SKILL.md`.
