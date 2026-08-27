# Dense Encoding Troubleshooting

Use this reference when dense encoding, Faiss search, Lucene dense search, or hybrid retrieval fails.

## `ModuleNotFoundError: No module named 'faiss'`

Likely cause: the base Pyserini install is present but optional Faiss dependencies are missing.

Recovery:

1. Confirm the workflow really needs Faiss. Lucene sparse search does not.
2. For CPU dense workflows, install a CPU Faiss package compatible with the user's Python/platform.
3. For GPU Faiss, install a GPU-capable Faiss package and verify CUDA compatibility; `faiss-cpu` cannot run `--faiss-device cuda:0`.
4. Re-run `python -m pyserini.search.faiss --help` or a small import check only after the optional dependency is installed.

Route broad package installation decisions to `../../install-and-runtime/SKILL.md`.

## Torch CPU/CUDA Mismatch

Symptoms:

- `Torch not compiled with CUDA enabled`.
- `CUDA driver version is insufficient`.
- command hangs or fails after model initialization on a GPU device.

Recovery:

- Use `--device cpu` and omit `--fp16` for CPU-only workflows.
- Use `--device cuda:0` only when Torch reports CUDA availability.
- Keep `--device` and `--faiss-device` separate: encoder inference may run on Torch while Faiss search may still run on CPU.
- If the user wants GPU Faiss search or index construction, verify a GPU Faiss build separately from Torch.

## Model Downloads or Cache Misses

Symptoms:

- Hugging Face download prompts or network errors.
- missing tokenizer/model files for a local path.
- authentication failures for private models.

Recovery:

- Ask whether model downloads are allowed before running a model command.
- Prefer `--encoded-queries` for search-only workflows when matching encoded queries already exist.
- Use local model paths when the user provides them.
- Set model-specific `--encoder-class`, `--pooling`, `--l2-norm`, and `--prefix` to avoid accidental class inference changes.

## OpenAI Credential or Privacy Failures

Symptoms:

- missing `OPENAI_API_KEY` or organization/key errors;
- rate-limit errors;
- user corpus cannot be sent to external APIs.

Recovery:

- Do not run OpenAI embedding commands without explicit user approval for network/API usage.
- Confirm credentials are present in the runtime environment, without printing secrets.
- Use `--rate-limit` conservatively for corpus encoding.
- Prefer local encoders or pre-encoded queries for private data.

## Invalid Input JSONL

Symptoms:

- missing document ids;
- `contents not found`;
- field count mismatch;
- unexpected empty vectors after encoding.

Recovery:

1. Run `scripts/validate_dense_jsonl.py --input INPUT --fields FIELD...`.
2. If ids are stored under a custom key, pass `--docid-field FIELD` to both the validator and Pyserini `input` subcommand.
3. If fields are packed into `contents`, make sure `--delimiter` matches exactly; for newline use `"\\n"` on the command line.
4. If fields are direct keys, ensure every required field exists unless the specific dataset format intentionally permits missing fields.

## Encoded Vector or Dimension Mismatch

Symptoms:

- Faiss index builder errors while converting JSONL;
- search scores are nonsensical after swapping models;
- `--dim` does not match vector length.

Recovery:

- Validate encoded JSONL with `--require-vector --dimension N`.
- Match corpus encoder and query encoder families; do not search a DPR index with a TCT-ColBERT query encoder.
- Use `python -m pyserini.index.faiss --dim N` matching actual vector length.
- Use `--normalize-distances` only when intentionally aligning Faiss inner-product scoring with Lucene dense behavior.

## Faiss Index Has No Raw Text

Symptoms:

- user asks to fetch passages from Faiss hits;
- `docid` is available but document body is not.

Recovery:

- Explain that Faiss dense indexes contain vectors and ids, not stored raw passages.
- Use a companion sparse Lucene index for content fetch.
- Route raw document retrieval, `doc()` calls, and stored-field decisions to `../../index-search-fetch/SKILL.md`.

## Lucene Dense/HNSW Routing Errors

Symptoms:

- using `pyserini.search.faiss` against a Lucene dense index;
- using `pyserini.search.lucene --dense` without `--hnsw` or `--flat`;
- missing ONNX encoder name for a Lucene dense prebuilt index.

Recovery:

- Use `python -m pyserini.search.lucene --dense --hnsw` or `--flat` for Lucene dense vector indexes.
- Use `--onnx-encoder NAME` when the Lucene dense search path requires an ONNX encoder.
- Use `python -m pyserini.search.faiss` only for Faiss indexes.

## Hybrid Retrieval Alignment Problems

Symptoms:

- hybrid results worse than expected;
- dense and sparse indexes use different document id spaces;
- score scale overwhelms one component.

Recovery:

- Confirm the dense Faiss index and sparse Lucene index cover the same corpus and document ids.
- Start with `fusion --normalization` when dense and sparse scores have different scales.
- Tune `fusion --alpha` and decide whether `--weight-on-dense` matches the intended interpretation.
- Evaluate the final run through `../../evaluation-and-fusion/SKILL.md` rather than judging from top hits only.

## Ambient `--help` Fails Before Argument Parsing

Some Pyserini CLIs import optional dependencies before printing help. If `python -m pyserini.encode --help` fails with a missing package such as `numpy`, or `python -m pyserini.search.faiss --help` fails with Java/JNI or Faiss imports, treat that as a runtime setup issue rather than a CLI syntax issue. Route environment repair to `../../install-and-runtime/SKILL.md`, then retry help checks.
