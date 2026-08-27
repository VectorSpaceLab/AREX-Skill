# Still-image troubleshooting

## `No face detected`

- Symptom: `demo.py` exits immediately after detection.
- Likely cause: the input has no visible face, the face is too small/oblique,
  or the detector assets are missing.
- Recovery: try one of the bundled sample inputs first, then confirm the
  detector checkpoint and the selected config.

## Missing output files

- Symptom: the script prints no error but the expected image/mesh is absent.
- Likely cause: the output directory is not writable, or the selected output
  mode writes a different suffix than expected.
- Recovery: confirm the `examples/results/` path exists, check the basename and
  suffix logic, and re-run with `--show_flag false` in a headless environment.

## `uv_tex` failures

- Symptom: UV texture output fails during matrix loading or interpolation.
- Likely cause: SciPy is missing, or the UV config files are absent.
- Recovery: verify the SciPy dependency set and the `BFM_UV.mat` / `indices.npy`
  assets.

## Render/depth/PNCC failures

- Symptom: `3d`, `depth`, or `pncc` mode fails to import or render.
- Likely cause: `Sim3DR_Cython` or `render.so` is missing.
- Recovery: return to the setup sub-skill and rebuild the native pieces.

## Headless plotting

- Symptom: the process blocks on a plot window in a non-GUI environment.
- Likely cause: `show_flag` is still enabled.
- Recovery: keep `--show_flag false` or use the bundled wrapper, which defaults
  to a headless plotting backend.
