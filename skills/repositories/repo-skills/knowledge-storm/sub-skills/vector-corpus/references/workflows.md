# Vector corpus workflows

This reference is for STORM runs grounded on a CSV/local corpus with `VectorRM` and Qdrant. Use the sibling sub-skill for Internet-search retrievers; use the Co-STORM sub-skill for collaborative discourse.

Commands below assume the current directory is this `vector-corpus` sub-skill directory. If running elsewhere, replace `scripts/...` with the path to the bundled script.

## Prerequisites

Install the public package in the environment that will run STORM:

```bash
python -m pip install knowledge-storm
```

If corpus conversion or vector-store creation reports a missing dataframe dependency, add:

```bash
python -m pip install pandas
```

For full STORM generation, configure LiteLLM provider credentials for the models you choose, for example:

```bash
export OPENAI_API_KEY="..."
```

For online Qdrant mode, also configure either `QDRANT_API_KEY` or pass a Qdrant API key to the helper:

```bash
export QDRANT_API_KEY="..."
```

## 1. Validate a user corpus

A `VectorRM` corpus is a single CSV file. `content` and `url` are required; `title` and `description` are optional. `url` is used as the document identifier and should be unique.

```bash
python scripts/validate_vector_corpus_csv.py \
  --input-path corpus.csv \
  --strict-unique-url
```

Use the non-strict form for a quick schema check that reports duplicate URLs as warnings:

```bash
python scripts/validate_vector_corpus_csv.py --input-path corpus.csv
```

Fix all missing `content` or `url` values before indexing. Duplicate URLs may cause citation/source ambiguity in STORM outputs, so use `--strict-unique-url` before creating a collection.

## 2. Convert the Kaggle arXiv abstracts dataset

If starting from Kaggle `arxiv_data_210930-054931.csv`, convert it to the `VectorRM` schema:

```bash
python scripts/process_kaggle_arxiv_abstract_dataset.py \
  --input-path arxiv_data_210930-054931.csv \
  --output-path arxiv_vector_rm.csv
```

The default conversion filters rows whose `terms` column equals `['cs.CV']`, maps `abstracts` to `content`, maps `titles` to `title`, creates synthetic unique `url` values, and writes an empty `description` column. Use `--no-filter` or `--filter-term` to change the downsample behavior.

Validate the generated CSV before indexing:

```bash
python scripts/validate_vector_corpus_csv.py \
  --input-path arxiv_vector_rm.csv \
  --strict-unique-url
```

## 3. Plan without embedding or network calls

Before doing expensive work, dry-run the STORM helper. Dry-run validates CLI arguments and CSV schema, reports the vector-store plan, and avoids embeddings, Qdrant calls, LLM calls, and network access.

Offline plan:

```bash
python scripts/run_storm_wiki_with_vector_rm.py \
  --topic "Neural radiance fields" \
  --output-dir ./results/vector_rm \
  --vector-db-mode offline \
  --offline-vector-db-dir ./vector_store \
  --csv-file-path corpus.csv \
  --collection-name my_documents \
  --device cpu \
  --dry-run
```

Online plan:

```bash
python scripts/run_storm_wiki_with_vector_rm.py \
  --topic "Neural radiance fields" \
  --output-dir ./results/vector_rm \
  --vector-db-mode online \
  --online-vector-db-url "https://YOUR-QDRANT-ENDPOINT" \
  --csv-file-path corpus.csv \
  --collection-name my_documents \
  --device cpu \
  --dry-run
```

Use `--validate-only` when you want configuration/schema validation and an exit code but no full run:

```bash
python scripts/run_storm_wiki_with_vector_rm.py \
  --vector-db-mode offline \
  --offline-vector-db-dir ./vector_store \
  --csv-file-path corpus.csv \
  --collection-name my_documents \
  --validate-only
```

## 4. Create or update a local Qdrant vector store

Provide `--csv-file-path` to create/update the collection from CSV rows. The manager splits each row into chunks with `--chunk-size` and `--chunk-overlap`, embeds chunks in batches with `--embed-batch-size`, and adds chunks to the selected Qdrant collection.

```bash
python scripts/run_storm_wiki_with_vector_rm.py \
  --topic "Neural radiance fields" \
  --output-dir ./results/vector_rm \
  --vector-db-mode offline \
  --offline-vector-db-dir ./vector_store \
  --csv-file-path corpus.csv \
  --collection-name my_documents \
  --embedding-model BAAI/bge-m3 \
  --device cpu \
  --chunk-size 500 \
  --chunk-overlap 100 \
  --embed-batch-size 64 \
  --do-research \
  --do-generate-outline \
  --do-generate-article \
  --do-polish-article
```

Notes:

- Use `cpu` first; it is functionally sufficient. `cuda` and `mps` only accelerate local embedding model execution when available.
- Re-running with the same collection appends/updates through Qdrant rather than deleting old chunks. Use a new collection name when you need a clean index.
- If `--csv-file-path` is omitted, the helper expects an existing collection at `--offline-vector-db-dir`.

## 5. Create or update an online Qdrant vector store

Online mode requires a Qdrant URL and API key. The helper reads `QDRANT_API_KEY` by default; use `--qdrant-api-key` only when you deliberately want to pass it on the command line.

```bash
export QDRANT_API_KEY="..."
python scripts/run_storm_wiki_with_vector_rm.py \
  --topic "Neural radiance fields" \
  --output-dir ./results/vector_rm \
  --vector-db-mode online \
  --online-vector-db-url "https://YOUR-QDRANT-ENDPOINT" \
  --csv-file-path corpus.csv \
  --collection-name my_documents \
  --embedding-model BAAI/bge-m3 \
  --device cpu \
  --do-research \
  --do-generate-outline \
  --do-generate-article
```

If you omit `--csv-file-path`, the online collection must already exist. `VectorRM` loads existing collections; it does not create missing collections by itself.

## 6. Reuse an existing vector store

Once the Qdrant collection exists, you can omit `--csv-file-path` and load the existing collection:

```bash
python scripts/run_storm_wiki_with_vector_rm.py \
  --topic "Neural radiance fields" \
  --output-dir ./results/vector_rm \
  --vector-db-mode offline \
  --offline-vector-db-dir ./vector_store \
  --collection-name my_documents \
  --embedding-model BAAI/bge-m3 \
  --device cpu \
  --do-research \
  --do-generate-outline
```

The `--collection-name` and `--embedding-model` should match the collection that was created. Mismatches usually surface as missing collection errors, empty retrieval, or embedding dimension/Qdrant client errors.

## 7. Direct API integration with STORMWikiRunner

After the vector store exists, the retrieval manager plugs into STORM exactly where an Internet search retriever would normally go:

```python
from knowledge_storm import STORMWikiRunner, STORMWikiRunnerArguments, STORMWikiLMConfigs
from knowledge_storm.lm import LitellmModel
from knowledge_storm.rm import VectorRM

lm_configs = STORMWikiLMConfigs()
lm_configs.set_conv_simulator_lm(LitellmModel(model="openai/gpt-4o-mini", max_tokens=500, temperature=1.0, top_p=0.9))
lm_configs.set_question_asker_lm(LitellmModel(model="openai/gpt-4o-mini", max_tokens=500, temperature=1.0, top_p=0.9))
lm_configs.set_outline_gen_lm(LitellmModel(model="openai/gpt-4o", max_tokens=400, temperature=1.0, top_p=0.9))
lm_configs.set_article_gen_lm(LitellmModel(model="openai/gpt-4o", max_tokens=700, temperature=1.0, top_p=0.9))
lm_configs.set_article_polish_lm(LitellmModel(model="openai/gpt-4o", max_tokens=4000, temperature=1.0, top_p=0.9))

args = STORMWikiRunnerArguments(
    output_dir="./results/vector_rm",
    max_conv_turn=3,
    max_perspective=3,
    search_top_k=3,
    retrieve_top_k=3,
    max_thread_num=3,
)

rm = VectorRM(
    collection_name="my_documents",
    embedding_model="BAAI/bge-m3",
    device="cpu",
    k=args.search_top_k,
)
rm.init_offline_vector_db(vector_store_path="./vector_store")

runner = STORMWikiRunner(args, lm_configs, rm)
runner.run(
    topic="Neural radiance fields",
    do_research=True,
    do_generate_outline=True,
    do_generate_article=True,
    do_polish_article=True,
)
runner.post_run()
runner.summary()
```

Switch `rm.init_offline_vector_db(...)` to `rm.init_online_vector_db(url="https://...", api_key=None)` for online Qdrant; `api_key=None` makes `VectorRM` read `QDRANT_API_KEY` from the environment.
