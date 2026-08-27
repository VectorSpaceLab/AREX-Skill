# Dataset curation and large-data planning

The repository's PDB/AFDB preparation scripts are production-scale,
networked or mutating procedures. This reference records their contracts and
stop conditions so an operator can plan them without accidentally running a
700-GB acquisition or rewriting a dataset. `scripts/validate_data_layout.py`
is deliberately a read-only substitute for preflight only; it does not
implement filtering, clustering, or downloading.

## Data tiers and directory schemas

The ordinary PDB workflow has two raw structure trees:

```text
<unfiltered_assembly_mmcifs>/<two-character-id>/<pdb>-assembly1.cif
<unfiltered_asym_mmcifs>/<two-character-id>/<pdb>.cif
```

The assembly and asymmetric-unit files are paired by basename and by the
replacement of `-assembly1`. Filtered output is written as:

```text
<split>_mmcifs/<two-character-id>/<pdb>-assembly1.cif
```

The README's example uses `train_mmcifs`, `val_mmcifs`, and `test_mmcifs`.
`PDBDataset` can also read a nested directory with `.cif*` files, but the
curation scripts require the divided two-character layout and ordinary
`.cif` inputs.

CCD-dependent training filtering expects both:

```text
<ccd_dir>/components.cif
<ccd_dir>/chem_comp_model.cif
```

The runtime input path additionally benefits from the local cache
`data/ccd_data/components_smiles.json`. The package may create that cache at
import if a components file is present, so stage it deliberately and do not
use an ordinary package import as a write-free environment probe.

Clustering output is a cache directory, not a runtime structure directory. It
contains JSON sequence/interface caches, per-type chain mapping CSVs, and an
interface mapping CSV. The chain mappings have at least:

```text
pdb_id,chain_id,molecule_id,cluster_id
```

The interface mapping has:

```text
pdb_id,interface_chain_id_1,interface_chain_id_2,
interface_molecule_id_1,interface_molecule_id_2,
interface_chain_cluster_id_1,interface_chain_cluster_id_2,
interface_cluster_id
```

`WeightedPDBSampler` combines those CSVs and normalizes calculated weights;
keep all mapping files from the same clustering run.

AFDB distillation data is a separate tree. The checked-in mapping is a
three-column tab-separated file with UniProt accession, a database column,
and a PDB ID. The download script's intended paths are:

```text
<data>/unfiltered_train_mmcifs/
<data>/data_caches/train/
<data>/data_caches/uniprot_to_pdb_id_mapping.dat
```

The dataset class maps an accession-named local mmCIF to one or more
`<pdb-id>-assembly1` candidates. A mapping file alone is not proof that the
corresponding AFDB mmCIF, MSA, template, or PDB template structure exists.

## Split rules actually encoded by the scripts

The date boundaries below are inclusive because the scripts compare with
`<=` on both ends unless noted otherwise.

### Training

The training filter's prefilter accepts release dates from `1970-01-01`
through `2021-09-30`, resolution at most `9.0 Å`, and at most 1000 polymer
chains in the actual call. It then marks polymer chains with fewer than four
resolved polymer residues for removal. The file header describes a 300-chain
training target, but the implementation explicitly comments that it retains
up to 1000 because the supplement's rationale was unclear. Treat this as a
known source-level discrepancy and record which policy was used; do not write
“300” as though it were enforced by this script.

The post-filter sequence is: remove hydrogens and waters; remove all-unknown
polymer chains; remove clashing chains; optionally remove the ligand exclusion
set; remove atoms outside CCD-defined atom names; remove CCD leaving atoms
from covalent ligands; remove protein chains with sequential C-alpha distance
above `10 Å` (only for chains with at least 10 peptide residues); select the
closest 20 chains for sufficiently large assemblies; and remove
crystallization aids according to the experiment method. A structure is
written only if not all chains are marked for removal.

Clash handling uses a `1.7 Å` neighbor threshold and marks a pair when the
clash count is greater than `30%` of either chain's atom count. The chain with
the larger fraction is removed; ties choose the chain with fewer atoms, then
the larger chain ID. For assemblies over 20 remaining chains, the script
selects a random interface token within `15 Å` of another chain and keeps the
20 closest chains. This step is stochastic and may make repeated curation
outputs differ unless the surrounding run controls randomness.

### Validation

The validation prefilter accepts releases from `2021-10-01` through
`2023-01-13`, at most `2048` tokens, at most `1000` chains, and resolution at
most `4.5 Å`. The later filtering removes hydrogens/waters, removes excluded
ligands unless `--keep_ligands_in_exclusion_set` is passed, and removes
crystallization aids. It does not use the training CCD atom/leave-atom
filtering sequence.

### Evaluation/test

The evaluation prefilter accepts releases from `2023-01-14` through
`2024-04-30`, rejects `NMR` structure methods, requires resolution strictly
better than `4.5 Å`, and requires strictly fewer than `5120` tokens. It then
removes hydrogens/waters, excluded ligands unless explicitly kept, and
crystallization aids. The strict comparisons differ from validation and must
not be collapsed into one generic “4.5 Å/5120” rule.

## Script interfaces and why they stay reference-only

Filtering scripts accept assembly and asymmetric input directories, an output
directory, split-specific date flags, `--skip_existing`, a ligand exclusion
switch, and worker/chunksize flags. Training additionally accepts `--ccd_dir`
and loads the two CCD files. They parse structures, mutate removal sets,
create output directories, and write filtered mmCIFs. Exceptions can cause a
partial output to be removed, but a timeout or process interruption can still
leave an incomplete run that must be audited.

Clustering scripts accept `--mmcif_dir`, an output cache directory, and
`--no_workers`. Validation/test also accept one or two reference clustering
directories. The `--clustering_filtered_pdb_dataset` flag is a structural
assumption: it enables the fast path that assumes each chain's residue IDs
are one-based after filtering. The README warns not to pass it to arbitrary
non-PDB mmCIF data, because interface clustering can then be wrong. The flag
is not a repair or a proof; only the producer's filtering provenance can
justify it.

The clustering run parses every mmCIF, writes sequence FASTA/JSON caches,
invokes MMseqs2 for polymer/peptide homology, groups ligands by CCD code, and
writes CSV mappings. The training policy is 40% protein identity, 100% nucleic
acid identity, 100% short-peptide identity, and exact CCD identity for
ligands, with 0.8 coverage in the MMseqs2 calls. Validation/test add
split-specific low-homology filtering and interface sampling. These are
expensive external workflows, not safe helper commands.

The distillation download shell script installs tools/modules, downloads a
large AFDB Swiss-Prot tar archive, extracts it, and recursively copies an MSA
tree from object storage. The reduction scripts read compressed archives,
filter by a UniProt-to-PDB mapping, create accession output directories, and
rewrite extracted data. They require network/data credentials or very large
local storage and are never invoked by the runtime skill.

## Storage and scale gates

The README warns that acquiring both full PDB mmCIF collections can use up to
700 GB. It describes a preprocessed filtered PDB archive of roughly 25 GB
for about 148k complexes and clustering files of roughly 3 GB for one dated
snapshot. These are planning estimates, not runtime guarantees. Check free
space for raw, temporary, output, and cache copies separately. Do not start a
full acquisition when the available space only covers the final tree.

A safe plan records:

- source snapshot/date and whether assembly and asymmetric trees match;
- expected split boundaries and resolution/token policy;
- CCD version and whether components/model files are present;
- output and cache roots on separate capacity accounting;
- whether a filtered-PDB one-based indexing assumption is justified;
- worker count, wall-time, and timeout policy; and
- a resume strategy that does not mix snapshots or overwrite verified output.

## Safe stop conditions

Stop before any mutating or network step when:

1. an assembly file has no paired asymmetric file, or a structure ID is not a
   four-character/PDB-compatible basename;
2. a required path is absent, points to a file of the wrong extension, or
   resolves to the output tree itself;
3. a release/cutoff date cannot be parsed as `YYYY-MM-DD`, or lower and upper
   dates are reversed;
4. CCD `components.cif`/`chem_comp_model.cif` is missing for training, or the
   CCD version does not match the planned structure snapshot;
5. a filtered-PDB clustering flag is requested for an arbitrary mmCIF tree;
6. mapping CSV headers are incomplete, cluster IDs are mixed across snapshots,
   or the interface mapping references a PDB absent from the structure tree;
7. a structure exceeds the intended token/chain/space budget before parsing;
8. the process times out, is interrupted, or reports a parse/write exception;
   quarantine and inspect partial output instead of silently resuming it; or
9. a proposed action would download, filter, cluster, spawn workers, mutate an
   existing output, or consume training resources when the task only asked
   for local preflight.

Run the bundled validator from an arbitrary working directory with explicit
absolute or project-relative paths. Its success means only that paths,
extensions, mapping headers, dates, and config values are self-consistent;
it does not validate mmCIF syntax, CCD chemistry, homology, biological
assembly correctness, or split leakage.
