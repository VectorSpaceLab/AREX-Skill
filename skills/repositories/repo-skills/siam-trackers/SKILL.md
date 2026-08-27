---
name: siam-trackers
description: "Guide visual object tracking work with the SiamTrackers
  collection, especially NanoTrack model inference, training configuration,
  dataset evaluation, ONNX/performance export, and selection among legacy
  Siamese tracker variants."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# SiamTrackers

Use this repo skill when a task involves NanoTrack, SiamFC/SiamRPN-family
trackers, SiamBAN/SiamCAR/SiamFC++, SiamMask, UpdateNet, TrTr, lightweight
single-object tracking, GOT-10k/VOT/OTB evaluation layouts, or NanoTrack's
ONNX/FLOPs/throughput workflow.

This is a high-reuse operating graph for a historical tracker collection. It is
not a claim that every snapshot is equally complete or compatible with a modern
Python/CUDA stack. Start by identifying the exact tracker variant, task phase,
checkpoint, dataset protocol, backend, and expected evidence.

## Route by task

- **Run or integrate NanoTrack on frames/video:** read
  [inference](sub-skills/inference/SKILL.md).
- **Prepare data or change training/configuration:** read
  [training](sub-skills/training/SKILL.md).
- **Test a tracker, validate result files, compute benchmark metrics, or search
  tracking hyperparameters:** read [evaluation](sub-skills/evaluation/SKILL.md).
- **Export NanoTrack to ONNX, inspect graph shapes, profile MACs/parameters, or
  measure throughput:** read [export](sub-skills/export/SKILL.md).
- **Choose or troubleshoot another collection snapshot:** read
  [variant-catalog](sub-skills/variant-catalog/SKILL.md).

For a request that crosses phases, load the smallest set of routes in order:
variant selection → inference/training → evaluation or export. Do not merge
independent model templates, global configs, checkpoints, or compiled
extensions from different variants in one process without an explicit
compatibility check.

## What is verified

The source collection has a complete NanoTrack implementation and a catalog of
other tracker snapshots. The generated routes are based on source/config
inspection plus live import/signature checks for core NanoTrack modules. The
bundled helpers are deliberately offline and safe by default: they validate
arguments, configs, result layouts, export plans, and measurement methodology;
they do not download datasets or weights, open a GUI, start training, or overwrite
artifacts.

No dataset or pretrained checkpoint is bundled. A successful PyTorch/CUDA
backend smoke does not prove checkpoint compatibility, model tracking quality,
benchmark scores, or mobile deployment. Keep those results separate from static
or synthetic checks. Read [troubleshooting](references/troubleshooting.md) when
an old compiled extension, dependency pin, missing weight, or backend mismatch
is involved.

## Public setup baseline

Use an isolated environment appropriate for the selected workflow. The source
README documents legacy versions such as PyTorch 1.x/CUDA 10-era packages; do
not install those pins blindly on a current host. A modern inspection or
execution environment normally needs a compatible PyTorch build, NumPy,
OpenCV, PyYAML, yacs, Cython, Pillow, SciPy, Matplotlib, tqdm, colorama, and
Shapely. Add `tensorboard`/`tensorboardX`, `thop`, `wget`, and ONNX tooling only
for the selected training, profiling, dataset, or export route.

Before a real run, execute the bundled environment probe from any working
folder:

```bash
python scripts/check_environment.py --json
```

To require a usable CUDA device, use `--require-cuda`; select a free device
with the host's normal device-visibility mechanism rather than assuming device
0. The probe reports missing optional modules and never changes the environment.

The historical implementation has multiple top-level import roots rather than
one reliable modern distribution. For a source checkout, make the relevant
implementation root importable using the checkout's packaging policy, then
run the bundled checks from this skill tree. Do not treat prebuilt `region.so`
files as portable; rebuild the Cython region extension in an isolated copy
before using benchmark code.

## Evidence and freshness

Read [repo-provenance.md](references/repo-provenance.md) before deciding whether
this graph still matches a checkout. If the commit, dirty paths, package
metadata, or major evidence roots differ, use a refresh workflow instead of
silently trusting old API/config claims.

## Hard boundaries

- Do not claim a full tracker result without a matched checkpoint, dataset
  layout, protocol, and recorded metrics.
- Do not call a CPU import equivalent to the CUDA-only portions of training or
  model-runner execution. The training and test scripts call CUDA paths.
- Do not run historical shell launchers, mobile builds, external model/data
  downloads, GUI demos, long training, or full benchmarks as a first diagnostic.
  Establish a tiny, offline gate first and record any skipped native case.
- Treat `LightTrack` and `Ocean` as reference-only entries in this checkout,
  and `SiamFace` as a separate excluded face demo, unless additional source
  evidence is supplied.
- Keep generated validation artifacts outside this runtime skill; they are
  review-only material and are not part of the public operating graph.

## Bundled shared references and helper

- [Troubleshooting](references/troubleshooting.md) covers cross-cutting
  installs, stale Cython binaries, optional dependencies, data/checkpoint
  validation, and backend decisions.
- [Model and variant overview](references/model-overview.md) summarizes NanoTrack
  variants and the collection's evidence-level boundaries.
- [Environment probe](scripts/check_environment.py) is the safe, no-download
  import/backend check linked above.
- [Region extension builder](scripts/build_region_extension.py) rebuilds the
  Cython `toolkit.utils.region` module in a temporary copy by default; pass an
  explicit implementation root and use `--in-place` only when mutation is
  intentional.
