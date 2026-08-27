---
name: pywavelets
description: "Routes PyWavelets users to discrete transforms, wavelet-family and
  CWT workflows, and wavelet-packet tree operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyWavelets

PyWavelets provides wavelet transforms in Python through the `pywt` package.

## Start here

- Install from PyPI: `python -m pip install PyWavelets`
- From this checkout: `python -m pip install -e .` after the source build dependencies are available.
- The current checkout's source build metadata requires Python 3.12+.
- Core runtime only needs NumPy; Matplotlib is optional for plot-heavy demo parity.
- Run `python scripts/check_pywavelets_install.py` from this skill directory for a no-network smoke check.
- Minimal import check:

  ```bash
  python - <<'PY'
  import pywt
  print(pywt.__version__)
  PY
  ```
- Read `references/repo-provenance.md` before deciding whether this skill still matches the current checkout.
- Read `references/package-overview.md` for the package map and bundled sample data.
- Read `references/troubleshooting.md` when imports, builds, transform parameters, or packet paths fail.

## Route by task

- Discrete wavelet transforms, inverse transforms, multilevel coefficient trees, stationary transforms, multiresolution analysis, coefficient packing, thresholding, signal extension modes, padding, or fully separable transforms: use `sub-skills/discrete-transforms/SKILL.md`.
- Wavelet families, custom wavelets, wavelet functions, continuous wavelet transforms, scale/frequency conversion, or bundled demo signals/data: use `sub-skills/wavelets-and-cwt/SKILL.md`.
- Wavelet packet trees in 1D/2D/ND, path-based node lookup, and packet reconstruction: use `sub-skills/wavelet-packets/SKILL.md`.

## Common defaults

- Prefer `wavelet='db1'` or `wavelet='haar'` for tiny smoke checks.
- Prefer `mode='symmetric'` for decimated DWT/IDWT workflows unless the task says otherwise.
- Use `mode='periodization'` when the workflow is explicitly SWT-based or when `mra(..., transform='swt')` is requested.
- Use `pywt.Modes.modes` to confirm supported signal extension modes.
- Use `pywt.wavelist()` and `pywt.families()` before choosing a custom wavelet family.
- Use `pywt.data.camera()`, `pywt.data.ascent()`, `pywt.data.aero()`, `pywt.data.ecg()`, or `pywt.data.nino()` as bundled sample inputs.

## What this skill does not do

- It does not replace the focused subskills for transform, CWT, or packet workflows.
- It does not depend on the original checkout remaining present after extraction.
- It does not require plot windows, downloads, or accelerator backends for the core workflows in this repo.

## Bundled helpers

- `scripts/check_pywavelets_install.py` checks importability and representative transform, CWT, and packet smoke paths.

## Reference files

- `references/package-overview.md` summarizes the public package surface and source-build expectations.
- `references/data-and-demo-signals.md` lists bundled example arrays and demo signals that are safe for smoke checks.
- `references/troubleshooting.md` collects cross-cutting install, import, build, and transform failures.
