# GemPy cross-cutting troubleshooting

Use the smallest caller-owned reproducer and record Python, GemPy,
`gempy_engine`, optional viewer version, backend, grid flags, and the exact
exception. Diagnose in this order:

1. **Interpreter/core import:** use Python 3.10+ and verify `gempy` plus
   `gempy_engine` with the same interpreter. Run `python -m pip check`.
2. **Optional boundary:** install only the dependency for the requested feature
   (`gempy[base]` for pandas/viewer, optional scientific packages for SciPy or
   mesh/plugin workflows, a matching Torch build for PyTorch).
3. **Backend:** prove NumPy first. A CPU import does not prove a PyTorch/CUDA
   path. If GPU fallback is accepted, record `GEMPY_GPU_FALLBACK=True` and the
   actual CPU fallback.
4. **Semantic validation:** call `model.validate()` and preserve
   `ModelValidationError.reason`, `.field`, `.message`, and `.context`.
5. **Workflow state:** inspect structural groups, input counts, active grid
   flags, solution type, archive suffix, or JSON schema according to the owning
   route.
6. **Viewer/headless:** separate model/grid correctness from Matplotlib,
   PyVista, VTK, display-server, and OpenGL failures. Use `MPLBACKEND=Agg`,
   `show=False`, or supported off-screen rendering for artifacts.
7. **Provenance drift:** compare the package versions and relevant options with
   [`repo-provenance.md`](repo-provenance.md) before calling a changed behavior
   a regression.

## Common recovery actions

- `ModuleNotFoundError: gempy_engine`: repair the core GemPy installation; a
  viewer package cannot replace the engine.
- `import gempy_viewer` fails while core imports work: treat viewer/pandas as an
  optional base boundary and keep core NumPy checks separate.
- `empty_model`, `underdetermined_input`, or empty-group errors: repair the
  input tables or structural frame; do not use `skip_validation=True` as a fix.
- Fault relation shape/direction errors: map all elements first, count final
  structural groups, then set a square matrix whose forward entries affect only
  younger groups.
- Unexpected result length: a custom, section, topography, centered, or old
  grid flag remains active. Reset the intended flags and recompute.
- `.gempy` suffix/schema failures: use the native suffix contract and compare a
  restored model's inputs, groups, grid, and fault matrix before recomputing.
- Missing `gempy_plugins`, `gstools`, `subsurface`, `pyvista`, `skimage`,
  `gempy_legacy`, or `torch`: report the requested optional capability as
  unavailable and install/version-check only that boundary.

Detailed failure matrices and owning-route handoffs are in each sub-skill's
`references/troubleshooting.md`.
