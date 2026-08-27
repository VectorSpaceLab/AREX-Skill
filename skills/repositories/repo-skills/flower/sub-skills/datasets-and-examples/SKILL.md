---
name: datasets-and-examples
description: "Use Flower Datasets and example app patterns without reopening the
  source repo."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Flower Datasets and Examples

Use this sub-skill when the user needs Flower Datasets, partitioning workflows, or example-project wiring patterns.

## Use for
- `FederatedDataset`, partitioners, preprocessors, and visualization
- local CSV/JSON/image/audio and in-memory data flows
- `flwr-datasets create` for IID demo partitions on disk
- example app catalogs and dependency variants from `examples/*/pyproject.toml`

## Stay out of
- Flower core app authoring beyond example layout clues
- deployment admin and strategy internals

## Route
1. Prefer `FederatedDataset` for Hugging Face Hub data.
2. For local or in-memory data, build a `datasets.Dataset` first and assign it to a partitioner directly.
3. Use `IidPartitioner` for even splits, `DirichletPartitioner` for label skew, and `PathologicalPartitioner` for exact class-count constraints.
4. Use `Divider` or `Merger` to reshape splits before partitioning.
5. Use `plot_label_distributions` or `plot_comparison_label_distribution` to inspect heterogeneity.
6. Use `scripts/catalog_examples.py` to compare example dependency stacks and `tool.flwr.app` wiring.

## References
- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`

## Helpers
- `scripts/check_flwr_datasets.py`
- `scripts/catalog_examples.py`
