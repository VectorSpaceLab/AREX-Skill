# Input Parsing API Reference

This reference summarizes public imports that are useful for validating Chai FASTA inputs without running full model inference.

## Package and CLI Facts

- Install from PyPI with `pip install chai_lab==0.6.1`, or install a compatible Chai Lab checkout with a standard Git-based pip install.
- Import package: `chai_lab`.
- CLI command: `chai-lab`; relevant full-fold route is `chai-lab fold`.
- Python inference entrypoint: `chai_lab.chai1.run_inference`.

## Core Data Types and Functions

### `chai_lab.data.dataset.inference_dataset.Input`

Signature:

```python
Input(sequence: str, entity_type: int, entity_name: str)
```

Represents one FASTA record after header parsing. `entity_type` is an integer value from `EntityType`; `entity_name` is the required FASTA label.

### `chai_lab.data.dataset.inference_dataset.read_inputs`

Signature:

```python
read_inputs(fasta_file: Path, length_limit: int | None = None) -> list[Input]
```

Behavior:

- Reads FASTA records with Chai's supported headers.
- Raises `ValueError` for unsupported entity types, missing labels, or extra header fields.
- Emits warnings when sequence heuristics suggest a different entity type than the header.
- Applies an optional character-count limit across raw sequences when `length_limit` is provided.
- Does not enforce duplicate entity-name uniqueness; inference context construction enforces that later.

### `chai_lab.data.parsing.fasta.read_fasta_content`

Signature:

```python
read_fasta_content(content) -> list[Fasta]
```

Uses Biopython FASTA parsing and returns records as `(header, sequence)` named tuples. Use this for low-level parsing checks when you do not want Chai entity validation yet.

### `chai_lab.data.parsing.fasta.write_fastas`

Signature:

```python
write_fastas(fastas, output_path: str) -> None
```

Writes Chai `Fasta(header, sequence)` records back to a FASTA file. Useful for generated or repaired inputs after you have decided exact headers.

### `chai_lab.data.parsing.input_validation.constituents_of_modified_fasta`

Signature:

```python
constituents_of_modified_fasta(sequence: str) -> list[str] | None
```

Tokenizes a protein/DNA/RNA-style sequence into single-letter constituents and bracketed modified residues. Returns `None` when brackets or characters are malformed. It does not validate SMILES.

Accepted examples:

```python
constituents_of_modified_fasta("RKDES")
constituents_of_modified_fasta("AAA(SEP)AAA")
constituents_of_modified_fasta("(KCJ)(SEP)(PPN)(B3S)(BAL)(PPN)KX(NH2)")
```

Rejected patterns include nested bracket starts, unmatched brackets, empty modifications, single-character modifications, and non-letter unbracketed characters.

### `chai_lab.data.parsing.input_validation.identify_potential_entity_types`

Signature:

```python
identify_potential_entity_types(sequence: str) -> list[EntityType]
```

Returns compatible entity types inferred from simple syntax heuristics. It can return multiple possibilities. Ligand and manual glycan compatibility are broad because many SMILES/glycan strings share ASCII character sets.

### `chai_lab.data.dataset.inference_dataset.load_chains_from_raw`

Signature:

```python
load_chains_from_raw(
    inputs: list[Input],
    identifier: str = "test",
    entity_name_as_subchain: bool = False,
    tokenizer=None,
) -> list[Chain]
```

Builds and tokenizes chains from parsed inputs. This can catch problems not visible in FASTA parsing, especially malformed ligands. Failed tokenization entries are logged and dropped; compare `len(chains)` with `len(inputs)`.

### `chai_lab.chai1.make_all_atom_feature_context`

Relevant signature fragment:

```python
make_all_atom_feature_context(
    fasta_file: Path,
    *,
    output_dir: Path,
    entity_name_as_subchain: bool = False,
    use_esm_embeddings: bool = True,
    use_msa_server: bool = False,
    msa_directory: Path | None = None,
    constraint_path: Path | None = None,
    use_templates_server: bool = False,
    templates_path: Path | None = None,
    esm_device=torch.device("cpu"),
)
```

This is heavier than basic parsing because it builds feature contexts and can load embeddings, MSAs, templates, and restraints. For pure input validation, prefer `read_inputs` plus optional `load_chains_from_raw` with no full model run.

### `chai_lab.chai1.run_inference`

Relevant signature fragment:

```python
run_inference(
    fasta_file: Path,
    *,
    output_dir: Path,
    use_esm_embeddings: bool = True,
    use_msa_server: bool = False,
    msa_directory: Path | None = None,
    constraint_path: Path | None = None,
    use_templates_server: bool = False,
    template_hits_path: Path | None = None,
    seed: int | None = None,
    device: str | None = None,
    low_memory: bool = True,
    fasta_names_as_cif_chains: bool = False,
)
```

Input-format implications:

- If `fasta_names_as_cif_chains=True`, FASTA entity names are used for parsing restraints and writing output CIF chain names.
- If `False`, Chai uses automatic `A`, `B`, `C`, ... chain names in accepted entity order.
- `output_dir` must be empty when inference starts; this is an inference concern covered by the CLI/inference sub-skill.

## `EntityType` Values

`chai_lab.data.parsing.structure.entity_type.EntityType` includes:

| Name | Value | FASTA header |
| --- | ---: | --- |
| `PROTEIN` | 0 | `protein` |
| `RNA` | 1 | `rna` |
| `DNA` | 2 | `dna` |
| `LIGAND` | 3 | `ligand` |
| `MANUAL_GLYCAN` | 7 | `glycan` |

Other enum values exist for parsed structures, but they are not accepted as input FASTA headers by `read_inputs`.

## Minimal Validation Snippet

```python
from collections import Counter
from pathlib import Path

from chai_lab.data.dataset.inference_dataset import read_inputs, load_chains_from_raw

fasta_file = Path("input.fasta")
inputs = read_inputs(fasta_file)
name_counts = Counter(item.entity_name for item in inputs)
duplicates = [name for name, count in name_counts.items() if count > 1]
if duplicates:
    raise ValueError(f"Duplicate entity names: {duplicates}")
chains = load_chains_from_raw(inputs)
if len(chains) != len(inputs):
    raise ValueError("At least one FASTA record failed Chai tokenization")
```

The bundled `scripts/validate_chai_fasta.py` wraps these checks with CLI reporting and safer defaults.
