# Enumeration Workflow

REINVENT4 enumeration is a CLI run mode for enumerating masked peptide templates against an amino-acid library, then scoring each enumerated peptide with a standard REINVENT4 scoring block.

## CLI Shape

```bash
reinvent [--config-format toml|json|yaml] [--device cpu|cuda:0] [--seed 123] \
  [--log-filename enumeration.log] [--log-level info] enumeration.toml
```

Useful flags:

- `FILE`: positional path to the config file.
- `--config-format`: force `toml`, `json`, or `yaml` if extension inference is not enough.
- `--device`: use `cpu` for portable checks; scoring components that depend on neural models may still use the selected PyTorch device.
- `--seed`: set runtime seeds for reproducibility where the called components use random state.
- `--log-filename`: write logs to a file instead of stderr.
- `--log-level`: choose the logging verbosity.
- `--dotenv-filename`: load environment variables needed by scoring plugins.
- `--enable-rdkit-log-levels`: expose RDKit logs while debugging chemistry issues.
- `--version`: print the installed REINVENT4 version.

`reinvent_datapre` is a separate preprocessing CLI; it does not run enumeration.

## Minimal Config Shape

```toml
run_type = "enumeration"
device = "cpu"
json_out_config = "enumeration.resolved.json"

[parameters]
smiles_file = "peptides.smi"
amino_acid_library_file = "amino_acids.csv"
aa_names_column = "Name"
smiles_column = "SMILES"
batch_size = 20
output_csv = "peptide_enumeration.csv"

[scoring]
type = "geometric_mean"

[[scoring.component]]
[scoring.component.QED]
[[scoring.component.QED.endpoint]]
name = "QED"
weight = 1.0
```

Runtime-safe `[parameters]` keys:

| Key | Role |
| --- | --- |
| `smiles_file` | Template peptide seed file. Each non-comment row is read from the first column. |
| `amino_acid_library_file` | CSV file containing amino-acid names and fragment SMILES. |
| `aa_names_column` | Amino-acid name column in the library CSV. Default is `Name`. |
| `smiles_column` | Amino-acid fragment SMILES column in the library CSV. Default is `SMILES`; do not use `RDKit_SMILES (REINVENT)`. |
| `batch_size` | Number of combinations processed per loop. Runtime default is `100`; use small values for smoke checks. |
| `output_csv` | CSV destination. Runtime default is `score_results.csv`; explicit paths are safer. |

Some older examples use `amino_acid_library` and `amino_acid_name_column`. Current validation is strict and expects `amino_acid_library_file` and `aa_names_column`, so update those keys before running.

## Peptide Enumeration Semantics

- The peptide template file uses CHUCKLES-like fragments separated by `|`.
- `?` marks masked amino-acid slots to enumerate.
- Current peptide enumeration requires at least one mask and supports at most two masked positions in the first parsed template.
- The enumerator forms the Cartesian product of library amino-acid names repeated by the mask count.
- Each selected amino-acid library SMILES has its trailing character removed before insertion, mirroring PepInvent-style fragment output.
- The filled peptide is converted with RDKit and invalid molecules can be marked invalid by downstream validation.
- The runtime scores the completed peptide SMILES and passes fragmented amino-acid context to the scoring function.

For a library with `N` unique amino-acid names and `M` masks, the maximum number of combinations is `N ** M`. Keep `batch_size` smaller than the total if you want incremental writes and easier failure isolation.

## Scoring Block Reuse

Enumeration always uses a `[scoring]` block. Keep this block structurally identical to scoring-only and staged-learning scoring blocks:

```toml
[scoring]
type = "geometric_mean"
parallel = false

[[scoring.component]]
[scoring.component.MolecularWeight]
[[scoring.component.MolecularWeight.endpoint]]
name = "MW"
weight = 1.0
transform.type = "sigmoid"
transform.low = 300
transform.high = 500
transform.k = 0.5
```

Use the sibling `scoring` sub-skill for component choice, endpoint parameters, transforms, external processes, custom plugins, and optional dependency issues. Enumeration-specific review should only verify that a `[scoring]` mapping exists, has a valid aggregation `type`, and is appropriate for completed peptide SMILES.

## Output CSV Expectations

A successful enumeration writes a CSV with:

- `SMILES`: completed peptide SMILES with no `?` masks remaining.
- `Amino_Acids`: the library names or generated filler representation used for the row.
- `Score`: aggregate score from the scoring block.
- Additional endpoint score and raw columns from the scoring components.

Output is appended in batches. On the first batch the runtime writes a header; later batches append rows without rewriting the header. Before rerunning, delete or rename a previous `output_csv` unless appending is intentional.

## Safe Preflight

Use the bundled helper before launching a job:

```bash
python sub-skills/enumeration/scripts/validate_seed_files.py enumeration.toml --kind enumeration
```

For seed files used by sampling workflows, call the same helper directly:

```bash
python sub-skills/enumeration/scripts/validate_seed_files.py scaffolds.smi --kind scaffolds
python sub-skills/enumeration/scripts/validate_seed_files.py warheads.smi --kind warheads
python sub-skills/enumeration/scripts/validate_seed_files.py mol2mol.smi --kind mol2mol
python sub-skills/enumeration/scripts/validate_seed_files.py pepinvent.smi --kind pepinvent
```

The helper is read-only. It parses files, checks key/column/attachment-point shape, and optionally uses RDKit if installed; it does not call `reinvent`, run scoring, generate molecules, or write outputs.
