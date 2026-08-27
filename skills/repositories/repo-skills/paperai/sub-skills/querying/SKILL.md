---
name: querying
description: "Guides paperai semantic and weighted queries, result filtering,
  article metadata display, interactive shell use, enriched API search, and
  optional search UI integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Querying

Use this route for one-shot paper searches, interactive terminal queries, API
integration, or a small application around a saved paperai index. It assumes
an `articles.sqlite` database and compatible txtai model directory already
exist; route index construction to [indexing](../indexing/SKILL.md). Route
multi-query Markdown/CSV/annotation generation to
[reporting](../reporting/SKILL.md).

## Fast route

1. Confirm the model directory contains both `articles.sqlite` and a saved
   embeddings config/model.
2. Run `python -m paperai.query "your query" [topn] [model-dir] [threshold]`.
3. Use `+token` to require a token and `-token` to exclude matching sections;
   start with the default threshold of `0.25`.
4. For repeated terminal use, run `paperai <model-dir>` and enter queries at
   the `(paperai)` prompt. For services, configure txtai's API with
   `paperai.api.API` and use its enriched article response.

Read [api-reference.md](references/api-reference.md) for method signatures and
response fields, [cli-reference.md](references/cli-reference.md) for command
forms, [workflows.md](references/workflows.md) for recipes, and
[troubleshooting.md](references/troubleshooting.md) for failure recovery.

## Important behavior

`Query.run` defaults `topn` to 10 through `Query.query` and the search threshold
to `0.25`. A query of `*` returns no vector matches in the direct query path;
reports use `*` specially for all articles. A CPU package import or framework
availability check does not validate a particular downloaded embedding model.
