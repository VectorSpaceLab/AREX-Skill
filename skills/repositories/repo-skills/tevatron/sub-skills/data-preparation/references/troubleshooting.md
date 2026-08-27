# Data Preparation Troubleshooting

## Malformed JSONL

Symptoms:

- `datasets` fails while reading a local `json` dataset.
- The validator reports `invalid JSON` with a line number.
- Only the first row appears to load because the file is a pretty-printed JSON array.

Fixes:

- Keep exactly one complete JSON object per line.
- Remove trailing commas and comments; JSONL is not Python syntax.
- Ensure the file is UTF-8 text, not multi-line pretty JSON.
- Run `python scripts/validate_tevatron_jsonl.py --kind <kind> --input <file>` before training or encoding.

## Missing IDs or Text Fields

Symptoms:

- Key errors for `query_id`, `docid`, `positive_document_ids`, or `negative_document_ids`.
- Encoded output has empty passage/query text unexpectedly.
- Reranker preparation cannot join rankings to corpus or queries.

Fixes:

- For new retriever training, include `query_id`, `positive_document_ids`, and `negative_document_ids`; provide `query_text` unless the query is intentionally textless multimodal input.
- For ID-list data, include a separate corpus with every referenced `docid` and pass it with `--corpus_name json --corpus_path <corpus.jsonl>`.
- For corpus/encoding rows, include `docid`; include `text` or a valid modality field.
- For legacy training and reranker training, include `query`, `positive_passages`, and `negative_passages`; each passage should include `text` and preferably `docid`.
- Keep ID values as strings consistently across train, corpus, qrels, rankings, and rerank input.

## ID-List Data Missing Corpus Pairing

Symptoms:

- New-format training rows validate individually but training fails when resolving selected positives/negatives.
- Errors mention missing docids, key lookup failures, or an empty corpus map.
- The user passed `positive_document_ids`/`negative_document_ids` without `--corpus_name` and `--corpus_path`.

Fixes:

- Prepare a corpus JSONL with `docid`, optional `title`, `text`, and optional media fields.
- Use local corpus flags with local train files: `--corpus_name json --corpus_path corpus.jsonl`.
- Validate train and corpus together: `python scripts/validate_tevatron_jsonl.py --kind train-new --input train.jsonl --corpus corpus.jsonl`.
- If the data intentionally embeds full passage text, switch to the legacy `positive_passages`/`negative_passages` shape instead of ID lists.

## Local JSON vs Hugging Face Dataset Confusion

Symptoms:

- A local path is interpreted as a dataset name.
- A hosted dataset ignores a local file.
- The split name is missing or not found.
- A dataset config such as a BRIGHT task is omitted.

Fixes:

- For local files, use `--dataset_name json --dataset_path file.jsonl`.
- For local corpus-ID training, add `--corpus_name json --corpus_path corpus.jsonl`.
- For hosted datasets, use `--dataset_name namespace/name`, optional `--dataset_config`, and the split actually published by that dataset.
- Remember the default split is `train`; pass `--dataset_split dev`, `test`, or the dataset-specific split when encoding queries or evaluating.

## Qrels and Ranking Delimiter Mismatch

Symptoms:

- Ranking conversion fails with an unexpected column count.
- Evaluation reports zero recall even though IDs appear present.
- Hard-negative mining reads the wrong token as a docid or score.
- A four-column qrels file is accidentally treated as a four-column ranking file.

Fixes:

- Use whitespace-delimited `qid docid score` for Tevatron search output and hard-negative mining.
- Use six-column TREC run format `qid Q0 docid rank score tag` for `trec_eval` runs.
- Use four-column qrels `qid 0 docid relevance` for `trec_eval` labels.
- Use three-column tab-separated `qid docid rank` only for MS MARCO-style submission/evaluation tools.
- Do not add headers to ranking or qrels files unless the downstream tool explicitly supports them.
- Validate rankings and qrels separately: `--kind ranking` for run files and `--kind qrels` for labels.

## Interleaved Ranking Blocks

Symptoms:

- Converted ranks restart unexpectedly.
- A repeated query ID appears in more than one block.
- Evaluation order differs from the first-stage search output.

Fixes:

- Sort/group ranking rows by query before conversion while preserving each query's desired score order.
- Do not merge shard outputs with plain concatenation if that interleaves partial results for the same query; route shard merging to `../encoding-retrieval/`.
- Use the validator warning about non-contiguous queries as a signal to regroup before `convert_result_to_trec.py` or `convert_result_to_marco.py`.

## Hard-Negative Count or Depth Mismatch

Symptoms:

- Training repeatedly samples the same negative passages.
- Mining output drops many queries after filtering.
- `train_group_size` is larger than available positives/negatives.
- A ranking depth of `k` produces fewer than `k` usable negatives after removing positives.

Fixes:

- Generate rankings at a depth comfortably larger than `train_group_size - 1` because positives, duplicates, and invalid docids may be removed.
- For default `train_group_size=8`, target at least seven usable negatives per query after filtering.
- Increase mining depth or lower `min_hn` only after checking that query IDs and docids match between rankings and corpus.
- Remove known positives from negative lists; exact-match QA mining should also remove candidates containing answer spans.
- Validate with `--train-group-size <n>` so warnings match the intended training command.

## Image, Audio, or Video Fields Without Assets

Symptoms:

- Encoding warns that video/audio files do not exist.
- Multimodal rows load but model input is missing media.
- Text-only experiments unexpectedly try to process media fields.
- A schema-valid image-only corpus fails later when assets are not available to the processor.

Fixes:

- Keep media paths relative to the configured assets root and verify them with `--assets-root` before execution.
- Disable unused modalities with the relevant encode flags when running text-only data.
- For audio, use either an object containing an `array` key or a `.mp3` path.
- For image-only corpora, allow `text` to be null or empty only if the target multimodal model path supports image encoding; route model/backend details to `../multimodal-llm/`.

## Rerank Input Join Failures

Symptoms:

- Rerank JSONL has fewer rows than the ranking depth suggests.
- Query or document fields are blank.
- Reranker inference raises key errors for `query`, `title`, or `text`.
- Rankings use IDs that do not match the casing/string form in query or corpus data.

Fixes:

- Normalize query rows to include `query_id` and `query` before preparing rerank input.
- Normalize corpus rows to include `docid`, `title`, and `text`; use an empty string for missing titles.
- Check that ranking `qid` and `docid` values match the exact string forms in query/corpus JSONL.
- Validate with `python scripts/validate_tevatron_jsonl.py --kind rerank --input rerank.jsonl` before model scoring.

## Conversion Script Errors

Symptoms:

- `conversion error` reports a column-count mismatch.
- Score parsing fails.
- A qrels file was passed to a ranking converter.

Fixes:

- Pass only ranking/run files to `convert_result_to_trec.py` and `convert_result_to_marco.py`.
- Use `qid docid score`, `qid docid rank score`, or `qid Q0 docid rank score tag` rows.
- Keep qrels as labels and never convert them as retrieval output.
- Check the file first with `python scripts/validate_tevatron_jsonl.py --kind ranking --input rank.tsv`.
