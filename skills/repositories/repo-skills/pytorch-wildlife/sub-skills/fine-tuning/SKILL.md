---
name: fine-tuning
description: "Use the legacy Pytorch-Wildlife companion workflows to validate
  camera-trap classification or detection datasets, prepare configuration, and
  integrate produced weights without launching expensive training by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fine-tuning

Use this sub-skill for the companion/legacy classification and detection
fine-tuning modules. It covers dataset contracts, split design, YAML/config
preflight, CLI orientation, and post-training weight handoff. These modules
are separate from the current core inference APIs and are best treated as
experimental compatibility workflows.

## Safety and status

- Do not start training, validation, inference, model downloads, external
  loggers, or services as a default action. They can be GPU-hour, disk, network,
  or credential bound.
- Run the bundled split helper and static/YAML checks first; inspect a small
  fixture before approving a real run.
- The classification companion documents Python 3.9 and its environment pins
  Python 3.8-era dependencies, including Lightning 1.9 and old TorchVision.
  The detection companion documents Python 3.10 and a separate Ultralytics
  stack. The installed package is PytorchWildlife 1.3.0 and requires Python
  >=3.10, so do not assume either companion environment is interchangeable
  with the core environment.
- A checkpoint produced by a companion workflow is not automatically a core
  PytorchWildlife weight. Validate architecture, checkpoint format, class
  names, and wrapper expectations before using it for core inference.

## Choose a workflow

1. Choose **classification** for a flat image directory and a CSV with
   `path`, `classification`, and `label` columns. Add `Location` for a
   location split or `Photo_Time` for a sequence split.
2. Choose **detection** for YOLO-format images and labels arranged into
   train/val/test partitions, with a dataset YAML describing those partitions.
3. Choose **data validation** before either workflow, especially when images
   came from camera bursts or when a YAML was authored by hand.
4. Route core model inference and detector-to-classifier crop behavior to the
   detection/classification sub-skills. Route audio training to bioacoustics.

Detailed contracts and checks:

- [Classification fine-tuning](references/classification-fine-tuning.md)
- [Detection fine-tuning](references/detection-fine-tuning.md)
- [Data validation](references/data-validation.md)
- [Troubleshooting](references/troubleshooting.md)
- [Safe classification splitter](scripts/split_classification_annotations.py)

## Required preflight

1. Work from a copied config and a reproducible output directory. Preserve the
   original annotation file; the companion split utility writes three CSVs.
2. Confirm every referenced image exists, is a supported image type, and is
   readable as RGB. Confirm labels are contiguous integers where the selected
   training code expects them, and that class names do not disagree by split.
3. For camera traps, prefer location or sequence grouping over random splitting.
   Random splitting can place near-identical burst frames in train and
   validation, producing leakage and inflated metrics.
4. Validate YAML paths relative to the YAML's intended dataset root, and check
   that every image has a matching label file where detection labels are
   expected. Reject out-of-range or malformed normalized boxes.
5. Record the Python, Torch/Lightning or Ultralytics versions, device choice,
   model identifier, class mapping, split seed, and output directory before
   any expensive command.

The bundled helper is intentionally limited to annotation splitting. Its
`--help` path and tiny CSV fixture are safe checks; it never constructs a
model, downloads weights, starts a logger, or trains.

## Decision boundaries

- Use a random split only when temporal, location, and burst independence are
  already established. Otherwise prefer the strongest grouping metadata
  available, and state when class balance is sacrificed.
- A classification CSV is not enough to prove that the companion crop stage
  is ready. Confirm the crop annotations, detector checkpoint, and output
  paths separately; core detector inference belongs to the detection route.
- A valid detection label file is not enough to prove model compatibility.
  Check YAML class ordering, the selected YOLO/RTDETR family, license terms,
  and the installed Ultralytics version before a user-approved run.
- Treat CPU parser and fixture checks as structural verification only. They do
  not validate GPU throughput, convergence, mAP, or checkpoint quality.
- Keep experiment logs local by default. A remote logger, service, or upload
  is an explicit follow-up decision, not part of preflight.

## Verification evidence

For a safe handoff, retain the splitter command and seed, emitted row counts,
location/sequence disjointness result, YAML parse result, class mapping, and
version/device notes. Mark model loading, weight integration, training,
validation, and inference as unverified unless they were explicitly run with
approved local artifacts. A failure caused by an old companion dependency is
an environment limitation, not evidence that the dataset or model is correct.

## Handoff checklist

Before integrating a produced checkpoint, retain the training config and
class mapping next to the weight, identify the actual run directory and best
checkpoint, and test loading with a local weight in an isolated environment.
Do not infer compatibility from a filename. If the core wrapper rejects the
weight or expects a different state-dict/model format, keep the checkpoint in
its companion workflow and route ordinary inference elsewhere.
