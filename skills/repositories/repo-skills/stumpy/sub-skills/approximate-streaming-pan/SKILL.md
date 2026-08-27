---
name: approximate-streaming-pan
description: "Use STUMPY anytime approximation, streaming updates, online
  segmentation, and pan matrix profile APIs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# approximate-streaming-pan

Use this sub-skill when the task is about STUMPY workflows that update over time or trade exactness for speed:

- anytime/approximate matrix profiles with `scrump`, `scraamp`, `prescrump`, or `prescraamp`;
- incremental matrix profiles for streaming data with `stumpi` or `aampi`;
- online semantic-segmentation state with `floss`;
- pan matrix profile / window-size exploration with `stimp` or `aamp_stimp`.

## Route away

- Exact 1-D matrix-profile setup, self-joins, AB-joins, dtype/window validation, and profile-column fundamentals belong in `../matrix-profile-basics/SKILL.md`.
- Dask/Ray `stimped`/`aamp_stimped` and CUDA `gpu_stimp`/`gpu_aamp_stimp` setup belong in `../distributed-gpu-acceleration/SKILL.md`.
- Interpreting discovered motifs, discords, regime changes, snippets, or segmentation decisions belongs in `../motifs-anomalies-segmentation/SKILL.md`.

## Operating flow

1. Confirm the user needs approximate, streaming, online segmentation, or window-size-selection behavior rather than an exact one-shot profile.
2. Choose normalized (`scrump`, `stumpi`, `stimp`, `floss` with `normalize=True`) versus non-normalized p-norm (`scraamp`, `aampi`, `aamp_stimp`, `floss(..., normalize=False, p=...)`).
3. For anytime objects, create the object, then call `.update()` repeatedly until the budget or stability criterion is met; read `.P_` and `.I_` after updates.
4. For streaming objects, call `.update(t)` once per scalar observation in arrival order; do not pass a batch array into a single update.
5. For pan matrix profiles, call `.update()` once per processed window-size row; use `.M_` to map rows to window sizes, `.P_` for raw profiles, and `.PAN_`/`.pan(...)` for transformed views.

## Bundled references and smoke script

- `references/api-reference.md` gives signatures, object attributes, and parameter meanings.
- `references/workflows.md` gives task-oriented recipes and acceptance guidance for approximate outputs.
- `references/troubleshooting.md` covers update ordering, egress, convergence, window bounds, pan-state interpretation, and FLOSS state traps.
- `scripts/streaming_pan_smoke.py` runs tiny no-network demos with `--workflow scrump|stumpi|stimp`.

Construction evidence is summarized in the root provenance and integration records; runtime use should rely on this sub-skill's bundled references and scripts.
