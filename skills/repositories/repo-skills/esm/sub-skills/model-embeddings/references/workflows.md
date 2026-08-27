# Model Embedding Workflows

## Choose a Model

Start with the smallest model that satisfies the task:

- Smoke tests, CPU-only checks, command validation: `esm2_t6_8M_UR50D`.
- General-purpose embeddings with stronger quality: `esm2_t33_650M_UR50D` or `esm2_t36_3B_UR50D` if hardware allows.
- Maximum ESM-2 capacity: `esm2_t48_15B_UR50D`, usually with GPU plus CPU offload.
- MSA-based embeddings or contacts: `esm_msa1b_t12_100M_UR50S` through Python API.

Before running model inference, confirm PyTorch is installed and decide whether downloads are allowed. Public loaders normally fetch weights through Torch Hub when not cached.

## Compute Single-Sequence Embeddings

```python
import torch
import esm

model_name = "esm2_t6_8M_UR50D"
model, alphabet = esm.pretrained.load_model_and_alphabet(model_name)
model.eval()

if torch.cuda.is_available():
    model = model.cuda()

data = [("seqA", "MKTAYIAKQRQISFVKSHFSRQ")]
batch_converter = alphabet.get_batch_converter(truncation_seq_length=1022)
labels, seqs, tokens = batch_converter(data)
if torch.cuda.is_available():
    tokens = tokens.cuda()

layer = model.num_layers
with torch.no_grad():
    results = model(tokens, repr_layers=[layer], return_contacts=False)

reps = results["representations"][layer].cpu()
lengths = (tokens.cpu() != alphabet.padding_idx).sum(1)
mean_reps = [reps[i, 1 : length - 1].mean(0) for i, length in enumerate(lengths)]
```

Use this pattern when the downstream task needs one vector per protein. Use `per_tok`-style residue embeddings when downstream logic needs one vector per amino acid.

## Compute Contacts

```python
with torch.no_grad():
    results = model(tokens, repr_layers=[model.num_layers], return_contacts=True)
contacts = results["contacts"].cpu()
```

Contacts require contact regression weights for models that support them. If a local checkpoint lacks its sibling regression file, embeddings can still load but contact predictions may be incorrect and the loader warns about missing regression weights.

## Embed MSAs

```python
import torch
import esm

model, alphabet = esm.pretrained.esm_msa1b_t12_100M_UR50S()
model.eval()
msa_converter = alphabet.get_batch_converter()
msa = [
    ("query", "MKTAYIAK"),
    ("homolog1", "MKTAYVAK"),
    ("homolog2", "MKTAYIAK"),
]
labels, msa_strs, msa_tokens = msa_converter(msa)

with torch.no_grad():
    out = model(msa_tokens, repr_layers=[model.num_layers], return_contacts=True)
```

If the user tries to pass MSA Transformer to `esm-extract`, redirect them to this Python workflow. `esm-extract` checks for `MSATransformer` and raises a clear error because its FASTA batching path is single-sequence only.

## Handle Long Sequences

- For quick extraction, set `truncation_seq_length=1022`, matching the CLI default.
- Warn the user when truncation changes biological interpretation; contacts and mean embeddings cover only the retained prefix.
- For larger models or long sequences, reduce `toks_per_batch`, force CPU only if no GPU is available, or use a smaller model.
- For ESM-2 15B, consider the FSDP CPU offload pattern in [fsdp-offloading.md](fsdp-offloading.md).

## Validate Without Downloads

For environments where network/model downloads are unavailable, use lightweight checks:

```bash
esm-extract --help
python sub-skills/model-embeddings/scripts/esm_extract_command_builder.py --help
```

For API checks without weights, instantiate alphabets only:

```python
import esm
alphabet = esm.Alphabet.from_architecture("ESM-1b")
converter = alphabet.get_batch_converter(truncation_seq_length=10)
labels, seqs, toks = converter([("p", "K A <mask> I S Q")])
assert toks.ndim == 2
```
