# FASTA and PDB API Reference

## `pipeline.fasta2inputs`

Signature:

```python
pipeline.fasta2inputs(
    fasta_path: str,
    output_dir: str | None = None,
    num_pseudo_msa: int = 15,
    device: torch.device | None = torch.device("cpu"),
    mask_rate: float = 0.12,
    num_cycle: int = 10,
    deterministic: bool = True,
)
```

Returns a generator. Each yielded value is:

```python
input_data, save_path
```

where `input_data` is a list of cycle dictionaries and `save_path` is the PDB path OmegaFold would write for that sequence.

### Parameters

| Parameter | Practical use |
| --- | --- |
| `fasta_path` | Path to a FASTA file with headers starting `>` or `:`. |
| `output_dir` | Destination directory for predicted PDB names. When passing a path directly to `fasta2inputs`, create it first. When `None`, a folder named after the FASTA basename is created next to the FASTA file. |
| `num_pseudo_msa` | Number of pseudo-MSA rows copied from the target sequence per cycle; output row count is `num_pseudo_msa + 1`. |
| `device` | Target device for generated tensors; use CPU for inspection. |
| `mask_rate` | Random masking rate for pseudo rows. Higher values replace more pseudo-row residues with token `21`. |
| `num_cycle` | Number of cycle dictionaries to produce. This should align with inference `--num_cycle` / forward `num_recycle`. |
| `deterministic` | When true, pseudo masks are reproducible for a fixed sequence length because the generator seed is `num_res`. |

### Minimal Inspection Example

```python
from omegafold import pipeline

for input_data, save_path in pipeline.fasta2inputs(
    "input.fasta",
    output_dir="out",
    num_pseudo_msa=2,
    num_cycle=1,
    deterministic=True,
):
    first_cycle = input_data[0]
    print(save_path)
    print(first_cycle["p_msa"].shape)
    print(first_cycle["p_msa_mask"].shape)
```

Expected shape for a sequence of length `L` with `num_pseudo_msa=2`:

```text
p_msa      -> torch.Size([3, L])
p_msa_mask -> torch.Size([3, L])
```

### Gotchas

- The generator sorts entries by sequence length, so do not assume FASTA file order.
- Headers are not sanitized beyond replacing the platform path separator; choose portable unique identifiers yourself.
- Duplicate resolved headers can overwrite PDB paths.
- Invalid residues fail during lookup; validate against `ARNDCQEGHILKMFPSTWYVX-` after applying `Z->E`, `B->D`, and `U->C` expectations.
- `output_dir=None` creates a directory as a side effect, even though no model inference runs.
- An explicit `output_dir` should already exist for direct API calls; otherwise `os.pathconf(output_dir, 'PC_NAME_MAX')` can raise `FileNotFoundError` before any PDB is written.

## `pipeline.path_leaf`

Signature:

```python
pipeline.path_leaf(path: str) -> str
```

Returns the final path component using `ntpath.split`, so it handles common Windows-style and POSIX-style path strings. `fasta2inputs` uses this to derive the default output folder name when `output_dir=None`.

Example:

```python
pipeline.path_leaf("/tmp/example.fasta")  # "example.fasta"
pipeline.path_leaf("C:\\tmp\\example.fasta")  # "example.fasta"
```

## `pipeline.save_pdb`

Signature:

```python
pipeline.save_pdb(
    pos14: torch.Tensor,
    b_factors: torch.Tensor,
    sequence: torch.Tensor,
    mask: torch.Tensor,
    save_path: str,
    model: int = 0,
    init_chain: str = "A",
) -> None
```

Writes atom14 coordinates to a PDB file with Biopython's `PDBIO`.

### Tensor Contract

| Argument | Shape | Meaning |
| --- | --- | --- |
| `pos14` | `[num_res, 14, 3]` | Atom14 coordinates for each residue. |
| `b_factors` | `[num_res]` | Per-residue value written into every emitted atom's B-factor field. |
| `sequence` | `[num_res]` | Residue indices from OmegaFold's residue table. |
| `mask` | `[num_res]` | Residue-level mask; false residues are skipped. |

`save_pdb` creates the parent directory for `save_path` automatically.

### Minimal Synthetic PDB Example

```python
import torch
from omegafold import pipeline

sequence = torch.tensor([0, 4, 7])  # A, C, G
pos14 = torch.zeros((3, 14, 3), dtype=torch.float32)
pos14[:, :, 0] = torch.arange(3, dtype=torch.float32).view(3, 1)
mask = torch.ones(3, dtype=torch.float32)
b_factors = torch.tensor([95.0, 70.0, 40.0])

pipeline.save_pdb(pos14, b_factors, sequence, mask, "tiny.pdb")
```

The resulting PDB should contain `ATOM` records with residue names `ALA`, `CYS`, and `GLY`; B-factor columns reflect `95.00`, `70.00`, and `40.00` on emitted atoms.

### Gotchas

- `sequence` index `21` is a gap/mask token and is skipped.
- `X` has index `20`; `save_pdb` cannot convert index `20` through `residx_to_3` because that helper indexes only the 20 canonical residues, so unknown residues are skipped by the writer.
- `pos14` coordinates are cloned to CPU inside the writer; inputs can come from model tensors, but CPU tensors are best for tiny checks.
- Biopython handles PDB formatting; unusual atom names, empty structures, or all-masked residues can produce sparse or effectively empty files.

## Bundled Helper

Use [`../scripts/inspect_fasta_pipeline.py`](../scripts/inspect_fasta_pipeline.py) to run these APIs safely from a shell. It creates a tiny FASTA by default, reports all generated shapes and paths, and can exercise `save_pdb` without model weights using `--write-tiny-pdb`.
