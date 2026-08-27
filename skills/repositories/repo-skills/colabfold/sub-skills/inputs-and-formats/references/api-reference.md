# Input API reference

These APIs are the core input-format helpers distilled for future agents. Prefer importing from `colabfold.input` for lightweight parsing. Some names are re-exported by `colabfold.batch`, but importing `colabfold.batch` can require optional AlphaFold/JAX dependencies.

## `safe_filename(file)`

```python
from colabfold.input import safe_filename
safe = safe_filename("A:B complex/1")
```

Signature:

```python
safe_filename(file: str) -> str
```

Behavior:

- Keeps letters, digits, `_`, `.`, and `-`.
- Replaces every other character with `_`.
- Does not guarantee uniqueness; check for collisions after sanitization when planning batch outputs.

## `parse_fasta(fasta_string)`

```python
from colabfold.input import parse_fasta
sequences, descriptions = parse_fasta(">job\nYYDPETGTWY\n")
```

Signature:

```python
parse_fasta(fasta_string: str) -> tuple[list[str], list[str]]
```

Behavior:

- Returns sequences and header descriptions in the same order.
- Removes leading `>` from descriptions.
- Ignores blank lines and comment lines beginning with `#`.
- Appends non-header sequence lines to the current record without validation of amino-acid alphabet.
- Malformed content with sequence text before the first header is not a supported FASTA shape; validate files before expensive workflows.

## `classify_molecules(query_sequence)`

```python
from colabfold.input import classify_molecules
proteins, other = classify_molecules("PROTEINSEQ:ccd|ATP|2")
```

Signature:

```python
classify_molecules(query_sequence: str) -> tuple[list[str], list[tuple[MolType, str, int]] | None]
```

Behavior:

- Uppercases and splits the input string on `:`.
- Components without `|` are returned as protein sequences.
- Components with `|` are parsed as `molecule_type|sequence|(copies)`.
- Supported non-protein molecule types are handled through ColabFold's `MolType` enum, including DNA, RNA, CCD, and SMILES.
- SMILES entries convert semicolons back to colons after splitting, so aromatic SMILES colons must be escaped as `;` in FASTA.
- Copy count defaults to `1`; invalid integer copy counts raise.
- Returns `other=None` when no non-protein entries are present.

## `get_queries(input_path, sort_queries_by="length")`

```python
from colabfold.input import get_queries
queries, is_complex = get_queries("input.fasta", sort_queries_by="length")
```

Signature:

```python
get_queries(input_path: str | Path, sort_queries_by: str = "length") -> tuple[list[tuple[str, str | list[str], list[str] | Path | None, object | None]], bool]
```

Return tuple per query:

```python
(job_name, query_sequence, a3m_lines_or_path, template_path_or_nonprotein)
```

Common return shapes:

- FASTA monomer: `("job", "SEQUENCE", None, None)`.
- FASTA complex: `("job", ["CHAINA", "CHAINB"], None, other_molecules_or_none)`.
- A3M file: `("job_stem", "QUERYSEQ", [full_a3m_text], None)`.
- CSV with `a3mpath`: `("job", "SEQUENCE" or ["A", "B"], Path(...), template_path_or_none)`.

Input handling:

- Missing input path raises `OSError`.
- Unknown standalone file suffix raises `ValueError`.
- CSV/TSV requires `pandas` and columns `id` and `sequence`.
- Directory parsing accepts FASTA/A3M/PDB/mmCIF-like suffixes and ignores other files with warnings.
- PDB/mmCIF parsing requires optional AlphaFold components for sequence decoding.

Complex detection:

- Any list-valued query sequence marks `is_complex=True`.
- A serialized A3M beginning with `#lengths\tcardinalities` marks complex unless it represents a single protein with cardinality `1`.

Sorting:

- `length`: ascending by `len("".join(query_sequence))`.
- `msa_depth`: descending by number of A3M header lines in the first A3M block.
- `random`: random order.

## `msa_to_str(unpaired_msa, paired_msa, query_seqs_unique, query_seqs_cardinality)`

```python
from colabfold.input import msa_to_str
serialized = msa_to_str(
    unpaired_msa=[">101\nAAAAAAAA\n"],
    paired_msa=[">101\nAAAAAAAA\n"],
    query_seqs_unique=["AAAAAAAA"],
    query_seqs_cardinality=[2],
)
```

Signature:

```python
msa_to_str(
    unpaired_msa: list[str] | None,
    paired_msa: list[str] | None,
    query_seqs_unique: list[str],
    query_seqs_cardinality: list[int],
) -> str
```

Behavior:

- Prefixes the output with a `#lengths\tcardinalities` header.
- Builds paired rows by concatenating matching aligned rows across chains.
- Builds unpaired rows by padding other chains with gaps.
- Temporarily normalizes cardinality to one while building the body; cardinality remains encoded in the header.
- Raises `ValueError("Invalid pairing")` if both paired and unpaired inputs are missing.

## `pdb_to_string(pdb_file, chains=None, models=None)`

```python
from colabfold.input import pdb_to_string
filtered = pdb_to_string("input.pdb", chains="A,B", models=[1])
```

Signature:

```python
pdb_to_string(pdb_file: str, chains: str | list[str] | None = None, models: list | None = None) -> str
```

Behavior:

- Accepts a filesystem path or raw PDB text containing newline characters.
- Filters ATOM records by chain and model when requested.
- Converts known modified residues from HETATM/MODRES records into standard protein residue names.
- Keeps `MODEL`, `TER`, and `ENDMDL` markers for selected models.
- Skips duplicate alternate atom placements.

## mmCIF/PDB helper APIs with heavier dependencies

`colabfold.batch` contains helper functions for template-style conversion and validation:

```python
from colabfold.batch import convert_pdb_to_mmcif, validate_and_fix_mmcif
```

Signatures:

```python
convert_pdb_to_mmcif(pdb_file: Path) -> None
validate_and_fix_mmcif(cif_file: Path) -> None
```

Important caveats:

- Importing `colabfold.batch` can raise `RuntimeError` if `alphafold` is not installed.
- `validate_and_fix_mmcif` checks required mmCIF fields such as `_entity_poly_seq.mon_id` and may append a missing revision date while writing a `.bak` backup; do not treat it as a read-only validator.
- The bundled validator script in this sub-skill avoids these heavier functions by default.

## Minimal parser smoke checks

```bash
python - <<'PY'
from colabfold.input import parse_fasta, classify_molecules, get_queries
print(parse_fasta(">x\nACD\n"))
print(classify_molecules("ACD:ccd|ATP|2"))
print(get_queries("input.fasta"))
PY
```

If this fails at import time, install the base package before running validation. If it succeeds but prediction later fails, route the problem to batch prediction because AlphaFold/JAX/OpenMM are optional for input parsing.
