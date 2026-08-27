# Training Troubleshooting

## Install And Import Failures

Symptom: `ModuleNotFoundError: colbert`, missing `colbert.infra`, or unexpected package version.

Actions:

- Confirm the installed distribution is `colbert-ai` and import package is `colbert`.
- Check that the active Python environment imports `colbert`, `colbert.infra`, and `from colbert import Trainer`.
- Avoid assuming GPU packages are installed in CPU-only inspection environments.
- If optional dependencies such as FAISS, CUDA-enabled Torch, or Transformers models are missing, separate safe validation from real training.

## CUDA And Backend Failures

Symptom: CUDA unavailable, model `.cuda()` errors, distributed launch failure, or training hangs after launch.

Actions:

- Treat practical ColBERT training and distillation scoring as GPU-required work.
- Confirm `torch.cuda.is_available()` and the number of visible GPUs before launch.
- Match `RunConfig(nranks=...)` to available GPUs unless using a deliberately configured distributed environment.
- For CPU-only machines, stop at data validation and template generation.
- If running on a GPU machine for CPU-only checks, set GPU visibility deliberately when needed.

## Batch And Distributed Assertions

Symptom: assertion involving `(bsize, nranks)` or unexpected per-process batch size.

Cause: ColBERT asserts `config.bsize % config.nranks == 0`, then divides `bsize` by `nranks` internally.

Actions:

- Choose a global `bsize` divisible by `nranks`.
- Reduce `bsize` for OOM, then increase `accumsteps` if the effective batch size becomes too small.
- Re-check `bsize` whenever changing the number of GPUs.

## Triples Shape Or `nway` Mismatch

Symptom: reshape failures, loss shape errors, unexpectedly truncated passages, or validation reports such as `expected qid plus at least N passages`.

Actions:

- For basic triples `[qid, pos, neg]`, use `nway=2`.
- For 64-way JSONL examples, use `nway=64`.
- Remember ColBERT consumes the first `nway` passage entries after the query ID.
- Run `scripts/validate_training_files.py --nway <N>` before launch.
- Do not mix scored and unscored entries inside one example unless the preprocessing and training objective intentionally support it.

## Missing Query Or Passage References

Symptom: `KeyError` from query or collection lookup, empty data assertions, or validator reports missing qids/pids.

Actions:

- Confirm every triples qid appears in `queries.tsv`.
- Confirm every triples pid appears in `collection.tsv`.
- Check duplicate IDs and empty text rows.
- For collection files, ensure passage IDs align with zero-based row positions or adapt loading intentionally.
- Validate a representative sample first, then validate the full file when practical.

## Scored Examples And Distillation Issues

Symptom: KL-divergence loss behaves unexpectedly, teacher scores seem ignored, or scored JSONL fails parsing.

Actions:

- Encode each scored passage as `[pid, score]`.
- Ensure all passage entries in a scored example include numeric scores.
- Check `ignore_scores`; when it is true, training uses cross-entropy behavior even with scores present.
- Tune `distillation_alpha` when teacher-score scale is too sharp or too flat.
- Keep `nway` equal to the number of scored passages intended for each example.
- Treat score generation with cross-encoders as a separate GPU-heavy preprocessing job.

## Checkpoint Confusion

Symptom: training starts from a different checkpoint than expected.

Cause: `Trainer.train(checkpoint=...)` overrides `ColBERTConfig(checkpoint=...)` for Trainer runs.

Actions:

- Put the intended source checkpoint in `trainer.train(checkpoint=...)`.
- Remove or align `ColBERTConfig(checkpoint=...)` to avoid misleading readers.
- In generated scripts, print or log the explicit checkpoint value before launch.

## OOM And Slow Training

Symptom: CUDA out of memory, very slow steps, or unstable distributed training.

Actions:

- Reduce `bsize` first while keeping it divisible by `nranks`.
- Increase `accumsteps` to preserve effective batch size.
- Reduce `doc_maxlen` only if truncating passages is acceptable.
- Reconsider `nway=64` and `use_ib_negatives=True` if GPU memory is limited.
- Use fewer ranks only when hardware requires it, then adjust `bsize` accordingly.

## Template Or Validation Helper Problems

Symptom: bundled helper script fails before importing ColBERT.

Actions:

- Use Python 3.9+ for the helpers because they use modern type hints.
- Run helpers from any working directory by passing explicit file paths.
- If validation reports many errors, fix the earliest parse/ID issue first; later errors may be cascading symptoms.
- The helpers are deterministic and do not launch training, download checkpoints, or import ColBERT.
