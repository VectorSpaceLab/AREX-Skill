---
name: dataflow
description: "Use Tensorpack DataFlow, datasets, augmentors, serializers, input
  sources, and performance-tuning utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tensorpack DataFlow Skill

Use this sub-skill when the user needs Tensorpack data loading, preprocessing,
serialization, image augmentation, TensorFlow input-source bridging, or data
pipeline performance diagnosis. Keep answers self-contained: rely on the bundled
references and script here instead of reopening the original repository.

## Read first

1. For exact API signatures, component roles, optional dependencies, and gotchas,
   read [`references/api-reference.md`](references/api-reference.md).
2. For concrete construction recipes and decision trees, read
   [`references/workflows.md`](references/workflows.md).
3. For symptom-to-recovery guidance, read
   [`references/troubleshooting.md`](references/troubleshooting.md).
4. For a safe serializer availability/roundtrip check, use
   [`scripts/dataflow_serializer_smoke.py`](scripts/dataflow_serializer_smoke.py).

## Use this when

- The task mentions `tensorpack.dataflow`, `DataFlow`, datapoints, components,
  `reset_state()`, `__iter__()`, `BatchData`, `MapData`, `MapDataComponent`,
  `FakeData`, `DataFromList`, `DataFromGenerator`, `RepeatedData`, or `PrintData`.
- The user asks how to choose between parallel runners and parallel mappers, or
  between threads, processes, and ZeroMQ data pipes.
- The task involves `LMDBSerializer`, `NumpySerializer`, `TFRecordSerializer`,
  `HDF5Serializer`, optional serializer imports, or a data serialization
  roundtrip.
- The task involves `tensorpack.dataflow.imgaug`, `AugmentorList`, deterministic
  image transforms, coordinate transforms, `Flip`, `Resize`, `CenterCrop`,
  `GoogleNetRandomCropAndResize`, dtype conversions, contrast, or brightness.
- The task asks how a DataFlow feeds Tensorpack trainers through `FeedInput`,
  `QueueInput`, `StagingInput`, `TFDatasetInput`, `TensorInput`, or `ZMQInput`.
- The task involves Tensorpack dataset loaders such as `Mnist`, `Cifar10`,
  `SVHNDigit`, `ILSVRC12`, or `ILSVRC12Files`.
- The task is about queue size, `TestDataSpeed`, random disk reads, CPU-bound
  augmentation, network/IPC bottlenecks, or slow input pipelines.

## Route elsewhere

- Model definitions, trainer selection, callbacks, summaries, and full training
  loops belong in [`../training/SKILL.md`](../training/SKILL.md).
- Offline prediction, export, checkpoint loading, `.npz` model-zoo variables,
  and checkpoint inspection belong in
  [`../inference-export/SKILL.md`](../inference-export/SKILL.md).
- Full domain example command catalogs belong at the root example catalog and the
  training example recipes:
  [`../../references/examples-catalog.md`](../../references/examples-catalog.md)
  and [`../training/references/example-recipes.md`](../training/references/example-recipes.md).

## Operating model

Tensorpack DataFlow is a pure-Python iterator system. A source DataFlow yields
one datapoint at a time; wrappers transform, filter, batch, shuffle, prefetch,
or serialize those datapoints. A datapoint is normally a list of components, but
some DataFlow utilities also support dict datapoints. Tensorpack trainers do not
usually consume DataFlow directly; an `InputSource` turns a DataFlow or another
input producer into tensors in the TensorFlow graph.

Default answer pattern:

1. Identify whether the user needs a source, wrapper, parallelization,
   serialization, augmentation, dataset loader, InputSource, or performance
   diagnosis.
2. State the DataFlow contract: implement `__iter__()`, call `reset_state()` in
   the process that will iterate, treat `__len__()` as optional/rough unless the
   downstream consumer needs exact size, and avoid concurrent iteration of one
   non-reentrant instance.
3. Choose the smallest composition that preserves correctness before optimizing
   speed.
4. For training, allow distribution-preserving duplication/reordering only when
   it is acceptable for stochastic training. For validation/inference, preserve
   exact membership and usually exact ordering.
5. Use `PrintData` and `TestDataSpeed` before guessing. If a trainer queue is
   close to empty, diagnose the input pipeline; if it is full, route graph or
   trainer speed questions to training.

## Quick decisions

- New custom data format: write a source `DataFlow` or wrap a generator with
  `DataFromGenerator`; then compose maps, augmentors, batches, and prefetching.
- In-memory toy or deterministic tests: use `FakeData` or `DataFromList`.
- Map one component: use `MapDataComponent(ds, func, index=...)`; map/filter a
  full datapoint: use `MapData(ds, func)`, returning `None` to drop it.
- Batch same-shaped components: use `BatchData(ds, batch_size)`; use
  `use_list=True` when components have variable shapes such as raw images.
- Training prefetch with independent stochastic workers: use
  `MultiProcessRunnerZMQ` or `MultiThreadRunner` only when duplicated/reordered
  i.i.d. samples are acceptable.
- Preserve set membership while parallelizing expensive transforms: use
  `MultiThreadMapData` or `MultiProcessMapData`/`MultiProcessMapDataZMQ`; use
  `strict=True` for finite validation-style passes, remembering order is still
  not preserved.
- Random-read ImageNet-like data on slow disks: consider serializing encoded
  bytes to LMDB, then sequentially read, locally shuffle, decode, augment, and
  batch.
- Feed a Tensorpack trainer: prefer `QueueInput(dataflow)` for most DataFlow
  training; wrap with `StagingInput` when GPU staging is useful; use
  `TFDatasetInput` or `TensorInput` for TensorFlow-native input pipelines.

## Reference tasks

- Build or audit a custom DataFlow contract: use
  [`references/workflows.md#custom-source-dataflow`](references/workflows.md#custom-source-dataflow)
  and the DataFlow section of
  [`references/api-reference.md#dataflow-object-contract`](references/api-reference.md#dataflow-object-contract).
- Compose maps, filters, batches, and debug prints: use
  [`references/workflows.md#compose-maps-batches-and-debug-prints`](references/workflows.md#compose-maps-batches-and-debug-prints).
- Decide runner vs mapper / threads vs processes: use
  [`references/workflows.md#parallelism-decision-tree`](references/workflows.md#parallelism-decision-tree).
- Serialize and reload tiny or large DataFlows: use
  [`references/workflows.md#serialization-roundtrips`](references/workflows.md#serialization-roundtrips)
  and the bundled smoke script.
- Create ImageNet-style training/validation pipelines: use
  [`references/workflows.md#imagenet-style-pipelines`](references/workflows.md#imagenet-style-pipelines).
- Distill a TIMIT-style LMDB preprocessing pattern: use
  [`references/workflows.md#timit-style-lmdb-pattern`](references/workflows.md#timit-style-lmdb-pattern).
- Bridge to Tensorpack trainers: use
  [`references/workflows.md#inputsource-bridge-to-trainers`](references/workflows.md#inputsource-bridge-to-trainers).
- Diagnose speed: use
  [`references/workflows.md#performance-diagnosis`](references/workflows.md#performance-diagnosis)
  and [`references/troubleshooting.md#slow-or-empty-queues`](references/troubleshooting.md#slow-or-empty-queues).

## Safe checks

Use the bundled script for serializer availability, optional dependency messages,
and tiny deterministic roundtrips:

```bash
python sub-skills/dataflow/scripts/dataflow_serializer_smoke.py --help
python sub-skills/dataflow/scripts/dataflow_serializer_smoke.py \
  --workdir <scratch-dir> --formats numpy
python sub-skills/dataflow/scripts/dataflow_serializer_smoke.py \
  --workdir <scratch-dir> --formats all
```

The script writes only under `--workdir`, uses tiny synthetic datapoints, avoids
network and downloads, and does not require original Tensorpack source files.

## Hard boundaries

- Do not recommend running original example or test files as part of answering a
  user question. Use the distilled recipes and bundled helper instead.
- Do not claim GPU or multi-node performance verification from this skill; the
  DataFlow references document CPU/IPC/disk/network reasoning and route trainer
  scaling to training.
- Do not expose machine-specific environment or filesystem locations in
  user-facing answers.
- Do not use runner-style parallelism for validation unless the user explicitly
  accepts potential duplication and reordering; use mapper-style strict passes or
  a single runner process for exact validation-style data.
