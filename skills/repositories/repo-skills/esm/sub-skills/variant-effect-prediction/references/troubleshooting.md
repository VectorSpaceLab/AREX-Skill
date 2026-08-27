# Variant Prediction Troubleshooting

## Wild-Type Mismatch

Symptom: `AssertionError: The listed wildtype does not match the provided sequence`.

Likely causes:

- `--offset-idx` is off by one or by a biological numbering offset.
- The DMS CSV uses a different isoform, processed mature sequence, signal peptide state, or construct boundaries.
- The mutation column contains multi-mutants or invalid notation that the example parser treats incorrectly.

Response:

1. Validate the CSV with the bundled helper.
2. Inspect the first few failing mutations and compute `mutation_number - offset_idx` manually.
3. Try candidate offsets based on whether the first sequence residue is numbered `0`, `1`, or a domain-specific residue such as `24`.
4. Confirm the supplied `--sequence` exactly matches the assay reference sequence.

## Invalid Mutation Notation

The example parser expects single substitutions like `A24D`. It does not validate notation before indexing. Reject or preprocess entries containing separators, empty positions, non-integer positions, insertions, deletions, or stop-codon conventions before running model inference.

## MSA Transformer Strategy Errors

Symptom: assertion that MSA Transformer only supports masked marginal strategy, or failure around a missing MSA.

Response:

- Use `--scoring-strategy masked-marginals` with `esm_msa1b_t12_100M_UR50S`.
- Provide `--msa-path` to an A3M-like FASTA file.
- Set `--msa-samples` to a bounded number that fits memory; the example default is `400`.
- Confirm lowercase A3M insertions, `.`, and `*` are expected to be stripped before batching.

## CUDA Despite `--nogpu`

The example only guards `model.cuda()` with `--nogpu`. Several inference branches still call `.cuda()` on token tensors directly in `wt-marginals`, `masked-marginals`, `pseudo-ppl`, and MSA paths. On CPU-only systems this can fail even when `--nogpu` is supplied.

Practical fixes:

- Run on a CUDA-capable environment for full inference.
- Patch a local copy of the script to create a `device = torch.device("cuda" if torch.cuda.is_available() and not args.nogpu else "cpu")`, move the model to that device, and replace tensor `.cuda()` calls with `.to(device)`.
- Use the helper for command construction and CSV validation when full inference is not available.

## Model Download Or Cache Failures

Model loading uses ESM pretrained model names or local checkpoint files. Pretrained names can trigger downloads through the PyTorch hub/cache stack.

Response:

- Verify network access or pre-populate the torch cache in the runtime environment.
- Use local checkpoint paths with `--model-location` when offline.
- Check available disk space for five ESM-1v checkpoints before ensemble runs.
- Keep model names exact, for example `esm1v_t33_650M_UR90S_1` or `esm_msa1b_t12_100M_UR50S`.

## Output CSV Surprises

The script writes the output CSV with all original columns plus one prediction column per model location.

Watch for:

- Existing output files being overwritten.
- Local checkpoint paths becoming column names.
- Multiple ensemble runs appending columns with duplicate names if the same model labels are reused.
- Pandas writing an index column unless downstream code drops or handles it.

## Runtime Scale

ESM-1v models are large and the five-model ensemble is expensive. `masked-marginals` loops over sequence positions, `pseudo-ppl` loops over DMS rows and masks positions inside each mutated sequence, and MSA Transformer scales with MSA depth and sequence length. Reduce `--msa-samples`, test on a tiny CSV, and validate command construction before full DMS scoring.
