# QM9 Data Layouts

## Required artifacts

This sub-skill bundles the benchmark split artifact at:

```text
references/random_split.t
```

The benchmark runner expects that artifact to be available when it computes the
train, validation, and test partitions.

## Dataset root

`torch_geometric.datasets.QM9` expects a writable dataset root directory. The
exact cache layout is handled by PyG, so the main requirement is that the root
is stable and accessible to the environment running the benchmark.

## Targets

The default target list used by the example contains 11 property indices. The
workflow can be adapted by changing the `target` list, but the split artifact
remains part of the benchmark recipe.

## Minimal validation idea

A valid setup should be able to:

- read the bundled split artifact,
- open the QM9 dataset root,
- and build the graph loaders without shape errors.
