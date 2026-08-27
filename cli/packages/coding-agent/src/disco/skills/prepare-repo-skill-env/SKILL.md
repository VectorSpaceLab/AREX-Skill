---
name: prepare-repo-skill-env
description: "Create, install, and prove the minimum backend-aware Python inspection environment set for a local repository before create-repo-skill. Use when a repo package must be installed into new or existing Conda, micromamba, uv, or venv environments; when selected native tests/examples require CPU, CUDA, ROCm, MPS, or vendor accelerator dependencies; when a broken inspection environment needs diagnosis; or when hardware/backend compatibility must be verified. Consume the confirmed extraction scope and backend verification plan, then run explicit terminal commands instead of delegating environment decisions to a bundled setup script."
metadata:
  disco-role: meta
---

# Prepare Repo Skill Env

## Purpose

Use this skill before `create-repo-skill` when a local repository needs a
verified Python environment for live API and runtime inspection. The caller
should provide or let this skill infer:

- The repository path.
- A new private environment prefix, or an existing environment that may be
  inspected.
- The confirmed extraction scope, backend-classified native candidate map, and
  backend verification plan from `create-repo-skill`, when applicable.

Create the environment, install only what the confirmed scope requires, and
prove that the package works from the environment's Python. "Minimum" means the
smallest environment set that covers every required backend in the selected
scope, not CPU-only by default. Usually one GPU-capable environment can also
cover CPU checks; create additional prefixes only for conflicting backend
variants or an independently selected CPU fallback claim. Run the relevant
Conda, micromamba, uv, Python, and pip commands directly in the terminal. Keep
each material step visible and separately diagnosable; do not hide environment
creation, dependency selection, installation, or verification behind a bundled
setup/bootstrap script.

Prefer Conda when it is already available because it handles Python versions
and compiled dependencies well. Micromamba is an equivalent prefix-based path
when it is already installed. If neither is available, use an existing
compatible Python with `venv`, or an installed `uv` when it can create the
requested environment. Do not mutate Conda `base`, the Python running DisCo, or
a user-owned environment without authorization.

Do not run the repo-native candidate tests/examples during environment
preparation. Install their required variants and run the smallest backend smoke
checks needed to prove that final native verification is feasible; the native
cases themselves run after the generated skill is integrated.

The default private prefix is
`$DISCO_CODING_AGENT_DIR/envs/<skill-id>-inspection` when that variable is set,
otherwise `~/.disco/agent/envs/<skill-id>-inspection`. Resolve it to a concrete
absolute path before executing commands.

This skill produces private setup evidence. Environment paths, checkout paths,
commands, and logs may be handed to `create-repo-skill`, but must not be copied
into the generated public repo skill.

## Required Outputs

Deliver an `ok`, `partial`, or `failed` environment handoff. In every case,
write a private `repo_env_report.json` in the caller's artifact directory, or
another explicit private path when invoked directly.

For success, record:

- Repository path, environment manager, prefix, and environment Python.
- Confirmed extraction scope and the dependency groups selected or skipped.
- Backend verification plan, required/optional/alternative candidates, CPU
  substitution decisions, hardware compatibility verdicts, and the minimum
  environment set selected.
- Exact environment creation, install, and verification commands with exit
  status and concise output/error evidence.
- Installed distribution names and successfully imported module names.
- Hardware/backend verdict when relevant.
- Any unsafe, credentialed, destructive, or long-running checks that were
  deliberately skipped.

Use `partial` only when a required backend cannot be prepared and the user
explicitly authorizes skill drafting with that exact limitation. A partial
handoff is not ready for full backend verification or auto-import. Without that
authorization, report `failed`.

For failure, record the failed phase, exact command, exit status, key stderr,
relevant platform/backend facts, attempted remedies, and the next viable
action. State explicitly that the environment is not ready for
`create-repo-skill`.

## Reference Map

Read the relevant references before acting:

- [references/install-planning.md](references/install-planning.md): packaging
  discovery, backend verification plan interpretation, environment-manager
  selection, direct command templates, extraction-scope dependency choices,
  and install order.
- [references/hardware-and-backends.md](references/hardware-and-backends.md):
  accelerator probing, backend package choices, and compatibility failures.
- [references/verification-and-failure-report.md](references/verification-and-failure-report.md):
  direct verification commands, the report contract, and handoff templates.

## Workflow

### 1. Resolve Inputs and Mutation Boundaries

Resolve these before installation:

- `repo_path`: canonical local checkout path.
- `environment_prefix`: canonical target prefix/path.
- Confirmed included/excluded directories, selected workflows, and user
  requirements from `create-repo-skill` when available.
- Backend-classified native candidates owned by included workflows. Require
  backend requirement, criticality, CPU substitution, dependency variant,
  hardware prerequisites, preparation smoke, and final native expectation.
- The caller's backend verification plan and proposed minimum environment set.
  If either is missing during a `create-repo-skill` call, derive it from repo
  evidence before installation rather than defaulting silently to CPU.
- Python version supported by repo metadata and required backend wheels.
- Distribution name and import module names.
- Required extras, requirements files, build tools, and backend packages.
- Backend expectation: `auto`, `cpu`, `cuda`, `rocm`, `mps`, or another
  documented backend.
- Whether the prefix is new, private and reusable, or user-owned.
- Whether potentially breaking mutation of an existing environment is already
  authorized.

When called automatically by `create-repo-skill`, use its resolved private
default prefix without asking again. During a direct invocation, ask for a
prefix or propose the private default before writing there. Never infer a path
outside the stated default-prefix policy.

If the prefix exists, inspect it read-only first. Imports, version queries,
`pip check`, metadata queries, and safe CLI help are read-only. Installing,
upgrading, downgrading, uninstalling, or repairing packages is mutation. Ask
before mutating a user-provided environment unless the user already authorized
that operation; otherwise create a new private prefix when allowed.

### 2. Inspect the Repository Before Choosing Commands

Read [references/install-planning.md](references/install-planning.md). Inspect
`pyproject.toml`, `setup.cfg`, `setup.py`, requirements files, lockfiles,
`environment.yml`, CI install steps, source roots, entry points, and documented
install variants.

Build a concise install and backend map before running anything:

```text
Selected Python: 3.11 (repo supports >=3.10; required wheels available)
Included scope: src/package, docs/gpu-inference.md, examples/infer.py
Excluded scope: training/, benchmarks/
Required candidate: examples/infer.py | cuda | required | CPU substitute: none
Optional candidate: benchmarks/throughput.py | cuda | optional | excluded
Host verdict: compatible NVIDIA GPU/driver/wheel
Environment set: one CUDA-capable prefix covering CUDA and CPU checks
Install: base package + [inference,cuda] + compatible torch CUDA wheel
Skip: [train], [all], requirements-dev.txt, benchmark dependencies
Preparation smoke: torch CUDA allocation + package backend import
Final native case: examples/infer.py with tiny fixture (run after integration)
```

Do not assume the repository name is the distribution or import name. Do not
install all extras or every requirements file as a substitute for analysis.

### 3. Probe Available Managers and Hardware

Run discovery commands separately so their outcomes remain visible:

```bash
command -v conda
command -v micromamba
command -v uv
command -v python3.11
command -v python3
command -v python
```

Use platform-equivalent commands on Windows. Query versions for tools that
exist. Do not treat a missing command as a fatal error until all suitable paths
have been evaluated.

Read [references/hardware-and-backends.md](references/hardware-and-backends.md)
and probe only the hardware relevant to the requested or repo-required backend.
A visible GPU does not by itself require a GPU install for package inspection.

Apply the backend plan after probing:

- When an included capability has a `required` backend and `CPU substitute:
  none`, prepare and verify that backend whenever compatible hardware and
  packages are available. A CPU-only prefix is not ready for that scope.
- When `CPU substitute` is `full` and the selected CPU candidate verifies the
  same behavior, use the CPU path and record the evidence.
- When the backend is `optional`, omit it from the minimum environment when it
  is unavailable or outside the selected scope, but preserve an explicit
  unverified-capability note.
- When required hardware or a compatible dependency variant is unavailable,
  do not install an arbitrary GPU wheel or call the CPU environment `ok`.
  Report `failed`, ask to narrow scope, or produce `partial` only after the user
  accepts drafting with the required-backend limitation.
- When required backend variants conflict, create separate concrete prefixes
  and verify each one. Do not mutate one prefix repeatedly between incompatible
  CPU/CUDA/ROCm/vendor states.

If no suitable Conda/micromamba, uv, or Python runtime exists, do not invoke a
bundled downloader. Explain the host change required and ask before installing
a runtime or environment manager unless the user already authorized that exact
kind of host-level installation. Once authorized, use the platform's normal
package manager or the selected tool's documented installer with explicit,
reviewable terminal commands, then resume this workflow. Do not silently curl
and execute an installer.

### 4. Create the Required Environment Set with Direct Commands

Substitute concrete absolute paths and the selected Python version in every
command. Do not execute examples with placeholder paths.

Create the primary prefix for the strongest required selected backend. A
GPU-capable prefix normally also runs CPU checks. When the backend plan requires
incompatible variants, derive distinct suffixes such as `-cuda`, `-rocm`, or
`-cpu` from the caller's private prefix and record every prefix in the report.

For Conda:

```bash
conda create --yes --prefix "/absolute/path/to/inspection-env" "python=3.11" pip
conda run --prefix "/absolute/path/to/inspection-env" python -c "import sys; print(sys.executable); print(sys.version)"
```

For an already installed micromamba:

```bash
micromamba create --yes --prefix "/absolute/path/to/inspection-env" "python=3.11" pip
micromamba run --prefix "/absolute/path/to/inspection-env" python -c "import sys; print(sys.executable); print(sys.version)"
```

For venv on Unix-like systems:

```bash
python3.11 -m venv "/absolute/path/to/inspection-env"
"/absolute/path/to/inspection-env/bin/python" -c "import sys; print(sys.executable); print(sys.version)"
```

On Windows, use the environment's `Scripts/python.exe`. If installed `uv` is
the best available path, make its runtime acquisition explicit:

```bash
uv venv --seed --python 3.11 "/absolute/path/to/inspection-env"
"/absolute/path/to/inspection-env/bin/python" -c "import sys; print(sys.executable); print(sys.version)"
```

If `uv` would download a Python runtime, treat that as runtime installation and
apply the authorization rule from step 3.

Do not rely on shell activation. For subsequent Conda/micromamba commands use
`run --prefix`; for venv/uv use the environment Python's absolute path. This
prevents commands from accidentally using DisCo's or the user's current
Python.

### 5. Install the Minimum Required Package Set

Execute one meaningful install phase at a time, with a finite terminal-tool
timeout and observable output. A typical new Conda environment uses commands
like:

```bash
conda run --prefix "/absolute/path/to/inspection-env" python -m pip install -e "/absolute/path/to/repo"
```

For venv/uv:

```bash
"/absolute/path/to/inspection-env/bin/python" -m pip install -e "/absolute/path/to/repo"
```

Add only evidence-backed requirements or extras:

```bash
conda run --prefix "/absolute/path/to/inspection-env" python -m pip install -r "/absolute/path/to/repo/requirements-inference.txt"
conda run --prefix "/absolute/path/to/inspection-env" python -m pip install -e "/absolute/path/to/repo[inference]"
```

Follow repo documentation when backend foundations such as torch, JAX,
TensorFlow, or a compiler/toolkit must be installed first. Do not reflexively
upgrade pip/setuptools/wheel or broad dependency sets, especially in an
existing environment; do so only when repo/build evidence requires it.

For every required backend candidate, install its evidence-backed dependency
variant into the prefix assigned by the backend plan. Do not install a CPU-only
torch/JAX/TensorFlow build into a required CUDA/ROCm environment and then count
package importability as backend coverage. Conversely, do not install GPU
stacks for optional or excluded candidates merely because hardware is visible.

Do not combine creation, multiple installs, and verification into one large
shell command. After each phase, record the exact command, exit status, elapsed
time, and relevant output in the private report. On failure, diagnose the
specific phase and adjust the next visible command rather than rerunning an
opaque all-in-one installer.

If metadata resolution or downloads stall, interrupt the command, distinguish
network delay from compilation, and use the network guidance in
[references/install-planning.md](references/install-planning.md). Proxy or VPN
details supplied by the user are local execution context only; never bake them
into the skill or generated package content.

### 6. Verify from the Environment Python

Read [references/verification-and-failure-report.md](references/verification-and-failure-report.md).
At minimum, run direct commands for:

- Environment Python identity and version.
- `python -m pip check`.
- Distribution metadata from the environment.
- Imports using the environment Python, preferably from outside the checkout
  and with `-I` when compatible, so the current directory or user site cannot
  make a broken install look healthy.
- Relevant CLI/API smoke checks.
- A preparation smoke check for every required backend in the backend plan,
  using the prefix assigned to that backend. For CUDA/ROCm/MPS or a vendor
  accelerator, prove framework/backend availability and a minimal device
  operation when safe.

Examples for Conda:

```bash
conda run --prefix "/absolute/path/to/inspection-env" python -m pip check
conda run --prefix "/absolute/path/to/inspection-env" python -I -c "from importlib.metadata import version; print(version('distribution-name'))"
conda run --prefix "/absolute/path/to/inspection-env" python -I -c "import package_name; print(package_name.__file__)"
```

Equivalent venv commands must use the environment Python's absolute path. A
successful environment creation or `pip install` is not verification. Fix and
rerun every applicable failed gate before an `ok` handoff. Do not run the
repo-native cases yet; record which final cases this prepared environment must
support after skill integration.

### 7. Write the Report and Handoff

Write `repo_env_report.json` from the actual command results. Do not invent
missing output or mark skipped gates as passed. Include at least:

```json
{
  "schemaVersion": 2,
  "status": "ok",
  "readiness": {
    "skillDrafting": true,
    "fullBackendVerification": true,
    "backendGateEligibleForAutoImport": true
  },
  "repositoryPath": "/absolute/path/to/repo",
  "environment": {
    "manager": "conda",
    "prefix": "/absolute/path/to/inspection-env",
    "pythonExecutable": "/absolute/path/to/inspection-env/bin/python",
    "backends": ["cpu", "cuda"]
  },
  "additionalEnvironments": [],
  "backendPlan": {
    "required": [
      {
        "backend": "cuda",
        "capability": "GPU inference",
        "cpuSubstitute": "none",
        "hostVerdict": "compatible",
        "dependencyVariant": "repo cuda extra plus compatible framework wheel",
        "preparationSmoke": "passed",
        "finalNativeCandidates": ["examples/infer.py"]
      }
    ],
    "optional": [],
    "alternative": []
  },
  "installPlan": {
    "python": "3.11",
    "includedScope": [],
    "excludedScope": [],
    "installedGroups": [],
    "skippedGroups": []
  },
  "commands": [],
  "verification": {},
  "warnings": [],
  "failures": []
}
```

Use `status: "ok"` only when every required preparation/backend gate passes.
Use `status: "partial"` only after explicit user acceptance, with
`skillDrafting: true`, `fullBackendVerification: false`, and
`backendGateEligibleForAutoImport: false`. Use `status: "failed"` when a
required gate remains unresolved without that acceptance. The `commands`
entries should identify phase, command, exit status, and concise stdout/stderr
evidence; do not put credentials or secret-bearing environment variables in
the report.

For every handoff, provide:

```text
Environment status: <ok|partial|failed>
Ready for skill drafting: <yes|no>
Ready for full backend verification: <yes|no>
Backend gate eligible for auto-import: <yes|no>
Repository path: <repo_path>
Environment manager: <conda|micromamba|venv|uv>
Environment prefix: <environment_prefix>
Additional environment(s): <prefix/backend or none>
Temporary inspection Python: <python_executable>
Installed package name(s): <distribution names>
Verified import(s): <modules>
Verification report: <repo_env_report.json>
Required backend verdict(s): <backend: preparation smoke passed/blocked>
Final native backend case(s): <candidate ids to run after skill integration>
Accepted partial limitation: <exact user-accepted block or none>
Additional notes: <extras installed, skipped unsafe checks, limitations>
```

`create-repo-skill` may continue normally from `ok`. It may continue drafting
from `partial` only after preserving the accepted backend block and disabling
auto-import. It must not continue from `failed` without repair or an explicitly
narrowed extraction scope.

## Non-Negotiables

- Execute environment creation, package installation, and verification as
  explicit terminal commands; do not route them through a bundled wrapper.
- Never install into or mutate Conda `base`.
- Never use DisCo's current Python as the target environment unless the user
  explicitly requests and authorizes that mutation.
- Never delete or recreate an existing prefix without explicit authorization.
- Never mutate a user-provided environment in a potentially breaking way
  without authorization; use a new private prefix when permitted.
- Never install broad extras, dev requirements, or backend packages unrelated
  to the confirmed extraction scope.
- Never call a CPU-only environment `ok` for a required CUDA/ROCm/MPS/vendor
  capability whose CPU substitute is `partial` or `none`.
- Never silently downgrade a required backend candidate to optional because
  hardware, wheels, drivers, or toolkits are unavailable.
- Never mark a partial environment eligible for auto-import. Preserve the
  required-backend block for final native verification and informed user
  acceptance.
- Never rely only on shell activation or an unqualified `python`/`pip` after
  environment creation.
- Never treat successful creation or installation as proof of usability.
- Never hide a failed or skipped verification gate in an `ok` report.
- Never wait indefinitely on a stalled resolver, download, or build. Use finite
  timeouts, retain useful failure evidence, and diagnose before retrying.
- Never copy private environment paths, proxy details, command logs, or setup
  reports into the generated public repo skill.
