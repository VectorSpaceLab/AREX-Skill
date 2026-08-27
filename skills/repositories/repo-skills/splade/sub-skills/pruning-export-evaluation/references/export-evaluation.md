# Export and Evaluation Reference

This reference covers SPLADE's Anserini export path and safe planning for BEIR and PISA evaluation. For core SPLADE train/index/retrieve commands, use `../../hydra-pipelines/SKILL.md`.

## Anserini Export Entry Point

SPLADE exports Anserini-readable sparse vectors with the Hydra module:

```bash
python -m splade.create_anserini \
  init_dict.model_type_or_dir=naver/splade-cocondenser-ensembledistil \
  config.pretrained_no_yamlconfig=true \
  config.index_dir=experiments/pre-trained/index \
  config.out_dir=experiments/pre-trained/out \
  +quantization_factor_document=100 \
  +quantization_factor_query=100
```

For checkpoint-backed runs, provide the checkpoint config through the SPLADE config environment or Hydra settings used by the core pipeline skill, then add the quantization overrides:

```bash
SPLADE_CONFIG_FULLPATH=/path/to/checkpoint/config.yaml \
python -m splade.create_anserini \
  +quantization_factor_document=100 \
  +quantization_factor_query=100
```

Do not run this command as a cheap smoke test: it loads a model, reads collections/queries, and may download Hugging Face weights unless the model is already cached. A safe native check is only `python -m splade.create_anserini --help`.

## Output Files

`EncodeAnserini` writes both files under `config.out_dir`:

| File | Producer mode | Format | Use |
| --- | --- | --- | --- |
| `docs_anserini.jsonl` | document | one JSON object per document with `id`, `content`, and `vector` | Anserini/Pyserini `JsonVectorCollection` indexing and static pruning |
| `queries_anserini.tsv` | query | `query_id<TAB>expanded token text` | Anserini/Pyserini search topics for impact indexes |

A document record has this shape:

```json
{"id": 0, "content": "document text", "vector": {"term": 12, "expanded": 4}}
```

The query TSV repeats each token according to its integer quantized weight, for example:

```text
0	term term expanded
```

## Quantization Semantics

`EncodeAnserini.index()` multiplies each nonzero SPLADE weight by `quantization_factor`, rounds with `numpy.rint`, casts to integer, and keeps only strictly positive integer weights. Typical examples use `+quantization_factor_document=100` and `+quantization_factor_query=100`.

For `matching_type=splade`, both document and query factors are read from Hydra overrides. For `matching_type=splade_doc`, the query factor is forced to `1` by `splade.create_anserini`.

Higher factors preserve more small weights before integer rounding but can produce larger impact values. Lower factors can collapse weak weights to zero and increase the chance of empty vectors.

## Empty Vector Fallback

If a document or query representation has no positive quantized tokens, SPLADE logs `empty input => <id>` and inserts tokenizer id `998` with weight `1`. In BERT-style vocabularies this is documented as the `[unused993]` fallback token. This prevents Anserini ingestion failures for empty vectors, but it is a fallback artifact, not meaningful model evidence.

## Anserini and Pyserini Planning

After export, external indexing/search is normally done outside SPLADE with Pyserini/Anserini:

```bash
python -m pyserini.index.lucene \
  --collection JsonVectorCollection \
  --input <directory-containing-docs-jsonl> \
  --index <anserini-index-dir> \
  --generator DefaultLuceneDocumentGenerator \
  --threads 12 \
  --impact --pretokenized

python -m pyserini.search.lucene \
  --index <anserini-index-dir> \
  --topics <queries_anserini.tsv> \
  --output <run.trec> \
  --output-format trec \
  --batch 100 --threads 16 \
  --hits 1000 \
  --impact
```

Treat these as plan templates unless the user confirms that Java, Pyserini, Lucene/Anserini dependencies, input data, output disk space, and runtime budget are available.

## BEIR Evaluation Planning

SPLADE includes `python -m splade.beir_eval`, which downloads a BEIR dataset zip with `beir.util.download_and_unzip()` using `+beir.dataset=<name>` and `+beir.dataset_path=<directory>`. It then indexes the BEIR corpus with SPLADE's internal sparse index, retrieves, removes same-id query/document hits, and writes metrics such as `NDCG@10`, `Recall@100`, and `R_cap@100`.

Safe planning command shape:

```bash
python -m splade.beir_eval \
  +beir.dataset=scifact \
  +beir.dataset_path=data/beir \
  config.index_retrieve_batch_size=100 \
  config.index_dir=experiments/beir/index \
  config.out_dir=experiments/beir/out
```

Do not run BEIR evaluation accidentally. It can trigger network downloads, model downloads, indexing, retrieval, and metric evaluation. Use `python -m splade.beir_eval --help` as the safe help-only check.

## PISA Evaluation Planning

The PISA notes are external-engine instructions, not a bundled SPLADE runtime. They require:

- a separate PISA checkout built with CMake and `make`;
- downloaded PISA index/query artifacts or locally produced equivalents;
- PISA binaries such as `evaluate_queries` and `queries`;
- `pyserini.eval.trec_eval` or another TREC metric evaluator for run scoring.

Plan PISA work as an environment-preparation task first. Confirm the index files, document map, WAND files, weighted query format, scorer choice such as `quantized`, target metrics, and CPU/parallelism settings before running external binaries.

## Benchmarking Notes

The benchmarking notes in this repository focus on experiment configurations and middle-trained models. They are useful for interpreting which trained checkpoint or config family produced an export, but the export/pruning/evaluation commands still need explicit local paths, downloaded data, and external evaluation dependencies.
