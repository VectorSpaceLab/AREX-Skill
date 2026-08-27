# Encoding and Retrieval Troubleshooting

## `ModuleNotFoundError: No module named 'faiss'`

FAISS is optional in a minimal Tevatron environment but required for `tevatron.retriever.driver.search` and the Tevatron searcher API. Install a suitable FAISS build before retrieval.

For CPU-only validation, `faiss-cpu` is enough. GPU search requires a GPU-enabled FAISS build compatible with CUDA.

Quick probe:

```bash
python - <<'PY'
import faiss
print('faiss version:', getattr(faiss, '__version__', 'unknown'))
print('gpus:', faiss.get_num_gpus())
PY
```

The bundled `scripts/tiny_faiss_search_smoke.py` skips with guidance by default when FAISS is unavailable; use its `--strict` flag if CI should fail instead.

## Passage Glob Matches No Files

The search CLI resolves `--passage_reps` with `glob.glob()` and then loads the first match. If the pattern matches nothing, the failure can appear as `IndexError: list index out of range`.

Preflight the pattern:

```bash
python - <<'PY'
import glob
matches = sorted(glob.glob('embeddings/corpus.*.pkl'))
print(len(matches), matches[:5])
assert matches, 'no passage embedding shards matched'
PY
```

Quote wildcard patterns in shell commands so Tevatron receives the intended pattern: `--passage_reps 'embeddings/corpus.*.pkl'`.

## Query and Passage Dimension Mismatch

FAISS `IndexFlatIP` requires query vectors and passage vectors to have the same embedding dimension. Mismatches usually come from mixing models, checkpoints, pooling modes, LoRA adapters, or custom embedding writers.

Probe shapes:

```bash
python - <<'PY'
import pickle
for path in ['embeddings/query.pkl', 'embeddings/corpus.00.pkl']:
    with open(path, 'rb') as handle:
        reps, ids = pickle.load(handle)
    print(path, getattr(reps, 'shape', None), len(ids))
PY
```

Regenerate query or corpus embeddings with matching `--model_name_or_path`, `--tokenizer_name`, `--pooling`, `--normalize`, LoRA, prefixes, padding, EOS-token, and dtype choices.

## Pickle vs Text Ranking Confusion

Encoding outputs are pickle files. Search outputs are text only when `--save_text` is set.

- Use pickle probes for `query.pkl` and `corpus.*.pkl`.
- Use text/TREC/MARCO tools only for rankings written with `--save_text`.
- If a ranking file starts with binary bytes or cannot be opened as text, rerun search with `--save_text`.

## `--batch_size -1` Runs Out of Memory

`--batch_size -1` searches all queries in one FAISS call. This can be fast but also materializes result arrays for every query at the requested depth.

Mitigations:

- Use a positive `--batch_size`, such as `64` or `128`.
- Lower `--depth` for diagnostic runs.
- Search passage shards separately and merge text outputs with `scripts/reduce_results.py`.
- Prefer CPU FAISS for tiny correctness checks when GPU memory is scarce.

## GPU FAISS Is Not Used

Tevatron logs CPU fallback when `faiss.get_num_gpus()` returns `0`. This is expected with `faiss-cpu`, without visible GPUs, or with incompatible CUDA/FAISS libraries.

Confirm the FAISS build before debugging model code. CPU search is still correct for small runs; switch to GPU only when the installed FAISS package and CUDA runtime are known to match.

## vLLM Dependency or Model Support Gaps

`tevatron.retriever.driver.vllm_encode` is optional. Failures may mention missing `vllm`, unsupported embedding task, LoRA rank issues, missing remote model code, unsupported dtype, CUDA/runtime incompatibility, or insufficient memory.

Fallbacks:

- Use `tevatron.retriever.driver.encode` for standard text encoding.
- Keep `--per_device_eval_batch_size` small while validating vLLM model support.
- Remove vLLM-specific assumptions from minimal validation and smoke tests.
- For multimodal variants, verify processor loading and assets in the multimodal/LLM sub-skill before full encoding.

## `torch` or Model Imports Are Missing During Encoding

The base package can import argument dataclasses without importing all workflow dependencies, but encoding needs `torch`, `transformers`, model code, and tokenizer/model artifacts. Install the smallest backend stack needed for the chosen model and avoid using search-only smoke tests as proof that model encoding can run.

## IDs or Text Fields Are Missing

The encoder expects `query_id` plus `query_text` or `query` for queries, and `docid` plus `text` for passages. It prepends `title` to passage `text` when present. If custom JSONL uses names such as `document_text` or `document_id`, transform it with the data-preparation sibling sub-skill before encoding.

## Scores Look Random or Too Low

Common causes:

- Query and corpus were encoded with different checkpoints, LoRA adapters, prefixes, pooling, normalization, or `--append_eos_token` settings.
- `--encode_is_query` was omitted for queries or accidentally used for corpus encoding.
- Passage IDs are duplicated in the corpus, making rankings and reductions ambiguous.
- Evaluation conversion used the wrong benchmark IDs or qrels.

Start with a tiny two-query/two-document fixture where expected matches are obvious, then scale up.

## Reducer Input Has Bad Lines or Duplicates

The bundled reducer expects whitespace-separated `qid pid score` rows. It validates the number of columns and score parsing, sorts by descending score, and preserves duplicate document IDs for a query if multiple shard files contain them. Remove duplicate documents upstream if each query should have unique passage IDs.
