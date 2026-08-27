---
name: evaluation
description: "Plan, validate, and safely run DeepSearcher retrieval evaluations,
  especially 2WikiMultiHopQA recall workflows, with explicit cost, resume, and
  corpus-loading controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation

Use this sub-skill for retrieval-quality evaluation with DeepSearcher. The supported benchmark workflow is **2WikiMultiHopQA**, comparing DeepSearcher retrieval with the naive RAG baseline using Recall@2 and Recall@5.

## Route here

- Validate a 2Wiki-style corpus/questions pair before spending embedding or LLM tokens.
- Plan a benchmark run with `dataset`, `config_yaml`, `pre_num`, `max_iter`, `output_dir`, `skip_load`, and `flag`.
- Interpret `details.csv`, `statistics.json`, retrieved-title metadata, recall@K, token usage, and resumable partial output.
- Resume an interrupted run without reloading a compatible, already-populated vector collection.

## Route elsewhere

- Provider names, credentials, YAML provider dictionaries, optional SDKs, or version selection: use `../provider-configuration/SKILL.md`.
- General local/website indexing, collection naming, chunking, or loader behavior: use `../data-ingestion/SKILL.md`.
- `query`, `retrieve`, `naive_retrieve`, RAG agent selection, or iteration behavior outside the benchmark: use `../rag-query/SKILL.md`.
- The `deepsearcher` console command or HTTP service: use `../cli-and-service/SKILL.md`.

## Start safely

1. Run the no-network validator before initialization or indexing. It checks the dataset name, both JSON shapes, required YAML feature sections, and the output path without importing DeepSearcher or invoking providers:

   ```bash
   python scripts/check_evaluation_inputs.py \
     --dataset 2wikimultihopqa \
     --corpus path/to/2wikimultihopqa_corpus.json \
     --questions path/to/2wikimultihopqa.json \
     --config-yaml path/to/eval_config.yaml \
     --output-dir path/to/eval-output
   ```

   Add `--create-output-dir` only when it is safe to create the planned output directories. See [data formats](references/data-formats.md) for custom-fixture requirements.

2. Confirm that `config_yaml` contains all five `provide_settings` feature sections and that the file loader can read the corpus (`JsonFileLoader` with `text_key: text` for the standard corpus). Check provider credentials and vector DB readiness separately; the validator intentionally does not test them.

3. Budget the run before launching it. A full run initializes an LLM, embedding model, loader/crawler providers, and vector DB, embeds the corpus on the first load, and invokes the retrieval pipeline for each evaluated question. More samples improve stability; higher `max_iter` generally increases token use and elapsed time. Use a small positive `pre_num` first, record the provider/model and configuration, and expand only after the smoke run succeeds.

4. Invoke the available evaluation runner using its public argument contract. The source-independent command shape is:

   ```bash
   python path/to/evaluation_runner.py \
     --dataset 2wikimultihopqa \
     --config_yaml path/to/eval_config.yaml \
     --pre_num 5 \
     --max_iter 3 \
     --output_dir path/to/eval-output \
     --flag result
   ```

   The full workflow is optional and credentialed/expensive. Do not treat a validator pass as proof that providers, embeddings, Milvus, or the benchmark runner are operational.

5. On the first run, allow corpus loading into a fresh or intentionally replaced collection. The benchmark loader uses the pre-chunked corpus as one large chunk per record (`chunk_size=999999`, `chunk_overlap=0`) and replaces the target collection in its normal first-run path. Treat that replacement as destructive; isolate the evaluation collection or vector DB from useful data.

6. After a successful load, resume or run another sample range with `--skip_load` only when the same compatible collection is still available: same vector DB endpoint/URI, collection, embedding dimension/model, and corpus. `skip_load` skips indexing; it does not verify that the collection exists or matches the files. Do not use it after changing embeddings, vector DB, collection, corpus, or an isolated working directory.

7. Use a distinct `flag` for logically separate reports. Results are written below `output_dir/<flag>/`; a flag separates report files, not vector collections. Avoid concurrent runs against the same local Milvus Lite database because the cwd-relative database can lock.

## Outputs and handoff

A completed or partial run writes:

- `details.csv`: one row per processed question, including the index, question, DeepSearcher and naive-RAG recall dictionaries, gold titles, and retrieved titles.
- `statistics.json`: aggregate Recall@2/Recall@5 for both systems, DeepSearcher token usage, error count, sample count, and token usage per sample.

The runner resumes from the number of existing CSV rows and combines saved statistics with newly processed rows. Preserve `details.csv` and `statistics.json` as a pair; back them up before manual edits. Inspect both files and record the dataset/config/model, `pre_num`, `max_iter`, `flag`, whether loading was skipped, and any pipeline errors when reporting results.

## References and helper

- [Evaluation workflow](references/evaluation-workflow.md) — parameter meanings, safe phases, resume procedure, and output lifecycle.
- [Data formats](references/data-formats.md) — accepted JSON/YAML contracts and Recall@K calculation.
- [Troubleshooting](references/troubleshooting.md) — validation, compatibility, cost, vector DB, and resume failures.
- `scripts/check_evaluation_inputs.py` — deterministic, no-network input checker with `--help` and optional output-directory creation.
