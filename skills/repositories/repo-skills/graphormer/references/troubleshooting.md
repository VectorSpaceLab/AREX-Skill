# Troubleshooting

This file collects Graphormer issues that cut across multiple sub-skills.
Workflow-specific fixes also appear in the nearest sub-skill reference.

## 1. Fairseq user-dir import fails

Symptoms:
- `ImportError` when importing `graphormer`
- missing `graphormer` tasks, models, or criterions in fairseq registries
- `--arch graphormer_base` or `--task graph_prediction` is rejected

Likely causes:
- `--user-dir` was omitted or points at the wrong directory
- the process imported a different module with the same basename first
- fairseq was installed without a compatible user-dir/plugin stack

Recovery:
- pass the directory that contains Graphormer's `models/`, `tasks/`, and
  `criterions/` packages as the user-dir
- retry in a fresh Python process if module caching caused a collision
- use the bundled environment checker to see whether the registry import or the
  user-dir path failed first

## 2. Old fairseq / packaging incompatibilities

Symptoms:
- editable installation fails while resolving fairseq dependencies
- metadata errors mention old `omegaconf` or `protobuf`
- `pip check` shows version conflicts after a seemingly successful install

Likely causes:
- the historical Graphormer stack uses older package constraints
- newer pip versions reject some older metadata or dependency markers

Recovery:
- keep the Graphormer inspection environment isolated
- if dependency resolution complains about old `omegaconf` metadata, pin pip
  below the version that enforces the stricter metadata rules
- if `fairseq` build extensions are not needed for your task, use an
  import-only editable installation path and document the limitation

## 3. Cython or compiled graph preprocessing fails

Symptoms:
- errors mention `graphormer.data.algos`, `Cython`, `pyximport`, or NumPy
  headers
- task import fails before registry inspection reaches Graphormer code

Likely causes:
- the graph preprocessing extension has not been built with a compatible Cython
  and NumPy version
- the environment is missing the build tools needed by the historical stack

Recovery:
- install the older Cython / NumPy-compatible toolchain used by the validated
  stack
- rerun the checker from a clean process
- if you only need registry or command rendering, keep the helper script
  import-only and do not run native training

## 4. CUDA runtime cannot be seen

Symptoms:
- `torch.cuda.is_available()` is false on a GPU host
- evaluation or DiG workflows fail before the first batch
- import succeeds, but a CUDA-only helper cannot allocate a tensor

Likely causes:
- the PyTorch wheel is CPU-only or mismatched with the host CUDA runtime
- the environment libraries are not visible to the Python process
- the selected workflow requires a GPU but the current host path is CPU-only

Recovery:
- use a CUDA-capable PyTorch build that matches the historical Graphormer stack
- ensure the environment's CUDA runtime libraries are discoverable before
  launching the checker or a training/evaluation run
- do not treat a CPU import as proof that CUDA-only workflows are usable

## 5. Dataset or checkpoint downloads fail

Symptoms:
- OGB, pretrained checkpoints, or DiG data downloads never complete
- a command hangs while trying to fetch a remote artifact
- a workflow fails because the expected dataset directory is empty

Likely causes:
- network access is unavailable or rate-limited
- the repository's external dataset/checkpoint host is unreachable
- the requested workflow depends on a data artifact that was never downloaded

Recovery:
- treat network-backed assets as external prerequisites, not bundled runtime
  dependencies
- confirm the dataset or checkpoint layout before running the workflow
- for optional research flows, use the command renderer and inspect the notes
  before attempting a real run

## 6. Duplicate module names

Symptoms:
- fairseq reports that the module name is not globally unique
- registry checks see the wrong Graphormer checkout

Likely causes:
- another checkout or package with the same top-level module name was imported
  earlier in the process

Recovery:
- use a fresh Python process for each registry check
- only point one process at one Graphormer user-dir
- if you are comparing multiple checkouts, isolate them in separate processes

## 7. Long-running jobs are not good smoke tests

Symptoms:
- a training or DiG command starts successfully but never finishes during a
  quick review pass

Likely causes:
- the workflow is intentionally data-heavy, GPU-heavy, or distributed

Recovery:
- use the bundled command renderer or environment checker first
- reserve the real run for a later Researcher session with the right data,
  hardware, and budget
