# Install and Smoke

## Verified baseline

- PhySO 1.2.0.
- Package metadata requires Python >=3.8; the verified construction baseline used Python 3.12.
- CPU scientific Python stack used during construction: PyTorch CPU build, NumPy, SymPy, pandas, Matplotlib, and scikit-learn.
- Import-time LaTeX warnings are expected if system LaTeX or optional graph-rendering extras are absent.

## Quick check

```bash
python scripts/physo_skill_doctor.py
```

Use `--json` for machine-readable output if helpful.

## Route-specific smoke helpers

```bash
python sub-skills/sr/scripts/smoke_sr_quick_start.py
python sub-skills/class-sr/scripts/smoke_class_sr_quick_start.py
python sub-skills/toolkit/scripts/smoke_toolkit.py
python sub-skills/benchmarks/scripts/smoke_benchmark_loaders.py
```

These smoke helpers are intentionally small and CPU-safe. They do not launch benchmark campaigns or long training runs.

## If the quick check fails

- Verify `physo` and the core scientific stack are importable in the same environment.
- Run `python -m pip check` to catch broken dependencies.
- Then route to the matching sub-skill to debug workflow-specific inputs and outputs.
