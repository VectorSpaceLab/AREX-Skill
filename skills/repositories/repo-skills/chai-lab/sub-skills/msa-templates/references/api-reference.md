# MSA and Template API Reference

## Package and CLI Facts

- Install target: `chai_lab==0.6.1` or a git install exposing the `chai_lab` import package.
- CLI entry point: `chai-lab`.
- Relevant CLI commands: `chai-lab fold`, `chai-lab a3m-to-pqt`, `chai-lab citation`.
- Safe help probes from this sub-skill directory: `chai-lab a3m-to-pqt --help` and `python scripts/validate_aligned_pqt.py --help`.

## `run_inference` MSA/Template Parameters

Relevant signature subset:

```python
run_inference(
    fasta_file: Path,
    *,
    output_dir: Path,
    use_esm_embeddings: bool = True,
    use_msa_server: bool = False,
    msa_server_url: str = "https://api.colabfold.com",
    msa_directory: Path | None = None,
    constraint_path: Path | None = None,
    use_templates_server: bool = False,
    template_hits_path: Path | None = None,
    recycle_msa_subsample: int = 0,
    num_trunk_recycles: int = 3,
    num_diffn_timesteps: int = 200,
    num_diffn_samples: int = 5,
    num_trunk_samples: int = 1,
    seed: int | None = None,
    device: str | None = None,
    low_memory: bool = True,
    fasta_names_as_cif_chains: bool = False,
) -> StructureCandidates
```

Mutual-exclusion rules enforced while making features:

| Rule | Failure message |
| --- | --- |
| Do not set both `use_msa_server=True` and `msa_directory=...`. | `Cannot specify both MSA server and directory` |
| Do not set both `use_templates_server=True` and `template_hits_path=...`. | `Cannot specify both templates server and path` |

Server side effects:

- `use_msa_server=True` creates `output_dir/msas` and expects it not to exist already.
- `use_templates_server=True` asks the server for template hits and expects `output_dir/msas/all_chain_templates.m8` to exist afterward.
- Server MSA generation is a network operation against `msa_server_url`.

Local MSA lookup:

- `msa_directory` is a directory, not a sequence-to-file mapping.
- Chai looks for `msa_directory / expected_basename(sequence)` for each unique protein sequence.
- If a protein MSA is missing, Chai logs a warning and uses a single-sequence MSA for that chain.
- Non-protein entities do not require `.aligned.pqt` files.

## `chai-lab a3m-to-pqt`

Command shape:

```bash
chai-lab a3m-to-pqt DIRECTORY [--output-directory TEXT]
```

Backed by:

```python
from chai_lab.data.parsing.msas.aligned_pqt import merge_a3m_in_directory
merge_a3m_in_directory(directory, output_directory=None)
```

Behavior:

- Scans `DIRECTORY` for `*.a3m` files.
- Assumes all A3M files are for the same query sequence.
- Infers the source database from each filename by removing `hits_` or `_hits` and treating the remaining stem as an MSA source enum value.
- Defaults an unrecognized filename source to `uniref90` with a warning.
- Writes `expected_basename(query_sequence)` to `--output-directory` or to the input directory when no output directory is supplied.

## `.aligned.pqt` Schema

Required columns:

| Column | Type | Constraints |
| --- | --- | --- |
| `sequence` | string | A3M-style aligned sequence. All rows must have the same aligned length after counting uppercase letters and `-`. |
| `source_database` | string | Must be a recognized Chai source. Strict default sources include `query`, `uniprot`, `uniref90`, `bfd_uniclust`, and `mgnify`. Chai also defines additional enum values such as `BFD`, `paired`, `main`, `singleton`, `pdb70`, `uniprot_n3`, `uniref90_n3`, and `mgnify_n3`. |
| `pairing_key` | string | Empty string for unpaired rows; matching non-empty strings can pair rows across chain MSAs. |
| `comment` | string | Free text ignored by the model. |

Required row convention:

- Row 0 must have `source_database == "query"`.
- There should be exactly one `query` row.
- Filename should be `sha256(query_sequence.upper()).aligned.pqt`.

Python helpers:

```python
from chai_lab.data.parsing.msas.aligned_pqt import (
    expected_basename,
    merge_a3m_in_directory,
    parse_aligned_pqt_to_msa_context,
)
```

Helper semantics:

- `expected_basename(query_sequence)` returns the Chai filename for a query sequence after uppercasing it.
- `parse_aligned_pqt_to_msa_context(path, quota_sizes=...)` validates the parquet schema, requires the first row to be `query`, applies per-source quotas by default, tokenizes A3M insertions/deletions, and returns an `MSAContext`.
- Lowercase A3M letters are insertion characters; they are not aligned positions but they increment deletion counts before the next aligned residue.

## MSA Source Values

Chai default MSA sources are:

```text
query
uniprot
uniref90
bfd_uniclust
mgnify
```

Additional enum values exist for internal/server/generated contexts:

```text
BFD
paired
main
singleton
none
pdb70
uniprot_n3
uniref90_n3
mgnify_n3
```

Prefer the default sources for hand-authored `.aligned.pqt` files unless you are deliberately matching Chai internals.

## Template m8 Schema

Chai parses a tab-delimited m8 file with no header and these columns:

| Position | Column | Notes |
| --- | --- | --- |
| 1 | `query_id` | Local template lookup should match the protein FASTA entity name. Server-generated lookup uses sequence hashes. |
| 2 | `subject_id` | Split as `pdb_identifier_chain`, for example `7WCU_A`. |
| 3 | `pident` | Percent identity; preserved from upstream search. |
| 4 | `length` | Alignment length. |
| 5 | `mismatch` | Mismatch count. |
| 6 | `gapopen` | Gap-open count. |
| 7 | `query_start` | 1-indexed in the input. |
| 8 | `query_end` | End coordinate in the input convention. |
| 9 | `subject_start` | 1-indexed in the input. |
| 10 | `subject_end` | End coordinate in the input convention. |
| 11 | `evalue` | Used for sorting within each `query_id`. |
| 12 | `bitscore` | Preserved from upstream search. |
| 13 | `comment` | Free text/comment field. |

Python helper:

```python
from chai_lab.data.parsing.templates.m8 import parse_m8_file
parse_m8_file(Path("templates.m8"))
```

Template-loading notes:

- Local template query matching uses `chain.entity_data.entity_name`.
- Server template query matching uses `hash_sequence(chain.entity_data.sequence)` because server template hits are remapped to sequence hashes.
- Template CIFs are loaded from RCSB or from the cache folder controlled by `CHAI_TEMPLATE_CIF_FOLDER`.
- Custom CIF filenames must match `$CHAI_TEMPLATE_CIF_FOLDER/identifier.cif.gz`, where `identifier` is the PDB identifier part of `subject_id`.
- Template loading requires `kalign` on `PATH`; missing `kalign>=3.3` can prevent template alignment.

## Bundled Helper Script Contracts

`validate_aligned_pqt.py`:

```bash
python scripts/validate_aligned_pqt.py msas/*.aligned.pqt
python scripts/validate_aligned_pqt.py --json msas/*.aligned.pqt
python scripts/validate_aligned_pqt.py --allow-internal-sources msas/*.aligned.pqt
```

- Requires `pandas` and a parquet engine available in the active Chai environment.
- Does not import model weights, run CUDA, call servers, or execute folding.
- Exit code is non-zero when any file has validation errors.

`stage_colabfold_outputs.py`:

```bash
python scripts/stage_colabfold_outputs.py COLABFOLD_OUT_DIR CHAI_DIR
```

- Reads local files only.
- Writes a Chai-ready folder per `sequences.csv` id.
- Preserves ColabFold paired rows as matching `pairing_key` row indices.
- Rewrites `pdb70.m8` query IDs from ColabFold numeric query ids to Chai FASTA entity names.
