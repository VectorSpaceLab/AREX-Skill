# Legacy Runtime Reference

## Purpose

Read this before running or porting native DARTS scripts. The original repository is a legacy script-style PyTorch research codebase; most operational failures are runtime-version, CUDA, or dataset/checkpoint issues rather than algorithm misunderstandings.

## Runtime facts

- The README states: `Python >= 3.5.5`, `PyTorch == 0.3.1`, `torchvision == 0.2.0`.
- The README explicitly warns that PyTorch 0.4 is not supported and may lead to OOM.
- The repository has no `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`, or console entry points. Treat it as a collection of scripts, not an installable package.
- The CNN runner scripts use legacy syntax and APIs such as `.cuda(async=True)`, `Variable(..., volatile=True)`, and `loss.data[0]`. Modern Python versions reserve `async` and modern PyTorch removed or changed these APIs.
- The native CNN runners exit immediately when `torch.cuda.is_available()` is false. RNN scripts expose a `--cuda` flag with inverted argparse semantics (`action='store_false'`) and still contain CUDA-heavy/default paths.

## What a compatible native environment needs

A faithful original run usually needs:

1. A Python version old enough to parse `async=True` keyword usage, such as the Python 3.5-era environment targeted by the README.
2. PyTorch 0.3.1 and torchvision 0.2.0 with a CUDA build compatible with the host GPU/driver.
3. NVIDIA CUDA hardware for the documented workflows.
4. Dataset files or folders in the expected layout; see [data and checkpoints](data-and-checkpoints.md).
5. Optional Graphviz Python package and system Graphviz binary only if using the original visualization scripts. The bundled genotype helper emits DOT without Graphviz.

## Modernization guidance

When a user asks to run this code on modern Python or PyTorch, frame it as a porting task:

- Replace `.cuda(async=True)` with modern non-blocking transfer syntax where appropriate, usually `.cuda(non_blocking=True)` or `.to(device, non_blocking=True)`.
- Replace `Variable(..., volatile=True)` with `with torch.no_grad():` and tensor usage.
- Replace `loss.data[0]` / scalar tensor indexing with `loss.item()` where the value is scalar.
- Audit `F.tanh` / `F.sigmoid` aliases, optimizer/scheduler order, and serialization formats.
- Revalidate memory behavior. The README warning about PyTorch 0.4 OOM means a naive version bump may not reproduce paper settings.
- Keep original results separate from ported results. A modernized port is useful engineering work, but it is not automatically paper-equivalent.

## Safe checks before native execution

Use the root helper [scripts/darts_static_inspector.py](../scripts/darts_static_inspector.py) on a DARTS source tree to detect missing files, package metadata absence, modern-Python syntax failures, and dataset placeholders without importing or running the repo.

Use [scripts/darts_command_builder.py](../scripts/darts_command_builder.py) to construct commands and prerequisites without launching long jobs. Smoke-mode commands are wiring checks only; never report their output as paper accuracy or perplexity.
