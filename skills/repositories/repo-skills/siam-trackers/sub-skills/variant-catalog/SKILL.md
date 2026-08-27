---
name: variant-catalog
description: "Route natural tracker-variant requests in SiamTrackers,
  distinguish maintained NanoTrack from alternative snapshots and references,
  and select a safe evidence-bounded workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# SiamTrackers variant catalog

Use this skill when a request names an alternative tracker, asks which tracker to
choose, or mixes tracker selection with build, data, training, test, evaluation,
or deployment requirements. The collection's maintained end-to-end workflow is
**NanoTrack**. The other entries are useful historical or comparative snapshots,
but their presence does not prove that their dependencies, checkpoints, data, or
full workflows are still runnable.

## Route first

1. Extract the request's objective: smallest/fastest deployment, baseline
   comparison, anchor-free box tracking, RPN tracking, segmentation, transformer
   tracking, model updating, training, benchmark evaluation, or export.
2. Ask whether the user has a current source checkout, authorized data and model
   artifacts, and a compatible isolated environment. If any is missing, provide a
   plan and an evidence boundary rather than inventing a runnable command.
3. Choose **NanoTrack** for the default maintained workflow, especially for
   lightweight CPU/mobile/embedded inference, training on the collection's
   documented cropped tracking data, or the collection's documented ONNX/NCNN
   direction. Route detailed NanoTrack implementation to the `inference`,
   `training`, `evaluation`, or `export` sibling skill as appropriate.
4. Choose an alternative only when the request names it or its distinctive
   research behavior matters. Use the comparison in
   [variant-overview.md](references/variant-overview.md), then apply the build
   and legacy-runtime gates in [legacy-workflows.md](references/legacy-workflows.md).
5. If the request is only “what is included?”, answer from the catalog and label
   every entry by evidence level. Do not turn a README link, result archive, or
   historical result table into an availability claim.

## Quick selection guide

| Need | First route | Important caveat |
|---|---|---|
| Maintained lightweight tracker | NanoTrack | Detailed model/API/export work belongs to sibling skills. |
| Classic fully-convolutional baseline | SiamFC | Snapshot has train/test/eval code, but no uniform setup contract. |
| RPN baseline or deeper RPN | SiamRPN, then SiamRPNpp | Pysot-like snapshots need their own config/checkpoint pairing. |
| Anchor-free box tracker | SiamBAN or SiamCAR | Source snapshots share legacy Cython/toolkit conventions. |
| Deeper/wider FC or RPN | SiamDW-FC or SiamDW-RPN | Older training/data layout and no shared region setup file. |
| Segmentation plus tracking | SiamMask | Mask datasets and mask-specific model/config are mandatory. |
| Learned template update | UpdateNet | It is an updater layered on DaSiamRPN, not a standalone replacement. |
| Transformer tracker | TrTr | GPU and transformer-compatible legacy stack are expected. |
| SiamFC++ framework variants | SiamFCpp-pysot or video_analyst | These are separate snapshots with different source layouts. |
| LightTrack/Ocean | Reference only | This checkout does not contain their implementation. |

## Evidence levels and non-goals

- **Maintained complete workflow:** NanoTrack has source, configs, launcher
  families, toolkit, build metadata, and documented train/test/eval/export-shaped
  paths. Its full run is still gated on user-supplied data and models.
- **Substantive snapshot:** DaSiamRPN, SiamBAN, SiamCAR, SiamDW-FC,
  SiamDW-RPN, SiamFC, both SiamFCpp snapshots, SiamMask, both SiamRPN
  snapshots, SiamRPNpp, TrTr, and UpdateNet contain implementation roots and
  representative launchers. “Substantive” means source evidence exists, not
  that a modern environment has passed end-to-end execution.
- **Reference-only:** LightTrack and Ocean contain a thin README/reference
  pointer in this collection, not a local implementation or reproducible
  package. Do not route a build or evaluation request to them as if source were
  bundled.
- **Excluded:** SiamFace is a separate face-classification Siamese demo. It is
  not a single-object visual tracker and is outside this catalog.
- This skill does not perform training, benchmark evaluation, checkpoint
  recovery, model download, or export. No full tracking/training/evaluation run
  is claimed by this catalog.

## Common gates before any alternative run

- Work from a user-provided, authorized active checkout or package source; do
  not rely on this skill's original checkout, external official repositories, or
  archive links. The collection's historical download references are provenance
  only, not bundled runtime sources.
- Confirm the selected snapshot's source root, config root, model format,
  expected dataset layout, result directory, and launcher family as one set.
  Do not mix a config, checkpoint, or toolkit from a different variant merely
  because names look similar.
- Use an isolated environment. The historical requirements commonly target
  Python 3.7-era and PyTorch 1.2–1.4-era stacks; treat those pins as
  compatibility evidence, not installation commands. Prefer a deliberately
  tested compatibility matrix over blind downgrades.
- Treat a Cython region extension as a build prerequisite when the selected
  evaluation toolkit imports it. A prebuilt extension compiled for another
  Python ABI is not proof of importability or evaluation correctness.
- Require actual dataset files, annotations/JSON, and matching checkpoints
  before test/eval. Empty directory skeletons, result ZIPs, README metrics, or
  a model filename in a default argument are not sufficient evidence.
- For CUDA or distributed training, check the selected environment, GPU
  visibility, torch/CUDA compatibility, process launcher, and batch/memory plan
  before starting. A preparation smoke test is not a tracker test.

## Route boundaries

- **NanoTrack deep implementation:** use `inference` for stateful model/API
  behavior, `training` for configs and training, `evaluation` for benchmarks,
  and `export` for ONNX/mobile/deployment. This catalog only chooses the route.
- **Alternative implementation details:** stay here for selection, evidence,
  prerequisites, and legacy troubleshooting; do not reproduce large launcher or
  model scripts.
- **Metrics:** historical tables are comparative context only. Report the
  dataset, protocol, checkpoint, config, and measurement source before treating
  a number as a result.
- **External acquisition:** request an authorized local artifact or an approved
  acquisition procedure from the user. Never claim that a named official repo,
  BaiduYun archive, password, or thin README is available to a future runtime.

## Bundled references

- [Variant overview](references/variant-overview.md): source-root inventory,
  evidence labels, comparison matrix, and per-variant routing.
- [Legacy workflows](references/legacy-workflows.md): build, data/model,
  train/test/eval, and deployment patterns distilled from representative bins.
- [Troubleshooting](references/troubleshooting.md): compatibility conflicts,
  extension failures, artifact mismatches, and safe stop conditions.
