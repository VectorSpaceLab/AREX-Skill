---
name: data-metadata-and-sqllab
description: "Route CubeStudio dataset, metadata, dimension, SQLLab, and ETL
  data workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Data, Metadata, and SQLLab

Use this sub-skill for dataset catalog records, metadata and dimension tables, SQLLab request lifecycle, and ETL data movement.

## Use this sub-skill when

- you need to inspect or explain dataset fields, storage paths, downloads, previews, or version history
- you need to validate metadata tables, metric catalogs, or dimension-table schemas and permissions
- you need to check SQLLab engine names, URI template shape, query status, or result download behavior
- you need to understand ETL pipeline records, task syncing, or the bundled data-import/export templates

## Consult first

- `references/data-workflows.md`
- `references/sqllab-and-engines.md`
- `references/etl-pipelines.md`
- `references/troubleshooting.md`
- `scripts/validate_sqllab_request.py`

## Route away from here

- General Argo workflow mechanics → sibling `../pipelines-and-job-templates/`
- Notebook and image catalog work → sibling `../compute-notebooks-and-images/`
- Cluster install, registry, or deployment operations → sibling `../deploy-and-operate/`
- Serving, AIHub, or inference-service deployment → sibling `../serving-aihub-and-llm/`

## Safe operating rules

- Prefer static inspection and bundled validation only.
- Do not start databases, schedulers, containers, or long-running services.
- Keep source evidence distilled into the bundled references and script.
