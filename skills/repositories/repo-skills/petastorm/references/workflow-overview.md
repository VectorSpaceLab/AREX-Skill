# Workflow Overview

## Purpose

Read this when you need a quick route map without opening every sub-skill reference. It connects natural user requests to the owning
Petastorm route.

## Route map

| User task family | Main route | Best first reference |
| --- | --- | --- |
| Read a Petastorm dataset, apply predicates, use NGrams, adapt to TF/Torch, or benchmark throughput | `sub-skills/read-datasets/` | `sub-skills/read-datasets/references/workflows.md` |
| Define schemas, write datasets, copy or repair metadata, or build row-group indexes | `sub-skills/create-datasets/` | `sub-skills/create-datasets/references/workflows.md` |
| Materialize a Spark DataFrame into reusable TF/Torch loaders | `sub-skills/spark-converter/` | `sub-skills/spark-converter/references/workflows.md` |

## Selection hints

- Use `read-datasets` when the task starts from an existing dataset or asks how to consume a dataset from Python, TensorFlow, PyTorch,
  Spark RDDs, or a throughput benchmark.
- Use `create-datasets` when the task starts from raw rows, schema definitions, metadata repair, or dataset copying and filtering.
- Use `spark-converter` when the task starts from a Spark DataFrame that should be cached once and reused many times for training or evaluation.

## Common boundary rule

- Reader questions belong in `read-datasets`.
- Writer, metadata, and schema questions belong in `create-datasets`.
- Spark cache conversion questions belong in `spark-converter`.
