# SPLADE API and Data Troubleshooting

## `raw.tsv` Shape Errors

Symptoms:

- `ValueError: not enough values to unpack` or `too many values to unpack` in pair datasets.
- Empty datasets after loading.
- Query/document text appears truncated or misplaced.

Checks:

- Collection/query files must be `id<TAB>text` in a directory named by the caller, with the file itself named `raw.tsv` for classic loaders.
- Triplet training files must be exactly `query<TAB>positive<TAB>negative` per line.
- Distillation triplets must be exactly five fields: query, positive, negative, positive score, negative score.
- HF `DatasetPreLoad` and `TRIPLET_Dataset` take raw TSV file paths; classic `CollectionDatasetPreLoad` and `PairsDatasetPreLoad` take directories containing `raw.tsv`.

## `row_id` vs `content_id` Key Errors

Symptoms:

- `KeyError` when fetching a query or document id from qrels, run files, or score files.
- Retrieval output ids are row numbers instead of expected external ids.
- A qrel id exists in JSON but lookup still fails.

Cause:

- `row_id` stores data under integer row offsets and returns the original first-column id separately.
- `content_id` stores data under first-column ids from `raw.tsv`, normalized to strings during lookup.

Fixes:

- Use `content_id` for any dataset that is indexed by qrel/run/score ids.
- Use `row_id` for indexing when sequential integer rows are intended, and preserve original ids through `doc_ids.pkl` or the returned id mapping.
- Normalize qids and dids as strings in validation scripts before comparing files.
- Check for hidden whitespace in `raw.tsv` ids; strip ids before writing files.

## Qrel JSON Problems

Symptoms:

- No queries are retained by hard-negative datasets.
- `assert len(self.query_list) > 0` fails in HF `L2I_Dataset`.
- Positives are treated as negatives.

Checks:

- Qrels must be a JSON object mapping qid to `{did: relevance}`.
- Relevance values should be numeric and positive for positives; SPLADE HF code keeps values where `int(relevance) >= 1`.
- Qrel qids must overlap the score dictionary qids.
- Positive dids must exist in the document collection.

## Hard-Negative Score Format Problems

Symptoms:

- Positive document cannot be removed from candidate negatives.
- `KeyError` for an int-looking id.
- Not enough negatives for `n_negatives`.

Checks and fixes:

- Score JSON shape is `{qid: {did: score}}` with numeric scores.
- `pkl_dict` score files are gzip pickles containing the same nested dictionary, often with integer qids/dids.
- Convert ids to strings for portable validation, but remember `MsMarcoHardNegatives` may call `int(positive)` internally for candidate removal.
- Ensure each query has at least one candidate not listed as positive. More candidates than `n_negatives` is preferable.
- If a positive document is absent from the score file, HF training falls back to the maximum candidate score for that positive; this is expected but should be documented.

## TREC Run Parsing Issues

Symptoms:

- `ValueError` while reading reranking run files.
- Top-k filtering behaves strangely.

Checks:

- Each line should have six whitespace-separated fields: `qid Q0 did rank score tag`.
- `rank` should parse as an integer and `score` as a float.
- SPLADE readers split on spaces, so avoid embedded spaces inside ids.

## Special Token Cleaning Surprises

Symptoms:

- Bag-of-words query vectors include `[CLS]`, `[SEP]`, `[PAD]`, or `[MASK]`.
- Lexical masking leaves unexpected special-token dimensions.

Cause:

- `SpladeDoc` clears pad/CLS/SEP for classic query bow.
- `SpladeLexical` and HF `SpladeDoc` call `clean_bow` with pad/CLS/SEP/MASK ids.
- `clean_bow` uses truthiness checks such as `if pad_id:`; if a tokenizer assigns a special token id of `0`, that column is not cleared by this helper.

Fixes:

- Inspect tokenizer special token ids before relying on cleaned bow behavior.
- For custom tokenizers, explicitly clear id `0` in caller code if it is a special token.
- Verify sparse vector nonzero ids against `tokenizer.vocab` or `tokenizer.get_vocab()`.

## Model Download or Offline Failures

Symptoms:

- `OSError` or `EnvironmentError` from `from_pretrained`.
- A simple constructor unexpectedly tries to contact HuggingFace.
- API inspection is blocked by network restrictions.

Checks and fixes:

- Classic `Splade`, `SpladeDoc`, `SpladeTopK`, `SpladeLexical`, HF `SPLADE`, and `DPR` constructors load HF model weights immediately.
- Use `inspect.signature` on classes instead of instantiating them when only API shape is needed.
- Pass a local model/checkpoint directory when offline.
- Set the appropriate HuggingFace offline/cache environment externally when required by the runtime environment.
- Use `inspect_splade_api.py` for no-download signature checks.

## Empty Sparse Vectors

Symptoms:

- Exported Anserini vectors are empty.
- Retrieval returns no documents above threshold.
- Expanded terms list is empty.

Checks and fixes:

- Ensure the model is in `eval()` for deterministic inspection and use `torch.no_grad()`.
- Verify input text is not empty after stripping.
- Confirm tokenizer/model vocabulary match the checkpoint.
- Check top-k settings: `top_d` or `top_q` can prune all useful dimensions if too small or if activations are zero.
- `EncodeAnserini` fills empty document vectors with a fallback unused token for export, but that is an export workaround, not a model-quality fix.
- Lower retrieval threshold only for diagnosis; route retrieval execution to `hydra-pipelines`.

## Optional Dependency Failures

Symptoms:

- `ModuleNotFoundError: pytrec_eval` when importing retrieval/evaluation modules.
- `warning: could not load pygaggle` in reranking dataset imports.

Guidance:

- API/data inspection does not require evaluation-only dependencies.
- Avoid importing top-level command modules when only inspecting model/data classes.
- Route evaluation and reranking execution setup to the relevant command sub-skills.

## Hydra/OmegaConf Version Warnings During API Work

Symptoms:

- Warnings about Hydra `version_base` or defaults list `_self_`.
- `omegaconf` version mismatch warnings from package checks.

Guidance:

- These warnings affect command execution and config composition more than static API inspection.
- For command construction and Hydra overrides, route to `hydra-pipelines`.
- For HF training/reranking configs, route to `hf-training-reranking`.
