# ESMFold API Reference

## Installation and Imports

ESMFold is exposed through `fair-esm`, but the structure predictor needs the ESMFold optional dependency stack in addition to the base package:

```python
import torch
import esm
```

Base ESM APIs may import successfully even when ESMFold inference fails because OpenFold-style dependencies are missing. If `esm.pretrained.esmfold_v1()` fails before model loading, check [troubleshooting.md](troubleshooting.md) before changing code.

## Model Loading

```python
model = esm.pretrained.esmfold_v1()
model = model.eval()
```

`esm.pretrained.esmfold_v1()` loads the recommended ESMFold v1 model. It downloads weights through PyTorch Hub-style mechanisms unless weights are already cached. The older `esm.pretrained.esmfold_v0()` exists for paper-era reproduction, while `esmfold_structure_module_only_*()` functions are ablation baselines and are not recommended for normal structure prediction.

Typical device setup:

```python
if torch.cuda.is_available():
    model = model.cuda()
else:
    model.esm.float()
    model = model.cpu()
```

On CPU, convert `model.esm` to fp32 before inference because the ESM-2 language-model component is initialized in fp16 and fp16 CPU inference is not supported for this path.

## Single-Sequence PDB Strings

```python
sequence = "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"

with torch.no_grad():
    pdb_string = model.infer_pdb(sequence)

with open("result.pdb", "w", encoding="utf-8") as handle:
    handle.write(pdb_string)
```

`model.infer_pdb(sequence)` returns one PDB-format string. It is a convenience wrapper around `model.infer_pdbs([sequence])[0]`, which itself calls `model.infer(...)` and `model.output_to_pdb(...)`.

## Batched Outputs and Confidence

Use `model.infer` when you need structured tensors, batch folding, pLDDT, pTM, or custom PDB conversion:

```python
sequences = [
    "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG",
    "KALTARQQEVFDLIRDHISQTGMPPTRAEIAQRLGFRSPNAAEEHLKALARKGVIEIVSGASRGIRLLQEE",
]

with torch.no_grad():
    output = model.infer(sequences, num_recycles=4)
    pdb_strings = model.output_to_pdb(output)

mean_plddt = output["mean_plddt"]
ptm = output["ptm"]
```

Important output fields for user-facing structure prediction:

| Field | Meaning |
| --- | --- |
| `model.output_to_pdb(output)` | Converts model output tensors into one PDB string per input sequence. |
| `output["mean_plddt"]` | Mean predicted lDDT confidence on a 0-100 scale. The PDB writer also stores per-atom/residue pLDDT in B-factor fields. |
| `output["ptm"]` | Predicted TM-score style global confidence per folded sequence. |
| `output["plddt"]` | Per-position pLDDT tensor on a 0-100 scale. |

When a downstream tool needs pLDDT from a PDB file, load B-factors from the written PDB and average them over atoms/residues according to the tool's policy.

## Recycles

`model.infer(sequences, num_recycles=...)` controls the number of recycling iterations. `None` uses the model's training/default maximum, documented by the CLI as 4. More recycles can improve refinement but increase runtime and memory pressure. For memory-constrained tasks, try fewer recycles together with chunking or smaller batches.

## Chunk Size

```python
model.set_chunk_size(128)
```

`set_chunk_size` chunks axial attention in the folding trunk. This changes memory behavior from roughly quadratic in sequence length to a lower-memory chunked computation, at the cost of speed. Recommended starting values are `128`, then `64`, then `32` for tighter memory. Use `None` to return to default unchunked behavior.

## Multimers

ESMFold accepts multimer sequences by separating chains with a colon in the sequence string:

```python
with torch.no_grad():
    pdb_string = model.infer_pdb("MKTAYIAKQRQISFVKSHFSRQ:DLLKKALE")
```

Internally, `model.infer` inserts a poly-glycine linker and chain index metadata so `output_to_pdb` can produce chain-aware PDB output. Keep the whole multimer as one FASTA record or one Python sequence string; do not pass chains as separate batch entries unless independent predictions are intended.

## API Boundaries

- ESMFold predicts structures from sequences; it is not the API for extracting language-model embeddings. Route embeddings to `../model-embeddings/SKILL.md`.
- ESMFold is the sequence-to-structure direction; route structure-to-sequence design or coordinate-conditioned scoring to `../inverse-folding/SKILL.md`.
- `esm.pretrained.load_model_and_alphabet(...)` and `Alphabet` are central to language-model workflows, but ESMFold loading returns only the structure model from `esmfold_v1()`.
