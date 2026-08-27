# Large-Scale Graph Workflows

## Partitioned Training

1. Load the graph with `get_data`.
2. Partition it with `metis`.
3. Permute the data into partition order with `permute`.
4. Use `SubgraphLoader` for training and `EvalSubgraphLoader` for evaluation.
5. Train a large-graph model with the partitioned batches.
6. Evaluate with `compute_micro_f1`.

## Memory/Buffer Helpers

- `FeatureMomentum` maintains a per-node embedding memory buffer.
- `AsyncIOPool` is the async transfer helper used by the GraphFMOB code path when the compiled extension is present.

## Example Guidance

- The repository example scripts for GraphFMOB and Reddit neighbor sampling are useful as evidence for loader order and partition behavior, but the generated skill should rely on bundled guidance and scripts.
