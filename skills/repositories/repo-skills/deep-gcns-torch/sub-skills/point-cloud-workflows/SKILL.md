---
name: point-cloud-workflows
description: "Operate the DeepGCNs point-cloud workflows for ModelNet40
  classification, S3DIS dense or sparse semantic segmentation, and PartNet part
  segmentation, including tensor contracts, exact configuration flags,
  checkpoint/evaluation boundaries, and safe synthetic verification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Point-cloud workflows

Use this skill for a point-cloud task involving ModelNet40 classification,
S3DIS semantic segmentation, or PartNet part segmentation. It is a reference
workflow, not a training runner: do not download data, fetch checkpoints, run
long training, launch distributed jobs, or open a visualization GUI from this
skill.

## Route first

- **ModelNet40 classification**: follow [workflows.md](references/workflows.md)
  and the ModelNet section.
- **S3DIS semantic segmentation**: choose dense or sparse using the decision
  rule in [workflows.md](references/workflows.md), then validate the layout in
  [data-formats.md](references/data-formats.md).
- **PartNet part segmentation**: follow [partnet.md](references/partnet.md);
  raw-data preparation and checkpoint/category matching are mandatory before
  evaluation.
- **Generic GCN layers, EdgeConv/MRConv, KNN, blocks, GENConv, or reversible
  primitives**: route to the sibling `graph-layers` skill. This skill only
  records the task-level layout and configuration needed to use those layers.
- **OGB or PPI**: route to the sibling `ogb-workflows` or `ppi-workflows`
  skill. Do not substitute S3DIS, PartNet, or ModelNet conventions for those
  datasets.

## Safe operating sequence

The command blocks in the references are non-executable command shapes for an
independently staged implementation. Replace only their neutral entrypoint and
resource placeholders; never use them to open or run files from an original
source checkout. The bundled smoke below is the only direct executable in this
skill.

1. State the task, dataset split, category/area, point count, feature count,
   dense/sparse layout, backend/device, and whether a checkpoint is supplied.
2. Run the bundled smoke from any current working directory before importing a
   project model:

   ```bash
   python <skill-root>/scripts/pointcloud_model_smoke.py --help
   python <skill-root>/scripts/pointcloud_model_smoke.py --mode all
   ```

   The script is self-contained and uses only a tiny synthetic fixture. It
   does not import `gcn_lib`, PyG, `torch_cluster`, a dataset, or a checkpoint.
3. Pre-stage data and checkpoints outside the skill. Treat every documented
   automatic download as disabled for this operating path.
4. Use the task's exact parser flags and verify that the checkpoint's class
   count, block, convolution, filters, blocks, KNN settings, category/area,
   and layout agree with the current request.
5. Start with the smallest non-distributed evaluation or forward pass. Reduce
   points, `k`, batch size, or blocks when diagnosing memory; do not infer
   benchmark-quality results from the smoke.

## Invariants

- Coordinates are the first three channels. S3DIS normally supplies 3-D
  positions plus six additional features (`in_channels=9`); ModelNet and the
  default PartNet path use positions only (`in_channels=3`).
- Dense point-cloud models consume `B x C x N x 1`; sparse models consume
  node features `N x C` plus a node-to-graph `batch` vector of length `N`.
- Classification returns one logit vector per cloud. Segmentation returns one
  logit vector per point; never pool away the point axis for S3DIS or PartNet.
- `k` is the requested neighborhood width and dilation internally asks for
  `k * dilation` candidates. It must not exceed the number of points in each
  cloud. Matrix KNN has quadratic point-count memory.
- `--use_cpu`/CPU availability selects the device, but installed PyTorch,
  PyG, `torch_scatter`, and `torch_cluster` binaries still need to be ABI and
  backend compatible. See [troubleshooting.md](references/troubleshooting.md).

## Scope boundary

The references preserve source-observed commands, defaults, data fields, and
failure modes without copying full training programs. They deliberately omit
network downloads, external-drive checkpoint retrieval, distributed launch
recipes as executable actions, and VTK execution. A result is not verified
until the requested data/checkpoint and backend are separately available and
an appropriate task-level test has passed.
