---
name: hls4ml
description: "Convert, tune, and deploy hls4ml FPGA inference projects from
  Keras, PyTorch, and ONNX inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# hls4ml

Use this skill for hls4ml model conversion, backend project generation, tuning, and extension workflows.

## Install

- Base package: `pip install hls4ml`
- Frontend smokes and most CPU inspection tasks: add `hls4ml[testing]`
- Keras 2 / QKeras / HGQ workflows: add `hls4ml[testing-keras2]`
- Profiling and plotting: add `hls4ml[profiling]`
- Distributed arithmetic: add `hls4ml[da]`
- SNN helpers: add `hls4ml[snn]`
- Symbolic regression helpers: add `hls4ml[sr]`

Read `references/install-and-environment.md` if you need to choose between Keras 2 and Keras 3 families or if the optimization extra needs a separate Python version.

Quick import check:

```bash
python -c "import hls4ml; print(hls4ml.__version__)"
```

For a richer read-only probe, run `scripts/check_install.py`.

## Route map

- `frontends` — Keras, PyTorch, ONNX, quantized, spiking, serialization, and conversion smoke checks.
- `backends` — backend selection, generated projects, build/report flows, and report parsing.
- `analysis` — profiling, precision inference, bit-exact propagation, and resource tuning.
- `extensions` — custom layers, optimizer passes, template hooks, and backend/writer plugins.

## Read first when checking freshness

- `references/repo-provenance.md`
- `references/troubleshooting.md`

## Shared inspection helper

- `scripts/check_install.py` — print the installed package version, backend registry, supported-layer counts, and optional dependency status.
