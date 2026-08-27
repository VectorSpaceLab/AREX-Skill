# Export, Pruning, and Evaluation Troubleshooting

Use this reference to classify failures before running external engines or downloads.

## Anserini Export Files Are Missing

Expected files after `python -m splade.create_anserini` are:

- `docs_anserini.jsonl` under `config.out_dir` for document vectors;
- `queries_anserini.tsv` under `config.out_dir` for query expansions.

If they are missing, check that the command actually completed, that `config.out_dir` is overridden to the expected directory, and that model/data loading did not fail earlier. Route Hydra config resolution issues to `../../hydra-pipelines/SKILL.md`.

## Wrong or Surprising Impact Values

SPLADE export multiplies floating weights by the quantization factor, rounds to integer, and keeps only positive values. If values are too large or too sparse:

- confirm `+quantization_factor_document` and `+quantization_factor_query`;
- remember that `matching_type=splade_doc` forces the query quantization factor to `1`;
- distinguish export quantization from later pruning thresholds;
- inspect a tiny sample before indexing externally.

For value pruning, the bundled `prune_doc_index.py` defaults to `threshold = --value-to-prune * 100`, matching the original pruning script. Use `--value-scale 1` when you want direct integer thresholds.

## Empty Vectors and Fallback Token

When a representation has no positive quantized terms, SPLADE inserts tokenizer id `998` with weight `1`; this is documented in source comments as `[unused993]`. This prevents empty Anserini vectors but can surprise downstream inspection. If many records contain only the fallback token, investigate model checkpoint, tokenizer, input text quality, and quantization factor.

## Pruning Input Layout Problems

The bundled pruning scripts expect explicit `--input-dir` and `--output-dir` paths. Input files must be plain `.jsonl` or `.jsonl.gz` and contain one JSON object per line with a `vector` object.

Common fixes:

- point `--input-dir` at the directory containing JSONL files, not at a parent experiment directory;
- use `--include '*.jsonl' --include '*.jsonl.gz'` defaults unless filenames differ;
- use `--dry-run --limit 2` to validate paths and record shape;
- check whether an output directory already exists before overwriting;
- preserve gzip by keeping input filenames ending in `.gz`.

## Quantile Pruning Keeps Too Much or Too Little

Quantile pruning computes one threshold per token over observed values and keeps values strictly greater than the threshold. If results look surprising:

- verify `--quantile` is between `0` and `1`;
- remember that missing token occurrences do not add zeroes to the token's distribution;
- use a tiny fixture to inspect per-token thresholds with `--print-thresholds`;
- expect all occurrences of a token with identical values to be pruned for high quantiles because the comparison is strict `>`.

## `pytrec_eval` or `trec_eval` Build Fails

SPLADE's retrieval/evaluation imports `pytrec_eval` through metric utilities. Inspection evidence showed retrieval/reranking imports fail when `pytrec_eval` is absent, and `pytrec_eval`/`trec_eval` builds can fail when source fetches or compilers are unavailable.

Options:

- install `pytrec_eval` only in an environment where native builds and network/source access are allowed;
- use Pyserini's `python -m pyserini.eval.trec_eval` if Pyserini and Java are already prepared;
- produce TREC run files first and evaluate in a separate metrics environment;
- do not block export/pruning work on metric packages unless the user asked for final effectiveness metrics.

## BEIR Downloads Unexpectedly Start

`python -m splade.beir_eval` calls `beir.util.download_and_unzip()` for the selected dataset and `+beir.dataset_path`. It can download data and then run indexing/retrieval. To avoid accidental network use:

- use `python -m splade.beir_eval --help` for help-only checks;
- ask for approval before running real BEIR commands;
- set `+beir.dataset_path` to a planned cache/data directory;
- confirm the dataset name, split expectations, disk space, and model cache state.

## Pyserini, Java, and Anserini Failures

Pyserini/Anserini indexing and search are external to SPLADE. Common prerequisites include a compatible Java runtime, Pyserini installation, Lucene/Anserini dependencies, enough disk for indexes, and correctly formatted `docs_anserini.jsonl`/`queries_anserini.tsv` files.

Symptoms and likely causes:

- `java` not found or class version errors: Java runtime mismatch;
- `JsonVectorCollection` errors: wrong input directory or malformed JSONL;
- empty search results: queries TSV path, tokenization/export, index path, or impact/pretokenized flags mismatch;
- metric command missing: Pyserini eval module or qrels are unavailable.

## PISA External Artifact Failures

PISA evaluation requires a separately built PISA engine and external artifacts such as `.docmap`, `.idx`, `.bmw`, and weighted query files. Failures usually mean one of these artifacts is missing or was produced with incompatible encoding/scorer assumptions.

Before running PISA commands, confirm:

- PISA was built successfully with the intended branch/version;
- index, WAND, docmap, and weighted query files belong to the same level/size/model variant;
- scorer settings such as `--scorer quantized --weighted` match the exported artifacts;
- metric evaluation is available after the TREC run is produced.

## Large Workflow Safety

If the user asks to reproduce pruning, BEIR, Anserini, or PISA numbers, separate the workflow into phases:

1. local export or input validation;
2. local pruning on a small sample;
3. external engine environment check;
4. full indexing/retrieval only after explicit approval;
5. metric evaluation and result comparison.

Record skipped downloads or external-engine steps clearly rather than silently running them.
