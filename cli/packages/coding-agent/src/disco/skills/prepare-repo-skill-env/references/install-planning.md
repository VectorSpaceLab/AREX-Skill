# Install Planning

## Purpose

Read this reference before creating an environment or installing the repo
package. The install plan must follow the repository's package metadata, Python
support, backend constraints, and the confirmed extraction scope from
`create-repo-skill`. Environment preparation is an adaptive agent task: inspect
the evidence, choose concrete commands, execute them one phase at a time, and
adjust from visible results.

Do not replace that reasoning with a bundled installer. In particular, keep
environment creation, backend foundations, requirements/extras, repo install,
and verification as separate terminal commands. This makes timeouts, resolver
failures, wheel mismatches, and partial state observable.

## Repository Evidence

Inspect package metadata first:

- `pyproject.toml`: `project.name`, `requires-python`, dependencies, optional
  dependencies, console scripts, and build backend.
- `setup.cfg`: metadata name, `python_requires`, `install_requires`, and entry
  points.
- `setup.py`: fallback metadata and custom build behavior.
- `requirements*.txt`, lockfiles, `environment.yml`, `tox.ini`, `noxfile.py`,
  and CI install commands.
- README/docs install instructions, especially backend or extras variants such
  as `[cuda]`, `[serve]`, `[train]`, `[dev]`, and `[all]`.

Identify import roots independently of the distribution name:

- `src/<module>/` and top-level packages with `__init__.py`.
- Namespace packages and top-level `<module>.py` files.
- Console entry points and `__main__.py`.

Do not assume the repo, distribution, and import names match. For example,
`scikit-learn` imports as `sklearn`.

## Extraction-Scope Mapping

Map dependencies to the confirmed scope before installing:

- Start with the distribution and import roots corresponding to included
  source directories.
- Add an extra only when an included workflow, included directory, or explicit
  user requirement needs it.
- Add a requirements file only when it is the documented runtime path for an
  included workflow. Skip lint, docs, benchmark, and broad test requirements
  unless those workflows are selected or a focused smoke test requires them.
- Add torch, JAX, TensorFlow, CUDA/ROCm packages, compilers, or toolkits only
  when selected repo areas import or exercise them.
- Skip dependencies used only by excluded experiments, notebooks,
  integrations, services, benchmarks, or training paths.

Record the reasoning before installation:

```text
Included scope: src/package, docs/inference.md, examples/predict.py
Excluded scope: training/, benchmarks/, docs/serving.md
Install: base package + [inference]
Skip: [train], [serve], [all], requirements-dev.txt
Reason: only inference APIs and CLI are selected
```

If a broader option is large, slow, hardware-specific, or likely to destabilize
an existing environment, ask before expanding an ambiguous scope.

## Backend Verification Plan

Consume the backend-classified native candidate map from `create-repo-skill`.
For every candidate owned by an included workflow, preserve:

- Backend requirement and criticality.
- Whether CPU is a full, partial, or nonexistent substitute.
- Required extras, requirements files, framework wheels, toolkit/compiler, and
  package variant.
- Hardware/driver/runtime prerequisites.
- The small preparation smoke check and the native case deferred until final
  verification.

Choose the minimum environment set that satisfies all `required` candidates.
This is not a CPU-first rule:

- If CUDA/ROCm/MPS/vendor execution is required and CPU substitution is
  `partial` or `none`, select the compatible backend packages and environment.
- If one GPU-capable environment also covers CPU checks, use that single
  prefix.
- If required variants conflict, use separate explicit prefixes instead of
  repeatedly replacing packages in one environment.
- If a CPU alternative fully verifies the same selected behavior, record the
  evidence and use that alternative.
- If required hardware or packages are unavailable, return a blocking verdict.
  A CPU import does not make the backend plan complete. Use a `partial` handoff
  only after the user accepts the exact limitation; otherwise fail or narrow
  the extraction scope.
- Optional backend candidates may remain uninstalled when unavailable or
  outside the selected scope, but report them as unverified and do not claim
  backend coverage.

Do not run native repo tests/examples during environment preparation. Install
what their final execution needs and run only a minimal framework/package
backend smoke. Preserve the native candidate ids for `verify-repo-skill`.

## Python Version Selection

Use evidence in this order:

1. Honor `requires-python` and explicit package documentation.
2. Prefer a version exercised by current CI and supported by required wheels.
3. If unconstrained, use Python 3.11 as a stable default.
4. Avoid Python 3.13 unless the repo and compiled dependencies support it.
5. Older ML repos with torch, TensorFlow, tokenizers, deepspeed, flash-attn,
   xformers, or similar compiled packages often need Python 3.10 or 3.11.

If repo metadata and available backend wheels conflict, report the conflict.
Choose another version only when package/backend evidence supports it.

## Manager Selection

Probe installed tools with separate commands:

```bash
command -v conda
command -v micromamba
command -v uv
command -v python3.11
command -v python3
command -v python
```

Choose in this order unless the user or repo requires otherwise:

1. Existing Conda for compiled or Conda-oriented projects.
2. Existing micromamba for the same prefix-based workflow.
3. Compatible host Python plus `venv` for ordinary Python packages.
4. Existing `uv` when it is the most suitable available manager.

Conda and micromamba do not require a host Python to create the target prefix.
If no suitable manager or Python exists, a bundled bootstrap script is not a
fallback. Identify a platform-appropriate runtime/manager installation, explain
its host-level effects, and obtain authorization unless already granted. Use
explicit official package-manager or installer commands, inspect download
sources and checksums where applicable, and never pipe an unreviewed download
directly into a shell.

## Prefix and Existing-Environment Policy

Always use an isolated absolute prefix. For Conda:

```bash
conda create --yes --prefix "/absolute/path/to/prefix" "python=3.11" pip
```

For venv:

```bash
python3.11 -m venv "/absolute/path/to/prefix"
```

Rules:

- Never use or modify Conda `base` for this task. Resolve `conda info --base`
  and compare canonical paths before any install into an existing prefix.
- Never install into the Python running DisCo unless explicitly requested.
- If the prefix exists, inspect its manager metadata, Python/version, installed
  package state, and `pip check` before deciding whether reuse is safe.
- Do not delete/recreate an existing prefix without authorization.
- Imports, version queries, metadata inspection, `pip check`, and safe CLI
  `--help` checks are read-only. Installs, upgrades, downgrades, uninstalls, and
  repairs are mutations.
- Ask before a potentially breaking mutation of a user-provided environment
  unless it was already authorized. If declined, use a new private prefix when
  allowed.
- Do not rely on activation. Use `conda run --prefix`, `micromamba run
  --prefix`, or the venv/uv Python's absolute path.

For venv or uv, the Unix environment Python is
`/absolute/path/to/prefix/bin/python`; on Windows it is
`C:\absolute\path\to\prefix\Scripts\python.exe`.

## Direct Command Templates

Substitute concrete values before running these examples. Do not execute
placeholder paths.

### Conda

```bash
conda create --yes --prefix "/absolute/path/to/prefix" "python=3.11" pip
conda run --prefix "/absolute/path/to/prefix" python -c "import sys; print(sys.executable); print(sys.version)"
conda run --prefix "/absolute/path/to/prefix" python -m pip install -e "/absolute/path/to/repo"
```

### Micromamba

```bash
micromamba create --yes --prefix "/absolute/path/to/prefix" "python=3.11" pip
micromamba run --prefix "/absolute/path/to/prefix" python -c "import sys; print(sys.executable); print(sys.version)"
micromamba run --prefix "/absolute/path/to/prefix" python -m pip install -e "/absolute/path/to/repo"
```

### venv

```bash
python3.11 -m venv "/absolute/path/to/prefix"
"/absolute/path/to/prefix/bin/python" -c "import sys; print(sys.executable); print(sys.version)"
"/absolute/path/to/prefix/bin/python" -m pip install -e "/absolute/path/to/repo"
```

### uv

```bash
uv venv --seed --python 3.11 "/absolute/path/to/prefix"
"/absolute/path/to/prefix/bin/python" -c "import sys; print(sys.executable); print(sys.version)"
"/absolute/path/to/prefix/bin/python" -m pip install -e "/absolute/path/to/repo"
```

An installed `uv` may download a managed Python. Make that possibility explicit
and apply the runtime-installation authorization rule.

## Install Order

Use this order unless repo documentation requires another:

1. Create or inspect the prefix.
2. Install or adjust packaging tools only when build evidence requires it.
3. Install required backend foundations from the backend verification plan,
   such as torch/JAX/TensorFlow and compatible CUDA/ROCm runtime or compiler
   packages, in the prefix assigned to that backend.
4. Install scope-required requirements files or extras.
5. Install the local repository package.
6. Install/build extension packages last when they must compile against an
   already-installed backend.
7. Run every verification gate.

Prefer editable installation for local inspection:

```bash
"/absolute/path/to/prefix/bin/python" -m pip install -e "/absolute/path/to/repo"
```

Use a normal install when editable mode is unsupported or changes behavior:

```bash
"/absolute/path/to/prefix/bin/python" -m pip install "/absolute/path/to/repo"
```

Install only selected extras:

```bash
"/absolute/path/to/prefix/bin/python" -m pip install -e "/absolute/path/to/repo[inference,serve]"
```

Run each material phase separately with a finite terminal timeout. Record the
command and outcome before starting the next phase. Avoid large chained shell
commands whose failure location is ambiguous.

## Requirements and Compiled Packages

Do not blindly install every requirements file:

- `requirements.txt` is often runtime, but verify with docs/metadata.
- `requirements-dev.txt` and `dev-requirements.txt` are usually unnecessary.
- `requirements-cuda.txt` or `requirements-gpu.txt` applies only to the selected
  and supported backend.
- `environment.yml` may be authoritative for older Conda-heavy projects;
  inspect it before translating its dependencies to prefix commands.

For torch CUDA extensions such as flash-attn, xformers, apex, or custom ops:

- Install and verify torch first.
- Match the torch ABI, CUDA tag, driver, Python, architecture, and GPU compute
  capability.
- Use `--no-build-isolation` when the extension must compile against installed
  torch:

  ```bash
  MAX_JOBS=4 "/absolute/path/to/prefix/bin/python" -m pip install flash-attn --no-build-isolation -v
  ```

- Keep `MAX_JOBS` conservative on memory-limited hosts.
- If source compilation is required, verify toolkit/compiler availability
  before launching a long build.

## Slow Installs and Network Routing

Interrupt and diagnose when metadata resolution or downloads make no meaningful
progress, repeatedly retry, or show unreasonable transfer rates. Preserve the
failed command, elapsed time, and useful output.

Distinguish network delay from active compilation. For network problems, use a
user-provided proxy/VPN only as local execution context. Otherwise consider a
temporary trusted mirror or the package's official backend-specific index.
Prefer per-command settings over modifying global pip or Conda configuration:

```bash
PIP_INDEX_URL=https://pypi.org/simple \
PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cu128 \
"/absolute/path/to/prefix/bin/python" -m pip install <package>
```

```bash
conda create --yes --prefix "/absolute/path/to/prefix" -c conda-forge "python=3.11" pip
```

Generic mirrors may not carry CUDA/ROCm/vendor wheels. Revert to official
indexes when a mirror changes resolution or lacks the required artifact. Never
put local proxy commands, credentials, tokens, or private network details into
generated skill content.

## Reproducibility Snapshot

After verification, capture private environment evidence with direct commands:

```bash
"/absolute/path/to/prefix/bin/python" -m pip freeze
"/absolute/path/to/prefix/bin/python" -m pip check
```

For Conda, also capture `conda list --prefix "/absolute/path/to/prefix"`. Store
summaries or artifact paths in `repo_env_report.json`; do not copy machine paths
or the full private environment snapshot into the public generated repo skill.
