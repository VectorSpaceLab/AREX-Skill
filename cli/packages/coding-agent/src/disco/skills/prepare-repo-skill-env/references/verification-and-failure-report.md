# Verification and Failure Report

## Purpose

Read this reference after installation commands run. An environment is not
ready for `create-repo-skill` until direct checks prove that the intended
package can be inspected from the target environment set and every required
backend in the caller's verification plan passes its preparation smoke.
Successful environment creation, CPU import, or `pip install` is only an
intermediate result.

## Verification Command Discipline

Run each gate as an explicit terminal command. For Conda or micromamba, use
`run --prefix`; for venv or uv, use the environment Python's absolute path. Do
not activate an environment and then rely on an unqualified `python` or `pip`.

Run import and metadata checks from outside the repository checkout when
practical. Use Python's `-I` isolated mode when compatible so the current
directory, `PYTHONPATH`, or user site cannot make an incorrect install appear
healthy.

Use finite terminal-tool timeouts for CLI and smoke checks. Capture the exact
command, exit status, and concise relevant output in the private report. Do not
combine unrelated gates into one shell chain.

## Mandatory Gates

A successful handoff requires all applicable gates:

1. The prefix exists and is not Conda `base`.
2. The target environment Python runs and reports the expected executable and
   version.
3. `python -m pip check` passes, or an equivalent manager check is documented
   when the environment intentionally has no pip.
4. Expected distribution metadata exists.
5. Expected import modules import successfully from the target environment.
6. Required console entry points or CLIs pass safe help/version checks.
7. Requested backend checks pass for CUDA, ROCm, MPS, TPU, or another vendor
   backend.
8. Repo-specific smoke checks pass when import alone is too weak.
9. Every required native candidate is mapped to a prepared compatible prefix
   and a final native command to run after skill integration. Optional skips and
   evidence-backed alternatives are distinguished from required blocks.

Metadata and import checks are both required. Metadata without import success
can mean a broken install. Import success without metadata can mean the checkout
or another Python path supplied the wrong module.

## Direct Verification Examples

Substitute concrete values before execution. Conda examples:

```bash
conda run --prefix "/absolute/path/to/prefix" python -c "import sys; print(sys.executable); print(sys.version)"
conda run --prefix "/absolute/path/to/prefix" python -m pip check
conda run --prefix "/absolute/path/to/prefix" python -I -c "from importlib.metadata import version; print(version('distribution-name'))"
conda run --prefix "/absolute/path/to/prefix" python -I -c "import package_name; print(package_name.__file__)"
conda run --prefix "/absolute/path/to/prefix" package-cli --help
```

Venv/uv examples on Unix-like systems:

```bash
"/absolute/path/to/prefix/bin/python" -c "import sys; print(sys.executable); print(sys.version)"
"/absolute/path/to/prefix/bin/python" -m pip check
"/absolute/path/to/prefix/bin/python" -I -c "from importlib.metadata import version; print(version('distribution-name'))"
"/absolute/path/to/prefix/bin/python" -I -c "import package_name; print(package_name.__file__)"
"/absolute/path/to/prefix/bin/package-cli" --help
```

On Windows use `Scripts/python.exe` and the platform's entry-point path. If
`-I` prevents a repo-supported editable install from resolving, explain why,
run from a neutral working directory without `PYTHONPATH` or user-site leakage,
and retain evidence that the import came from the intended installation.

## Extra Smoke Checks

Use the smallest safe check that exercises the required capability:

- For a CLI, run `<command> --help` or `--version` with a short timeout.
- For an API, construct a minimal object or inspect a signature without
  downloading models or starting a service.
- For torch CUDA, allocate a tiny tensor and query device capability.
- For a service extra, import its module and inspect CLI help; do not start a
  long-running listener just to prove installation.

Execute Python smoke code directly, for example:

```bash
"/absolute/path/to/prefix/bin/python" -I -c "import package_name; print(package_name.__version__)"
"/absolute/path/to/prefix/bin/python" -I -c "from package_name import important_api; print(important_api)"
```

Do not silently run checks that need credentials, external services, large
downloads, training, destructive writes, or untrusted repo code. Record what
was skipped, why, and what would be needed to verify it.

Do not run the repo-native GPU test/example during this preparation phase. Run
the smallest backend smoke that proves its environment is viable and preserve
the native candidate for final `verify-repo-skill` execution. A synthetic check
may validate generated guidance, but it cannot replace required GPU/accelerator
runtime evidence.

## Writing `repo_env_report.json`

Write the report from the observed command results after the gates finish. The
report is private setup evidence, not generated skill content. Use this minimum
shape:

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
    "prefix": "/absolute/path/to/prefix",
    "pythonExecutable": "/absolute/path/to/prefix/bin/python",
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
        "preparationSmoke": "passed",
        "finalNativeCandidates": ["examples/infer.py"]
      }
    ],
    "optional": [],
    "alternative": []
  },
  "installPlan": {
    "python": "3.11",
    "includedScope": ["src/package"],
    "excludedScope": ["training"],
    "installedGroups": ["base", "inference"],
    "skippedGroups": ["dev", "train"]
  },
  "commands": [
    {
      "phase": "import verification",
      "command": "<redacted only if it contained a secret>",
      "exitCode": 0,
      "outcome": "package import succeeded from target environment"
    }
  ],
  "verification": {
    "pipCheck": "passed",
    "distributions": ["distribution-name"],
    "imports": ["package_name"],
    "backendSmokes": [{"backend": "cuda", "status": "passed"}]
  },
  "warnings": [],
  "failures": []
}
```

Use `status: "failed"` if any required gate remains unresolved without explicit
partial-drafting acceptance. Never invent output, turn a skipped gate into a
pass, or store credentials, tokens, or secret environment-variable values. Use
`status: "partial"` only after explicit user acceptance, and set
`fullBackendVerification` and
`backendGateEligibleForAutoImport` to `false`. A command may be redacted only
enough to remove a secret; preserve the executable, operation, and non-secret
arguments needed to diagnose it.

## Handoff Template

Use this shape for every `ok`, `partial`, or `failed` handoff:

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
Required backend verdict(s): <backend: passed/blocked>
Final native backend case(s): <candidate ids deferred until integration>
Accepted partial limitation: <exact limitation or none>
Additional notes: <extras installed, skipped unsafe checks, limitations>
```

## Failure Template

Use this shape when the environment is not ready:

```text
Environment status: <partial|failed>
Ready for skill drafting: <yes only after explicit partial acceptance|no>
Ready for full backend verification: no
Backend gate eligible for auto-import: no
Failed phase: <manager discovery | environment create | dependency install | repo install | pip check | metadata | import | backend | smoke test>
Repository path: <repo_path>
Environment manager: <conda|micromamba|venv|uv|unavailable>
Environment prefix: <environment_prefix>
Requested backend: <cpu/cuda/rocm/mps/auto/...>
Blocking native candidate(s): <candidate ids and criticality>
CPU substitute: <full/partial/none with evidence>

Facts:
- OS/arch: <...>
- Python target: <...>
- Available managers/runtimes: <...>
- Hardware: <GPU/backend facts or CPU-only>
- Driver/toolkit: <driver CUDA, nvcc, ROCm, vendor toolkit, or not present>

Blocker:
<specific reason the environment cannot be considered usable>

Evidence:
- Command: <failed command>
- Exit status: <...>
- Key error: <short stderr excerpt>
- Report: <repo_env_report.json>

Next viable actions:
1. <change Python/package/backend/wheel/toolkit/driver/hardware>
2. <fallback manager or private-prefix route>
3. <authorization or external input still required>
```

## Quality Bar

- "Ready" means commands prove the package is usable from the target Python.
- `ok` means every required backend preparation gate is satisfied; it never
  means merely CPU-importable.
- `partial` means drafting was explicitly accepted with a known required
  backend block. It is not full verification and cannot authorize auto-import.
- "Installed" is not the same as "ready".
- "CUDA available" is not the same as "the repo's CUDA path works".
- Hardware impossibility requires exact platform/version evidence.
- Every warning that weakens later package inspection appears in the handoff.
- The report must match the command transcript; it is not a replacement for
  executing and observing the checks.
