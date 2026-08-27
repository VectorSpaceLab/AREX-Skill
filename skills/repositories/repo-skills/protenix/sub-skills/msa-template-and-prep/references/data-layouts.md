# Protenix MSA, Template, RNA, and Search Data Layouts

## Inference Protein MSA Directory

A Protenix protein MSA directory should contain at least one useful protein MSA file and usually both paired and unpaired files:

```text
<msa-dir>/
  pairing.a3m
  non_pairing.a3m
  hmmsearch.a3m
```

Expected use:

- `pairing.a3m` is referenced by `proteinChain.pairedMsaPath`.
- `non_pairing.a3m` is referenced by `proteinChain.unpairedMsaPath`.
- `hmmsearch.a3m` is referenced by `proteinChain.templatesPath` when template search uses HMMER output.
- `hmmsearch.a3m` is optional for MSA-only inference and expected after `protenix mt` or `protenix prep` with templates.

A3M minimum checks:

- The file should contain FASTA-like header lines starting with `>` and sequence lines after headers.
- The first entry is typically `>query` followed by the query sequence.
- Uppercase letters and `-` are aligned columns; lowercase letters are insertions and are normal in A3M.
- Empty files, header-only files, and mismatched aligned-column lengths are not useful for prediction or template search.

## Pairing Header Requirements

Protenix uses taxonomy/species cues in paired MSA headers to support multimer pairing. Supported patterns include:

```text
>UniRef100_<hit-name>_<taxonomy-id>/
>tr|ACCESSION|ID_SPECIES/START-END ... OX=TaxonomyID ...
>sp|ACCESSION|ID_SPECIES/START-END ... OX=TaxonomyID ...
```

Practical implications:

- A `pairing.a3m` containing only `>query` is a dummy paired MSA. It can keep path plumbing working but does not provide real paired evolutionary information.
- Raw ColabFold A3M headers may not include taxonomy-like identifiers Protenix expects for paired-chain species matching.
- For multimer pairing problems, inspect `pairing.a3m` first; `non_pairing.a3m` alone cannot supply paired-chain species matching.
- `non_pairing.a3m` may still be useful for single-chain or unpaired evolutionary features.

## JSON Path Fields

This sub-skill owns path semantics, not the full Protenix JSON schema.

Protein path fields:

```json
{
  "proteinChain": {
    "sequence": "...",
    "pairedMsaPath": "path/to/pairing.a3m",
    "unpairedMsaPath": "path/to/non_pairing.a3m",
    "templatesPath": "path/to/hmmsearch.a3m"
  }
}
```

RNA path field:

```json
{
  "rnaSequence": {
    "sequence": "...",
    "unpairedMsaPath": "path/to/rna_msa.a3m"
  }
}
```

Legacy protein field conversion:

```json
{
  "proteinChain": {
    "msa": {
      "precomputed_msa_dir": "path/to/dir-with-pairing-and-non-pairing"
    }
  }
}
```

`update_infer_json` converts the legacy `msa.precomputed_msa_dir` form to `pairedMsaPath` and `unpairedMsaPath` when the referenced files exist. Route detailed JSON entity authoring and validation to `../../input-data-and-features/SKILL.md`.

## Search Output Roots

For a JSON task named `my_task`, Protenix writes stage outputs under the requested output directory:

```text
<out-dir>/
  my_task/
    msa/
      0/
        pairing.a3m
        non_pairing.a3m
        hmmsearch.a3m
      1/
        pairing.a3m
        non_pairing.a3m
    rna_msa/
      2/
        rna_msa.a3m
```

Notes:

- Protein MSA subdirectory indexes are assigned after sorting pending protein sequences, not necessarily input-chain order.
- RNA MSA subdirectory indexes use the sequence index in the JSON `sequences` list.
- Template search writes `hmmsearch.a3m` into the same protein MSA directory it used as input.
- JSON update files are written beside the original input JSON, not under the output directory.
- If a chain already points to valid existing paths, Protenix reuses them and may skip that stage.

## Released Training/Inference Data Root

A released Protenix data root has this relevant structure:

```text
<protenix-data-root>/
  common/
    seq_to_pdb_index.json
  mmcif_msa_template/
    0/
      pairing.a3m
      non_pairing.a3m
      hmmsearch.a3m
    1/
      pairing.a3m
      non_pairing.a3m
      hmmsearch.a3m
  rna_msa/
    msas/
      <pdb-entity-id>/
        <pdb-entity-id>_all.a3m
    rna_sequence_to_pdb_chains.json
  search_database/
    pdb_seqres_2022_09_28.fasta
    nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta
    rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta
    rnacentral_active_seq_id_90_cov_80_linclust.fasta
```

Protein mapping:

- `common/seq_to_pdb_index.json` maps exact protein sequence strings to integer MSA directories under `mmcif_msa_template`.
- Each mapped directory should contain `pairing.a3m` and `non_pairing.a3m`; include `hmmsearch.a3m` when template features are expected.

RNA mapping:

- `rna_msa/rna_sequence_to_pdb_chains.json` maps RNA sequence strings to PDB entity ids.
- The corresponding released RNA MSA is under `rna_msa/msas/<pdb-entity-id>/<pdb-entity-id>_all.a3m`.
- A released RNA MSA can be referenced as `rnaSequence.unpairedMsaPath` after validating the file exists.

## Custom Training MSA Layout

For a custom training set, the minimum MSA-related contract is:

```text
<training-data-root>/
  common/
    seq_to_pdb_index.json
  mmcif_msa_template/
    <integer-seq-id>/
      pairing.a3m
      non_pairing.a3m
      hmmsearch.a3m
```

Generation concepts:

- `seq_to_pdb_index.json` must use the exact protein sequence as the key and the integer directory id as the value.
- `pdb_index_to_seq.json` is useful while generating data, but the runtime loader primarily needs `seq_to_pdb_index.json`.
- `seq_to_pdb_id_entity_id.json` connects sequences back to PDB/entity ids for data-specific post-processing.
- Raw `.a3m` search files are not the final layout. They must be taxonomy-annotated where possible and split into `pairing.a3m` and `non_pairing.a3m`.
- `hmmsearch.a3m` is template output, not a replacement for `pairing.a3m` or `non_pairing.a3m`.

## External Tool and Database Layout

Default search database lookup is under the configured Protenix data root in `search_database/`.

Template search database:

```text
search_database/pdb_seqres_2022_09_28.fasta
```

RNA search databases:

```text
search_database/nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta
search_database/rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta
search_database/rnacentral_active_seq_id_90_cov_80_linclust.fasta
```

Required binaries by feature:

- Template search: `hmmsearch`, `hmmbuild`.
- RNA MSA search: `nhmmer`, `hmmalign`, `hmmbuild`.
- Some template downstream parsing/alignment paths may require `kalign` during prediction with templates.
- ColabFold local search: `colabfold_search`, `mmseqs`, and ColabFold/MMseqs databases.
- Training MSA generation: external search/database tooling plus mapping and taxonomy files.

The bundled checker is read-only and does not verify database contents beyond file presence. It intentionally does not download, run HMMER, run MMseqs, import Protenix, or contact an MSA server.

## Layout Checker Usage

Run the checker on any candidate file or root before rerunning expensive preprocessing:

```bash
python sub-skills/msa-template-and-prep/scripts/check_msa_template_layout.py input.json --expect-template --expect-rna
python sub-skills/msa-template-and-prep/scripts/check_msa_template_layout.py msa_dir
python sub-skills/msa-template-and-prep/scripts/check_msa_template_layout.py data_root --sample-limit 10
```

Exit codes:

- `0`: no errors were found.
- `1`: warnings exist and `--strict` was used.
- `2`: at least one error was found.

Use `--json` when another tool needs machine-readable findings.
