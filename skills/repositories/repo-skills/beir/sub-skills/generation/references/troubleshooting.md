# BEIR Generation Troubleshooting

Use this guide when synthetic queries, qrels, or expanded corpus files are missing, misnamed, too small, or difficult to load.

## Generated Query Count Assertion

Symptom:

```text
AssertionError
```

Likely cause: `QueryGenerator.generate(...)` expected `len(batch) * ques_per_passage` strings from `model.generate(...)`, or `generate_multi_process(...)` expected `len(corpus) * ques_per_passage` strings from `model.generate_multi_process(...)`.

Fix:

- Check the custom model protocol in `references/api-reference.md`.
- Return one string per requested sequence, not one list per document.
- For `ques_per_passage=3` and a batch of two documents, return six strings.
- Add a tiny fake-model test before using a real model wrapper.

The bundled helper intentionally validates this contract; adapt it to reproduce count failures without downloads.

## Duplicate Query De-Duplication

Symptom: the saved `gen-queries.jsonl` has fewer rows than `len(corpus) * ques_per_passage`, but no assertion failed.

Likely cause: BEIR asserts the raw model output count before de-duplication, then converts each passage's generated slice into a `set(q.strip() ...)`. Exact duplicates or whitespace-only differences for the same source passage collapse into one query.

Fix:

- Inspect raw model outputs for each passage.
- Increase diversity through the real model settings that BEIR exposes (`top_p`, `top_k`, `ques_per_passage`) or through model-specific adapter logic.
- Do not assume final qrel count equals the raw sequence count when duplicates are possible.

## Prefix and Path Surprises

Symptom: generated files exist, but `GenericDataLoader(data_folder=..., prefix="gen").load(split="train")` cannot load them or loads the wrong corpus.

Check the layout:

```text
dataset/gen-queries.jsonl
dataset/gen-qrels/train.tsv
dataset/corpus.jsonl
```

Prefix mode changes query and qrels paths only. It does not select `gen-corpus.jsonl`.

Fix:

- For generated queries, load with `prefix="gen"` and `split="train"`.
- For expanded passages, pass `corpus_file="gen-corpus.jsonl"` if that file should be the active corpus.
- If both generated queries and expanded corpus are used together, pass both `prefix="gen"` and the intended `corpus_file` explicitly.
- Route detailed schema validation to the data-loading sub-skill.

## Missing Output Files

Symptom: expected files such as `gen-queries.jsonl`, `gen-qrels/train.tsv`, or `gen-corpus.jsonl` are absent.

Fix:

- Confirm `output_dir` points to the dataset directory where you expect outputs.
- Confirm `prefix`; BEIR writes `<prefix>-queries.jsonl`, `<prefix>-qrels/train.tsv`, and `<prefix>-corpus.jsonl`.
- Confirm the generation method completed; BEIR writes final files after processing all batches.
- Check filesystem permissions for `output_dir`.
- For custom wrappers, fix exceptions thrown before final save.

## `save_after` Behavior

Symptom: periodic saves do not happen when expected, or output files appear to be repeatedly overwritten.

BEIR 2.2.0 periodically calls `save(...)` only when the accumulated query count is exactly divisible by `save_after` and at least `save_after`. Each save writes the full accumulated `queries` and `qrels` dictionaries, not just a shard. The final save always overwrites the same files at the end.

Fix:

- Use `save_after` as a durability checkpoint, not as a sharding mechanism.
- Avoid very small `save_after` values unless repeated full-file rewrites are acceptable.
- Do not rely on the `save=False` argument to suppress output in BEIR 2.2.0; the method still saves.

## Missing NLTK or Model Dependencies

Symptoms:

- `LookupError` for `stopwords`
- Transformers model/tokenizer download failures
- missing `torch`, `transformers`, or network/cache errors

Likely surfaces:

- `TILDE` needs NLTK English stopwords, `bert-base-uncased` tokenizer files, the TILDE model, PyTorch, and Transformers.
- `QGenModel` needs a sequence-to-sequence tokenizer/model from Hugging Face plus PyTorch and Transformers.

Fix:

- Use fake model objects for smoke tests and documentation examples that must run offline.
- For real generation, ensure model downloads are permitted or pre-populate the model cache.
- Install or download the NLTK stopwords corpus before constructing `TILDE` when required.
- Choose CPU/GPU `device` intentionally for large jobs.

## Large Model, GPU, and Network Constraints

Symptom: generation is slow, runs out of memory, or blocks on external services.

Fix:

- Start with a small corpus slice and low `ques_per_passage`.
- Reduce `batch_size` for GPU/CPU memory pressure.
- Confirm network and credentials if the model wrapper calls external APIs.
- Treat vLLM, LoRA, NVEmbed, LLM2Vec, PEFT, and other large-model workflows as optional backend work that may require extra packages, large downloads, and GPU-specific setup.
- Keep no-download tests separate from real-model experiments.

## Multi-Process Pool Shape

Symptoms:

- `KeyError: 'processes'`, `'input'`, or `'output'`
- worker startup failures
- hanging process at shutdown

Fix:

- For BEIR `QGenModel`, create the pool with `model.start_multi_process_pool()` and pass that exact dictionary to `QueryGenerator.generate_multi_process(...)`.
- For custom models, document and implement the pool shape expected by that model's `generate_multi_process(...)`.
- Put multi-process code inside `if __name__ == "__main__":`.
- Stop `QGenModel` pools with `model.stop_multi_process_pool(pool)` in `finally`.
- If CPU fallback starts too many workers for the environment, pass an explicit `target_devices` list.

## Passage Expansion Count Mismatch

Symptom: passage expansion writes fewer rows than expected or raises an index error.

Likely cause: the expansion model returned a list whose length does not match the input batch. `PassageExpansion.expand(...)` assumes `expansions[idx]` exists for every document in the batch.

Fix:

- Return exactly one expansion string per input document.
- Add assertions in custom model adapters before returning to BEIR.
- Use the bundled smoke helper to validate the expected `gen-corpus.jsonl` layout.

## Cross-Links

- Use data-loading for `GenericDataLoader` prefix semantics, custom `corpus_file`, and BEIR JSONL/TSV validation.
- Use training for consuming generated `train.tsv` qrels in a fine-tuning loop.
- Use retrieval-evaluation for evaluating generated or expanded datasets with BEIR metrics.
