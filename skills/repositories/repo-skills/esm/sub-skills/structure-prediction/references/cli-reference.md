# ESMFold CLI Reference

## Command Shape

```bash
esm-fold -i input.fasta -o pdb_output_dir [OPTIONS]
```

The `esm-fold` console script folds every FASTA record into one PDB file under the output directory. The output filename is derived from the FASTA header, with `.pdb` appended. For automation, make FASTA headers filesystem-safe and unique.

Use the bundled command builder to validate paths and print a command without starting inference:

```bash
python scripts/esm_fold_command_builder.py \
  --fasta input.fasta \
  --pdb pdb_output_dir \
  --cpu-only \
  --chunk-size 128 \
  --max-tokens-per-batch 512
```

The helper defaults to `--print-only`; it does not load PyTorch, download weights, or run `esm-fold`.

## Core Flags

| Flag | Meaning |
| --- | --- |
| `-i`, `--fasta PATH` | Required input FASTA file. Each record is predicted independently. |
| `-o`, `--pdb DIR` | Required output directory for generated `.pdb` files. The CLI creates the directory when possible. |
| `-m`, `--model-dir DIR` | Parent directory used as the PyTorch Hub cache location for pretrained ESM weights. Useful for pre-downloaded weights or controlled caches. |
| `--num-recycles N` | Number of recycles. `None`/omitted uses the model default, documented as the training setting of 4. |
| `--max-tokens-per-batch N` | Groups shorter sequences into batches up to this token count. Lower it to reduce per-forward memory. Set `0` to disable batching. |
| `--chunk-size N` | Chunk axial attention to lower memory. Common values are `128`, `64`, or `32`; lower values are slower but use less memory. |
| `--cpu-only` | Run on CPU. The CLI converts the ESM language-model component to fp32 before moving to CPU. Very slow for real folding. |
| `--cpu-offload` | Use FSDP CPU parameter offloading for the ESM component while running the structure model on CUDA. Useful for long sequences when GPU memory is limited. |

## Output and Logs

For each successful FASTA record, `esm-fold` writes one PDB string to:

```text
<pdb_output_dir>/<fasta_header>.pdb
```

The CLI logs progress with sequence length, pLDDT, pTM, per-sequence runtime, and completion count. Failed CUDA OOM batches are logged and skipped; other exceptions are re-raised.

Expected log fields:

- `pLDDT`: mean predicted lDDT on a 0-100 scale for the predicted structure.
- `pTM`: predicted TM-score style global confidence.
- `batch size`: appears when multiple shorter records are folded together.

## FASTA Requirements

- Use amino-acid sequences as FASTA records; avoid whitespace inside sequences.
- Use unique, filesystem-safe headers because headers become output filenames.
- For multimers, put chains in one FASTA record and separate chains with `:`. Example sequence line: `MKTAYIAKQRQISFVKSHFSRQ:DLLKKALE`.
- If a caller provides many short sequences, keep batching enabled for speed unless memory errors occur.
- If a caller provides one long sequence, batching is irrelevant; use `--chunk-size`, fewer recycles, or CPU offload for memory.

## Safe Command Patterns

CPU-only smoke command for a tiny FASTA:

```bash
esm-fold -i small.fasta -o pdbs --cpu-only --chunk-size 128 --max-tokens-per-batch 512
```

Lower-memory CUDA command for long records:

```bash
esm-fold -i long_sequences.fasta -o pdbs --chunk-size 64 --max-tokens-per-batch 256 --num-recycles 2
```

CPU-offload command for long CUDA inference:

```bash
esm-fold -i long_sequences.fasta -o pdbs --cpu-offload --chunk-size 128 --max-tokens-per-batch 256
```

Use `--model-dir` when a shared or pre-populated model cache is required:

```bash
esm-fold -i input.fasta -o pdbs --model-dir model_cache
```

## CLI Boundaries

- `esm-fold` performs real model loading, optional downloads, and heavy inference. Do not run it as a cheap validation unless the environment, model cache, hardware, and runtime budget are confirmed.
- `esm-fold --help` and the bundled command builder are safe lightweight checks.
- Do not use `esm-fold` for embedding extraction; use the embedding sub-skill and `esm-extract` instead.
