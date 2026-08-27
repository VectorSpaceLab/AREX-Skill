---
name: installation
description: "Install, inspect, and troubleshoot Fairlearn runtimes, optional
  plotting/adversarial dependencies, and version diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fairlearn installation

Use this sub-skill when the task is about installing Fairlearn, confirming imports, inspecting versions, optional dependencies, plotting extras, PyTorch/TensorFlow adversarial backends, `show_versions`, missing dependency errors, or package-runtime diagnostics.

## Quick workflow

1. Determine whether the user is using a released package, a local checkout, or a prepared environment.
2. Install the smallest dependency set needed for the requested workflow.
3. Run the root check script or the wrapper in this sub-skill.
4. If optional plotting or adversarial backends are absent, decide whether the requested workflow actually requires them before installing.
5. Route back to the workflow-owning sub-skill after imports and optional dependencies are resolved.

## Read these references

- [`../../references/installation.md`](../../references/installation.md) for root install commands, optional dependency table, raw import checks, and `show_versions` guidance.
- [`references/runtime-and-version-checks.md`](references/runtime-and-version-checks.md) for workflow-specific runtime probes and version diagnostics.
- [`references/troubleshooting.md`](references/troubleshooting.md) for install/import, extras, `show_versions`, backend, and version-skew recovery.
- [`scripts/check_runtime.py`](scripts/check_runtime.py) wraps the root installation check from this sub-skill location.

## Core facts

- Package name: `fairlearn`.
- Python requirement in the inspected source: `>=3.11`.
- Core dependencies: `narwhals`, `numpy`, `pandas`, `scikit-learn`, and `scipy`.
- Public version check: `import fairlearn; print(fairlearn.__version__)`.
- Environment report: `fairlearn.show_versions()`.
- No Fairlearn-specific CLI entry points were found in the inspected source.

## Optional dependency ownership

| Dependency | Owned workflow | First route |
| --- | --- | --- |
| `matplotlib` | assessment and postprocessing plots | `../assessment/` or `../postprocessing/` |
| `torch` | PyTorch adversarial backend | `../adversarial/` |
| `tensorflow` / `keras` | TensorFlow adversarial backend | `../adversarial/` with explicit unverified-backend note |
| OpenML/network/cache | dataset loaders | `../datasets/` |

## Fast validation

From this skill directory:

```bash
python sub-skills/installation/scripts/check_runtime.py --include-optional
```

Or from the root skill directory:

```bash
python scripts/check_install.py --include-optional
```

If the check passes but a workflow still fails, switch to that workflow's troubleshooting reference.
