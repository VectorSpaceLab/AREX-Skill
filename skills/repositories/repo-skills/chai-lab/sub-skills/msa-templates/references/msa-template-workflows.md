# MSA and Template Workflows

This reference is self-contained for Chai Lab version 0.6.1. It assumes Chai is installed with either `pip install chai_lab==0.6.1` or an equivalent git install that exposes the `chai_lab` Python package and `chai-lab` CLI.

## Choose an MSA Strategy

Chai can fold without MSAs, but local or server-generated MSAs often improve protein predictions. Choose exactly one MSA route per fold:

| Route | Use when | Chai input |
| --- | --- | --- |
| No MSA | You want single-sequence mode or the input has no proteins. | Do not pass `--msa-directory` or `--use-msa-server`. |
| Local `.aligned.pqt` | You already have MSAs, staged ColabFold outputs, or reproducibility requirements. | `chai-lab fold input.fasta out --msa-directory msas/` or `run_inference(..., msa_directory=Path("msas"))`. |
| ColabFold server | You can accept network calls to a shared/default or private ColabFold MMseqs2 server. | `chai-lab fold --use-msa-server [--msa-server-url URL] input.fasta out` or `run_inference(..., use_msa_server=True)`. |

Do not combine local and server MSAs. Chai asserts that `use_msa_server` and `msa_directory` are not both set.

## Local `.aligned.pqt` Directories

A local MSA directory contains one parquet file per unique protein sequence. Chai derives the filename from the uppercased query sequence:

```text
sha256(uppercased_query_sequence).aligned.pqt
```

Each `.aligned.pqt` is a parquet table with required string columns:

| Column | Meaning |
| --- | --- |
| `sequence` | A3M-style aligned sequence. Uppercase letters and `-` define aligned positions; lowercase letters are insertions and are counted in deletion features but ignored as aligned residues. |
| `source_database` | Source label featurized by Chai. Use `query` for the first row; common MSA sources are `uniref90`, `uniprot`, `bfd_uniclust`, and `mgnify`. |
| `pairing_key` | String key for pairing rows across chains in a complex. Rows with the same non-empty key can be paired across different chain MSAs. Use an empty string for unpaired rows. |
| `comment` | Human-readable metadata ignored by Chai. |

Rules that matter before inference:

1. The first row must be the unique query row with `source_database == "query"`.
2. The query row sequence should match one protein sequence in the input FASTA after uppercasing and ignoring A3M insertions.
3. Every row should have the same aligned length as the query when counting only uppercase residues and `-` gap characters.
4. The file basename must be the expected SHA-256 hash so `msa_directory` lookup can find it.
5. Missing local MSAs do not crash immediately; Chai logs a warning and creates a single-sequence MSA for that protein. Validate names proactively if you expected MSA coverage.

Validate local files before folding:

```bash
python scripts/validate_aligned_pqt.py msas/*.aligned.pqt
```

Use `--json` when another tool needs machine-readable validation results.

## Convert A3M Files to `.aligned.pqt`

Use the Chai CLI when a directory contains A3M files for a single query sequence:

```bash
chai-lab a3m-to-pqt path/to/a3m_dir --output-directory path/to/msas
```

Input expectations:

- The command scans `*.a3m` files in the directory.
- All A3M files in one invocation must share the same first query sequence.
- Filenames drive source inference. Names such as `hits_uniref90.a3m`, `hits_uniprot.a3m`, `hits_mgnify.a3m`, or `hits_bfd_uniclust.a3m` map cleanly to Chai MSA sources.
- If the source cannot be inferred from the filename, Chai defaults to `uniref90` and logs a warning.
- Pairing keys are inserted only for UniProt-style sources by default. If pairing needs a different biological grouping, build the `.aligned.pqt` explicitly rather than relying on the generic converter.

After conversion, run the bundled validator on the output parquet. The validator catches mismatched aligned lengths, a non-query first row, invalid source labels, and incorrect filename hashes.

## Preserve Pairing Across Chains

`pairing_key` controls multimer pairing. Chai pairs MSA rows across different chain-specific `.aligned.pqt` files when the keys match. Use this intentionally:

- Leave `pairing_key` empty for unpaired single-chain hits.
- Use matching species, taxonomy, or another consistent identifier when rows should pair across chains.
- Avoid using arbitrary row numbers unless the upstream tool already emitted paired rows in the same order. Chai's ColabFold staging route uses row indices for paired ColabFold rows because ColabFold already performed the pairing.
- Preserve the first query row with an empty `pairing_key`; the query row is not a paired hit.

## Use the ColabFold MSA and Template Server

The server route triggers network work during feature preparation:

```bash
chai-lab fold --use-msa-server --use-templates-server input.fasta output_dir
```

For a private server:

```bash
chai-lab fold --use-msa-server --msa-server-url "https://your-colabfold-server.example" input.fasta output_dir
```

Behavior to know:

- The default URL is `https://api.colabfold.com`.
- Server MSAs are written under `output_dir/msas`; Chai requires that directory to be newly created and empty.
- `--use-templates-server` only makes sense with `--use-msa-server`; server template hits are written as `output_dir/msas/all_chain_templates.m8`.
- Chai server-generated template query IDs use sequence hashes internally; local template m8 files normally use FASTA entity names instead.
- The public ColabFold service is shared infrastructure. Avoid using it in workflows that require offline reproducibility, credential-free CI, or no external side effects.

## Local Template Hit Files

Use local templates when you already have hits or want to avoid server searches:

```bash
chai-lab fold input.fasta output_dir --template-hits-path templates.m8
```

Do not combine `--use-templates-server` with `--template-hits-path`. Chai asserts that server templates and local template hits are mutually exclusive.

The m8 table is tab-delimited and has no header. Chai reads these columns:

```text
query_id subject_id pident length mismatch gapopen query_start query_end subject_start subject_end evalue bitscore comment
```

Important local-template rules:

- For local `--template-hits-path`, `query_id` must match the protein FASTA entity name Chai sees for that chain.
- For server-generated templates, Chai uses sequence hashes for lookup; do not copy that convention to ordinary local m8 files unless you are deliberately mimicking server output.
- `subject_id` is split as `pdbid_chain`, for example `7WCU_A`.
- `query_start`, `query_end`, `subject_start`, and `subject_end` are read as integers. The m8 file is 1-indexed; Chai converts starts to zero-indexed internally.
- Template loading may download RCSB CIFs. Set `CHAI_TEMPLATE_CIF_FOLDER` to a directory containing or caching template CIFs to control this location.
- Custom CIF files should be named `identifier.cif.gz` under `CHAI_TEMPLATE_CIF_FOLDER`, where `identifier` matches the m8 `subject_id` PDB identifier before the underscore.
- Template alignment uses `kalign`; failures can cause hits to be skipped rather than used.

## Stage Existing ColabFold Outputs for Chai

When a ColabFold run already produced the standard output tree, use the bundled helper to preserve its MSAs, pairing, and template hits:

```bash
python scripts/stage_colabfold_outputs.py colabfold_out_dir chai_inputs
```

Expected ColabFold-like input layout:

```text
colabfold_out_dir/
  sequences.csv
  <id>_pairgreedy/pair.a3m
  <id>_env/uniref.a3m
  <id>_env/bfd.mgnify30.metaeuk30.smag30.a3m
  <id>_env/pdb70.m8
```

The `sequences.csv` file must contain exactly `id,sequence` columns. Multimer sequences are colon-separated in the `sequence` field.

For each `id`, the helper writes:

```text
chai_inputs/<id>/
  chai.fasta
  msas/<hash>.aligned.pqt
  msas/<hash>.aligned.pqt
  all_template_hits.m8
```

Then fold with local inputs:

```bash
chai-lab fold chai_inputs/<id>/chai.fasta out_dir \
  --msa-directory chai_inputs/<id>/msas \
  --template-hits-path chai_inputs/<id>/all_template_hits.m8
```

The helper preserves ColabFold paired rows by using matching row-index pairing keys across chain-specific `.aligned.pqt` files. This differs from asking Chai to call the ColabFold server itself, which may produce different searches or pairing.

## Python API Patterns

Local MSA and template files:

```python
from pathlib import Path
from chai_lab.chai1 import run_inference

candidates = run_inference(
    fasta_file=Path("input.fasta"),
    output_dir=Path("out"),
    msa_directory=Path("msas"),
    template_hits_path=Path("templates.m8"),
    use_msa_server=False,
    use_templates_server=False,
)
```

Server MSAs and templates:

```python
from pathlib import Path
from chai_lab.chai1 import run_inference

candidates = run_inference(
    fasta_file=Path("input.fasta"),
    output_dir=Path("out"),
    use_msa_server=True,
    use_templates_server=True,
    msa_server_url="https://api.colabfold.com",
)
```

For full inference output handling, ranking data, GPU settings, and output directory safety, route to `../cli-inference/SKILL.md`.
