---
name: data-training
description: "Route NeuroMANCER data preparation and CPU-first training
  workflows for dictionary, static, sequence, and graph data, including
  normalization, splitting, collation, Trainer, Lightning, callbacks, logging,
  and checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data and training

Use this sub-skill when a NeuroMANCER task starts with tensors/arrays and must
produce named batches, sequence windows, graph batches, or a bounded training
run. It is written for `neuromancer==1.5.6` and a CPU-first workflow.

## Route the request

- **Dictionary/static samples:** use `DictDataset` or `StaticDataset`, then a
  `DataLoader` with the dataset's `collate_fn`. See
  [API reference](references/api-reference.md) and
  [data formats](references/data-formats.md).
- **Time series or multiple trajectories:** use `SequenceDataset` directly or
  `get_sequence_dataloaders`; preserve the `*p`/`*f` key contract and validate
  `nsteps` before constructing windows.
- **Node/edge/graph batches:** use `GraphDataset` with precomputed graphs or
  its local radius-graph builder. Treat graph batching as a separate contract;
  do not silently substitute ordinary dictionary collation.
- **Optimization:** choose the base `Trainer` when explicit PyTorch loaders,
  callbacks, and a CPU device are desired. Choose `LitTrainer` when the
  `data_setup_function`/Lightning lifecycle, checkpoint callbacks, or custom
  Lightning hooks are desired. The two APIs are not interchangeable.

Follow [workflows](references/workflows.md) for the smallest safe setup. Keep
symbolic objectives/constraints in `symbolic-problems`, model and dynamics
construction in `dynamics-modeling`, and PSL/control rollouts in
`control-simulation`.

## Non-negotiable batch contract

1. Every sample-bearing tensor has the same first/sample axis before a dataset
   is built.
2. Every loader uses the owning dataset's `collate_fn`; it adds the `name`
   field consumed by NeuroMANCER problem outputs.
3. Split raw data before fitting normalization statistics. Apply train
   statistics to development and test data; do not use the convenience
   dataloader normalization path when that would leak held-out values.
4. Start with `device="cpu"` for `Trainer` or `accelerator="cpu"` for
   `LitTrainer`; CUDA and multi-device behavior is optional and unverified.
5. Keep development data named `dev` and training data named `train` when using
   `LitDataModule`.

## Validate before training

Run the bundled, side-effect-free smoke check from any working directory:

```bash
python scripts/data_smoke.py --help
python scripts/data_smoke.py --run
```

`--run` creates only tiny in-memory static, dictionary, and sequence fixtures;
it performs no training, network access, checkpointing, or writes. For failure
recovery and known source-version edge cases, use
[troubleshooting](references/troubleshooting.md).
