# API Reference

This reference lists Chai-1 APIs relevant to restraints and glycans in package version `0.6.1`.

## `run_inference`

```python
from pathlib import Path
from chai_lab.chai1 import run_inference

candidates = run_inference(
    fasta_file=Path("input.fasta"),
    output_dir=Path("outputs"),
    constraint_path=Path("restraints.csv"),
    use_esm_embeddings=True,
    use_msa_server=False,
    use_templates_server=False,
    num_trunk_recycles=3,
    num_diffn_timesteps=200,
    num_diffn_samples=5,
    num_trunk_samples=1,
    seed=42,
    device="cuda:0",
    low_memory=True,
    fasta_names_as_cif_chains=False,
)
```

Signature verified for Chai-1 `0.6.1`:

```text
run_inference(fasta_file: Path, *, output_dir: Path, use_esm_embeddings=True, use_msa_server=False, msa_server_url='https://api.colabfold.com', msa_directory=None, constraint_path=None, use_templates_server=False, template_hits_path=None, recycle_msa_subsample=0, num_trunk_recycles=3, num_diffn_timesteps=200, num_diffn_samples=5, num_trunk_samples=1, seed=None, device=None, low_memory=True, fasta_names_as_cif_chains=False) -> StructureCandidates
```

Restraint-specific notes:

- `constraint_path` points to the contact/pocket/covalent CSV.
- `fasta_names_as_cif_chains=False` means restraints use automatic `A`, `B`, `C`, ... chain IDs.
- `fasta_names_as_cif_chains=True` means restraints use the FASTA entity names and output CIF chain names also follow those names.
- The output directory must be empty before inference starts.
- Expensive inference is not needed to validate CSV schema; use the bundled `scripts/validate_restraints.py` first.

`StructureCandidates` fields:

- `cif_paths`
- `ranking_data`
- `msa_coverage_plot_path`
- `pae`
- `pde`
- `plddt`

## CLI Route

The Typer CLI exposes `chai-lab fold` from `chai_lab.chai1.run_inference`. Option names are generated from function parameters. For a restraint run, the important flags are:

```bash
chai-lab fold input.fasta outputs \
  --constraint-path restraints.csv \
  --device cuda:0 \
  --seed 42 \
  --num-trunk-recycles 3 \
  --num-diffn-timesteps 200 \
  --num-diffn-samples 5
```

When using FASTA entity names as restraint chain IDs, include:

```bash
chai-lab fold input.fasta outputs \
  --constraint-path restraints.csv \
  --fasta-names-as-cif-chains
```

Run `chai-lab fold --help` in the target environment for exact Typer rendering and boolean negation options.

## Restraint Parser

```python
from chai_lab.data.parsing.restraints import parse_pairwise_table

interactions = parse_pairwise_table("restraints.csv")
```

`parse_pairwise_table(table)` returns `list[PairwiseInteraction]` and performs these checks:

- Required columns exist by name.
- `restraint_id` is unique.
- `connection_type` is one of `contact`, `pocket`, `covalent`.
- `confidence` is in `[0.0, 1.0]` when supplied, with blanks filled as `1.0`.
- Distance fields are non-negative when supplied.
- `res_idxA` and `res_idxB` strings parse into residue and atom components.
- Contact/pocket row-shape assertions are enforced by `PairwiseInteraction.__post_init__`.

It does not fully prove that chain IDs, residue letters, residue positions, or covalent atom names exist in the FASTA-derived feature context. Those checks happen when Chai builds features or covalent bond pairs.

## `PairwiseInteraction`

Verified constructor fields:

```text
PairwiseInteraction(chainA, res_idxA, atom_nameA, chainB, res_idxB, atom_nameB, connection_type, max_dist_angstrom=10.0, min_dist_angstrom=0.0, confidence=1.0, comment='')
```

`connection_type` should be a `PairwiseInteractionType` enum value:

```python
from chai_lab.data.parsing.restraints import PairwiseInteraction, PairwiseInteractionType

contact = PairwiseInteraction(
    chainA="A",
    res_idxA="C387",
    atom_nameA="",
    chainB="B",
    res_idxB="Y101",
    atom_nameB="",
    connection_type=PairwiseInteractionType.CONTACT,
    max_dist_angstrom=5.5,
)
```

Key computed properties:

- `res_idxA_name` and `res_idxB_name`: first character of the residue token, or blank.
- `res_idxA_pos` and `res_idxB_pos`: integer position after the first character, defaulting to `1` when no residue token is present.
- `to_table_entry()`: returns a row dictionary without `restraint_id`.

Important assertions:

- Chains must be non-empty.
- `max_dist_angstrom >= min_dist_angstrom` when both are numeric.
- Pocket rows require blank `res_idxA`, nonblank `res_idxB`, and no atom names.
- Contact rows require a token or atom on both sides.
- Nonblank residue positions must be positive.

## `write_pairwise_table`

```python
from chai_lab.data.parsing.restraints import write_pairwise_table

write_pairwise_table([contact], "restraints.csv")
```

`write_pairwise_table(interactions, fname)` writes a CSV and assigns generated IDs `restraint_0`, `restraint_1`, ... . Use it when building restraints programmatically and then validate the file before inference.

## Glycan Parser Helpers

Public input behavior comes through `>glycan|name` FASTA records, but the parser functions are useful for validation:

```python
from chai_lab.data.parsing.glycans import glycan_string_residues

residues = glycan_string_residues("NAG(4-1 NAG)")
```

Observed parser behavior:

- A three-character uppercase/digit CCD code becomes one glycan residue.
- A glycosidic branch chunk such as `4-1` records an `O4` to `C1` bond.
- Parentheses may express nested and branched glycans.
- Empty or malformed glycan strings raise errors.

## Feature-Loading Implications

When `constraint_path` is supplied, Chai builds features in this order:

1. Parse pairwise table.
2. Load contact and pocket restraints into restraint feature context.
3. Convert covalent rows into atom covalent-bond indices.
4. Drop glycan leaving atoms in place for inferred glycan bonds.

This means a CSV can pass parser validation but still fail later if a chain ID, residue index, residue one-letter code, or covalent atom name does not match the FASTA-derived context. Use parser validation as the first gate, not the only gate.
