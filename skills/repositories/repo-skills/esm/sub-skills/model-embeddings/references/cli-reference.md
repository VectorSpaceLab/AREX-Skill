# `esm-extract` CLI Reference

`esm-extract` extracts per-sequence `.pt` files from a FASTA file using a single-sequence ESM model. It is installed with `fair-esm` and mirrors the installed console entry point behavior.

## Command Shape

```bash
esm-extract MODEL_LOCATION FASTA_FILE OUTPUT_DIR \
  --repr_layers -1 \
  --include mean per_tok \
  --toks_per_batch 4096 \
  --truncation_seq_length 1022 \
  --nogpu
```

Arguments:

| Argument | Meaning |
| --- | --- |
| `MODEL_LOCATION` | Public model name such as `esm2_t33_650M_UR50D` or a local `.pt` checkpoint path. |
| `FASTA_FILE` | FASTA with unique record labels. Duplicate labels fail because output filenames are label-based. |
| `OUTPUT_DIR` | Directory where one `.pt` file per FASTA label is written. |
| `--repr_layers` | One or more layer indices. `-1` means final layer in CLI normalization; `0` is embeddings before transformer blocks. |
| `--include` | One or more of `mean`, `per_tok`, `bos`, `contacts`. Required by the upstream parser. |
| `--toks_per_batch` | Approximate token budget per batch; lower it for memory pressure. |
| `--truncation_seq_length` | Prefix length retained per sequence before model inference; default is `1022`. |
| `--nogpu` | Keep model/tokens on CPU even when CUDA is available. |

The CLI auto-detects CUDA unless `--nogpu` is set.

## Output `.pt` Files

Each FASTA record writes `OUTPUT_DIR/<label>.pt` containing a dictionary with:

| Key | Included when | Contents |
| --- | --- | --- |
| `label` | Always | FASTA label string. |
| `representations` | `--include per_tok` | Layer map of residue-level tensors shaped `(truncated_len, hidden_dim)`. |
| `mean_representations` | `--include mean` | Layer map of mean-pooled residue tensors shaped `(hidden_dim,)`. |
| `bos_representations` | `--include bos` | Layer map of BOS-token tensors shaped `(hidden_dim,)`; upstream docs caution not to use BOS with pretrained models for supervised interpretation. |
| `contacts` | `--include contacts` | Contact tensor shaped `(truncated_len, truncated_len)`. |

Load outputs with `torch.load(path, map_location="cpu")` when inspecting on a CPU machine.

## Safe Command Builder

Use the bundled helper to validate options and print a command without loading weights:

```bash
python sub-skills/model-embeddings/scripts/esm_extract_command_builder.py \
  esm2_t33_650M_UR50D proteins.fasta protein_embeddings \
  --repr-layers -1 --include mean contacts --nogpu --print-only
```

The generated command uses the installed `esm-extract` entry point by default. Add `--runner python-script --script-path path/to/extract.py` only if an environment lacks the console entry point and you have a self-contained script path available.

## Difficult Case: Mixed FASTA, Mean + Contacts, CPU

```bash
python sub-skills/model-embeddings/scripts/esm_extract_command_builder.py \
  esm2_t33_650M_UR50D mixed.fasta mixed_esm2_embeddings \
  --repr-layers -1 \
  --include mean contacts \
  --toks-per-batch 1024 \
  --truncation-seq-length 1022 \
  --nogpu \
  --print-only
```

Then run the printed command after confirming model downloads/cache and CPU runtime are acceptable.

## Why MSA Transformer Fails Here

`esm-extract` reads a FASTA as independent single sequences and feeds 2D tokens into the model. MSA Transformer requires aligned MSA inputs with 3D tokens `(batch, alignments, tokens)`. If the model is `esm_msa1b_t12_100M_UR50S` or another MSA Transformer checkpoint, use the Python MSA workflow in [api-reference.md](api-reference.md) instead of `esm-extract`.
