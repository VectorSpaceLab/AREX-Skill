# Model Embeddings Troubleshooting

## Unknown Model Name or HTTP Download Failure

Symptoms:

- `Could not load ... check if you specified a correct model name?`
- Torch Hub URL or HTTP errors.
- Long hangs before first inference.

Fixes:

- Check exact model spelling, including case: `esm2_t33_650M_UR50D`, not `esm2_t33_650m`.
- Use a smaller known model for smoke tests: `esm2_t6_8M_UR50D`.
- Confirm network access or pre-populate the Torch Hub cache outside the generated skill workflow.
- If using a local file, pass a `.pt` path so `load_model_and_alphabet_local()` is used.

## Local Checkpoint Missing Contact Regression Weights

Symptoms:

- Warning: `Regression weights not found, predicting contacts will not produce correct results.`
- Embeddings load, but contacts are suspicious or unavailable.

Fixes:

- Put the matching `MODEL-contact-regression.pt` file next to `MODEL.pt` for local checkpoints that expect contact regression weights.
- If only embeddings are needed, omit `return_contacts=True` or `--include contacts`.
- For public model names, let the loader download both model and regression weights when network access is allowed.

## MSA Transformer Passed to `esm-extract`

Symptoms:

- Error: `This script currently does not handle models with MSA input (MSA Transformer).`
- User has aligned sequences but tries `esm-extract esm_msa1b_t12_100M_UR50S ...`.

Fix:

- Do not use `esm-extract` for MSA Transformer.
- Load `esm.pretrained.esm_msa1b_t12_100M_UR50S()` in Python.
- Pass one MSA as `[(label, aligned_sequence), ...]` or a batch of such MSAs to `alphabet.get_batch_converter()`.
- Ensure all aligned sequences inside each MSA have equal length.

## GPU Out Of Memory

Symptoms:

- CUDA OOM during loading or forward pass.
- OOM only for long sequences or large `toks_per_batch`.

Fixes:

- Use a smaller model such as `esm2_t6_8M_UR50D` or `esm2_t12_35M_UR50D`.
- Lower `--toks_per_batch` for `esm-extract`.
- Shorten or explicitly truncate long sequences with `--truncation_seq_length`.
- Move to CPU with `--nogpu` if GPU memory is the blocker and slow runtime is acceptable.
- For `esm2_t48_15B_UR50D`, use the FSDP CPU offload pattern in [fsdp-offloading.md](fsdp-offloading.md).

## CPU-Only Runs Are Too Slow

Symptoms:

- Inference appears stuck but CPU is active.
- Large ESM-2 models run for a very long time.

Fixes:

- Use the smallest model that can answer the question.
- Run a one-sequence smoke test before bulk extraction.
- Avoid `contacts` unless needed because contact prediction requires attention outputs.
- Reduce FASTA batch size and process subsets when validating commands.

## Sequences Longer Than Truncation

Symptoms:

- Embeddings/contact maps are shorter than the original FASTA sequence.
- Downstream code expects full-length outputs.

Fixes:

- Remember the CLI default `--truncation_seq_length 1022`.
- Increase truncation only if the selected model and memory allow it.
- Document that `per_tok`, `mean`, and `contacts` cover only `min(truncation_seq_length, len(sequence))` residues.
- Split long proteins only if downstream biology supports separate segments.

## Duplicate FASTA Labels

Symptoms:

- `AssertionError: Found duplicate sequence labels`.
- Output files would overwrite each other.

Fixes:

- Make every FASTA header unique before using `FastaBatchedDataset.from_file()` or `esm-extract`.
- Include stable suffixes such as `proteinA_isoform1`, `proteinA_isoform2`.
- Avoid spaces or path separators in labels when filenames must be portable.

## Wrong MSA Input Shape

Symptoms:

- `assert tokens.ndim == 3` from MSA Transformer.
- `RuntimeError: Received unaligned sequences for input to MSA, all sequence lengths must be equal.`
- Single-sequence model receives 3D tokens or MSA model receives 2D tokens.

Fixes:

- For single-sequence ESM/ESM-2 models, input tokens must be 2D `(batch, tokens)`.
- For MSA Transformer, input tokens must be 3D `(batch, alignments, tokens)`.
- Use the model's own `alphabet.get_batch_converter()`; it selects `BatchConverter` vs `MSABatchConverter` from the alphabet.
- Check aligned MSA rows are equal length after gap handling.

## Representation Layer Index Errors

Symptoms:

- `AssertionError` from `esm-extract` layer validation.
- Missing key in `out["representations"]`.

Fixes:

- In `esm-extract`, valid layers satisfy `-(model.num_layers + 1) <= layer <= model.num_layers`; use `-1` for final layer.
- In direct Python calls, pass concrete layer indices such as `[model.num_layers]` rather than `[-1]`.
- Request the same layer you later read from `out["representations"]`.
- Use `model.num_layers` after loading instead of hard-coding layer counts when switching models.
