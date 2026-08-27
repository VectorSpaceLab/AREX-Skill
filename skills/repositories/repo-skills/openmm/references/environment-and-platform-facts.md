# Environment and Platform Facts

## Verified Public Import Surface

A temporary inspection environment verified these public imports:

```python
import openmm
import openmm.app
import openmm.unit
```

The same inspection created a one-particle `System`, a `VerletIntegrator`, and a `Context` on the `Reference` platform, then retrieved positions from a `State`. This confirms that the core package can be inspected and that checkout-independent Reference-platform smokes are appropriate.

## Version Caveat

The source checkout recorded in `references/repo-provenance.md` reported OpenMM version components `8.5.0`, while the inspection package reported installed distribution version `8.5.2`. Use source files, docs, and tests as the authority for checkout-specific maintainer work. Use installed-package inspection for stable public API shapes and smoke checks. Refresh this skill if exact version behavior matters.

## Installation Guidance

For user-facing Python work, prefer a released OpenMM package rather than building the local source tree unless the user is changing OpenMM itself.

Typical package-level checks:

```bash
python -m pip check
python - <<'PY'
import openmm, openmm.app, openmm.unit
print(openmm.__version__)
print([openmm.Platform.getPlatform(i).getName() for i in range(openmm.Platform.getNumPlatforms())])
PY
```

OpenMM packaging exposes optional GPU/backend variants. The source metadata includes extras named `cuda12`, `cuda13`, `hip6`, and `hip7` for platform-specific packages on supported non-macOS systems. Match GPU packages to the user's driver, hardware, Python version, and platform instead of installing every extra by default.

## Platform Expectations

- `Reference`: slow, deterministic enough for correctness smokes, and the safest fallback for scripts bundled with this skill.
- `CPU`: practical CPU execution when installed; use thread-related platform properties only after listing supported properties.
- `CUDA`: recommended for NVIDIA GPU production when the plugin/package and driver are compatible.
- `OpenCL`: accelerator option when an OpenCL runtime is available; property names differ from CUDA.
- `HIP`: AMD GPU option when the HIP plugin/package and ROCm stack are compatible.

Always list platforms and supported property names before hard-coding `platformProperties`. A platform visible in one environment may be absent in another.

## Safe Smoke Strategy

- Use root `scripts/openmm_reference_smoke.py` for package-level import/platform/context verification.
- Use `sub-skills/simulation-workflows/scripts/minimal_reference_smoke.py` for application-layer `Simulation`, stepping, reporter, and restart checks.
- Use `sub-skills/force-fields-modeling/scripts/forcefield_modeling_check.py` for ForceField/Modeller smoke checks.
- Use `sub-skills/custom-forces-integrators/scripts/custom_force_smoke.py` for expression-force validation.
- Use `sub-skills/platforms-performance/scripts/check_openmm_platforms.py` for platform inventory and optional per-platform context smokes.

Keep smoke runs short, file-light, and Reference/CPU-compatible unless the user explicitly asks to exercise GPU hardware.
