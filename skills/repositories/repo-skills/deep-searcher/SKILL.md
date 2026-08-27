---
name: deep-searcher
description: "Route DeepSearcher workflows for provider setup, data ingestion,
  RAG querying, CLI and service operation, and evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepSearcher

Use this repo skill when a task mentions the DeepSearcher package, its `deepsearcher` console command, document loading, website crawling, retrieval-augmented querying, the HTTP service, or the evaluation workflow. The skill is split into focused sub-skills so future agents can jump straight to the right workflow without reopening the original checkout.

## Start here

| User intent | Read |
| --- | --- |
| Pick LLM, embedding, loader, crawler, or vector DB providers; diagnose missing SDKs or credentials | [sub-skills/provider-configuration/SKILL.md](sub-skills/provider-configuration/SKILL.md) |
| Load local files/directories or websites into a collection | [sub-skills/data-ingestion/SKILL.md](sub-skills/data-ingestion/SKILL.md) |
| Ask questions over loaded data, choose DeepSearch vs ChainOfRAG vs NaiveRAG, or inspect retrieved references | [sub-skills/rag-query/SKILL.md](sub-skills/rag-query/SKILL.md) |
| Use the `deepsearcher` CLI or the bundled FastAPI service helper | [sub-skills/cli-and-service/SKILL.md](sub-skills/cli-and-service/SKILL.md) |
| Validate or run the 2WikiMultiHopQA retrieval evaluation workflow | [sub-skills/evaluation/SKILL.md](sub-skills/evaluation/SKILL.md) |

## Package facts to keep in mind

- Distribution: `deepsearcher`.
- Version inspected for this skill: `0.0.2`.
- Import module: `deepsearcher`.
- Console script: `deepsearcher = deepsearcher.cli:main`.
- Python requirement from package metadata: `>=3.10`.
- The default configuration constructs providers during `init_config(config)`, so provider and vector DB readiness matter even before query/load workflows run.
- The inspected default config uses OpenAI, OpenAIEmbedding, PDFLoader, FireCrawlCrawler, and Milvus with a local `./milvus.db` URI.

## Install and sanity check

1. Install the package in an environment with Python 3.10+:

   ```bash
   pip install deepsearcher
   ```

2. For this checkout's inspected default local stack, also ensure a Milvus Lite-compatible set and a FireCrawl version that exports `ScrapeOptions`:

   ```bash
   pip install "pymilvus==2.5.8" "milvus-lite==2.5.1" "setuptools<81" "firecrawl-py==2.16.5"
   ```

   These pins were needed in the inspected environment to keep the default Milvus/FireCrawl paths usable.

3. Run the bundled environment check before deeper work:

   ```bash
   python scripts/check_deepsearcher_environment.py
   ```

   Add `--check-cli-help` if you want a temp-cwd CLI probe with a dummy OpenAI key.

4. If you only need to verify the installed package identity, the helper's version/import output is enough. If the installed package is missing optional provider SDKs, route to the provider sub-skill before assuming the repo skill is incomplete.

## How to route requests

- Configuration, provider names, credentials, and optional extras: `provider-configuration`.
- Loading files, crawling websites, chunking, and collection creation: `data-ingestion`.
- Querying loaded data and interpreting references: `rag-query`.
- CLI help, `deepsearcher load/query`, FastAPI endpoints, and deployment checks: `cli-and-service`.
- 2WikiMultiHopQA recall evaluation and report outputs: `evaluation`.

## Cross-cutting cautions

- `init_config(config)` creates every configured provider, not just the one you care about. A bad default provider can fail before the workflow begins.
- The default local Milvus URI is relative to the current working directory, so repeated runs in the same directory can lock `./milvus.db`.
- CLI help and service startup can expose provider initialization problems early; use the dedicated CLI/service sub-skill for those failure modes.
- Do not point future agents back to the original repository checkout. Read the bundled references and scripts in this skill tree instead.

## Skill metadata for future refreshes

- Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill still matches the current checkout.
- Use [references/repo-routing-metadata.json](references/repo-routing-metadata.json) as the structured router metadata consumed by the managed repo-skill importer.
- Read [references/installation-and-compatibility.md](references/installation-and-compatibility.md) and [references/troubleshooting.md](references/troubleshooting.md) when the default install or import path fails.
- Run [scripts/check_deepsearcher_environment.py](scripts/check_deepsearcher_environment.py) for a read-only environment sanity check before deeper routing.
