# Environment and dependencies

## When to read

Read this before installing the package, selecting CPU versus CUDA, diagnosing
an import error, or deciding whether an optional acceleration path belongs in a
runtime plan.

## Reproducible baseline

Use a fresh Python environment and install the public distribution:

```bash
python -m pip install alphafold3-pytorch
python -c "import torch, alphafold3_pytorch; print(torch.__version__)"
```

The package metadata requires Python `>=3.9` and PyTorch `>=2.1`. Prefer a
Python version and PyTorch wheel that are both supported by the target machine;
do not mix an arbitrary CUDA extension or framework wheel with an existing
installation. For a repository checkout, an editable install is appropriate,
but a future agent using this skill should not depend on that checkout.

## Backend decision

- **CPU:** appropriate for import, data parsing, input conversion, config
  validation, and deliberately reduced model checks. It is not evidence of
  CUDA behavior or production throughput.
- **CUDA:** probe with `scripts/check_environment.py --cuda`. A CUDA-capable
  PyTorch build, compatible driver, visible device, and enough memory are all
  required. Start with a reduced model and small input; the package's default
  model is not a cheap device smoke test.
- **Nim MSA acceleration:** optional. The Python MSA implementation is the
  fallback. Do not install a compiler/toolchain merely to validate the core
  package; only add it for a specifically selected acceleration workflow.
- **PLM/NLM embeddings:** optional model integrations. They can require extra
  model packages, checkpoints, or downloads; keep them out of a no-network
  smoke test.
- **Gradio app:** included in package dependencies, but launching it loads a
  checkpoint, starts a local server, and clears its cache directory. Use the
  `cli-serving` route and a disposable cache only after explicit approval.

## Diagnostic helper

Run this from any current directory:

```bash
python scripts/check_environment.py --help
python scripts/check_environment.py --json
python scripts/check_environment.py --cuda
```

The helper reports distribution versions, import status, CUDA availability and
one optional small allocation. It does not install packages, download weights,
create files, launch services, or alter the environment. Treat missing optional
modules separately from a missing core import.

## Install failure triage

1. Capture Python version, platform, PyTorch version/build tag, and the first
   import traceback.
2. Run `python -m pip check` and the helper in JSON mode.
3. Resolve framework/backend ABI mismatches before installing optional packages.
4. If the failure names RDKit, Gemmi, Biopython, CCD utilities, or another
   declared dependency, repair the isolated environment rather than masking
   the import in application code.
5. If only Nim, PLM/NLM, Kalign, or Gradio functionality is missing, narrow the
   task or install the explicitly selected optional surface.
