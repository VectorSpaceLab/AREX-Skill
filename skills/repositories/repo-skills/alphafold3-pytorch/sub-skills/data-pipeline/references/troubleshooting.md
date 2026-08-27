# Data-pipeline troubleshooting

Use the symptom, boundary, and stop action below. A missing optional feature
is a valid fallback only when it is recorded as such; it is not a successful
verification of an external database or biological coverage.

## Structure and mmCIF failures

### `Either an mmCIF file or a Biomolecule object must be provided`

`PDBInput` received neither `mmcif_filepath` nor `biomol`. Supply exactly one.
If a filepath is supplied, verify it exists and ends in `.cif` or `.cif.gz`.
Do not rename a PDB, CIF, or arbitrary text file merely to satisfy the suffix
check.

### `mmCIF file ... must have a .cif or .cif.gz file extension`

The constructor is intentionally strict. Preserve the real compression state,
then use `.cif` for plain text or `.cif.gz` for gzip. The parser reads gzip by
content detection, but the `PDBInput` constructor still checks the suffix.

### `No complex chains found`, parse errors, or sequence-length mismatch

The parser requires usable entity/sequence/component loops and processes only
the first model. Inspect the parse result's `errors` before conversion. Check
for missing `_pdbx_poly_seq_scheme`, component records, malformed unequal loop
columns, an absent first model, unsupported insertion numbering, or a
structure containing only non-complex material. For an arbitrary mmCIF, try
explicit author/internal chain and residue semantics only as a documented
choice; never silently rewrite residue IDs.

If assembly metadata is missing, `get_assembly` returns the input biomolecule
with a warning. That is a valid parse result but not proof that the input is a
biological assembly. Record `assembly=unexpanded` and check chain count and
coordinates manually.

### A filtered structure writes no output

The curation scripts intentionally skip a target when a date, resolution,
chain/token, experiment, clash, CCD, or cleanup rule rejects it, or when every
chain is marked for removal. Check the script's prefilter and removal sets
rather than treating no output as a filesystem error. The filter scripts also
require paired assembly/asymmetric files; a missing pair is skipped before
processing.

### Output mmCIF is malformed or a writer fails after cropping

`write_mmcif` expects positions for observed atoms only. Confirm
`sampled_atom_positions.shape == biomol.atom_positions[atom_mask].shape` and,
if supplied, that B-factors have the same masked shape. Cropping changes the
structure; writing from an original filepath may reconstruct a different
assembly and fail. Write from the matching parsed/cropped biomolecule, use a
new output path, and inspect the output before replacing any source. Treat a
partial file as untrusted.

## CCD and molecule conversion

### Missing `components_smiles.json` / canonical ligand failure

The package's input module loads `data/ccd_data/components_smiles.json` at
import. If that file is absent but `components.cif` exists, import can spend
minutes building and writing the cache. If neither exists, canonical ligand
molecule extraction fails. Stage the CCD assets in advance, avoid importing
just for a read-only check, and do not claim ligand support until the exact CCD
snapshot is available.

### Unknown/modified residue or atom errors

The parser preserves chemical components and missing residues. During input
conversion, modified polymer residues may be treated as atomized modified
molecules, while ligands are resolved through CCD SMILES. Check the `chemid`,
chemical component type, missing atom mask, and atom count before blaming the
model. A malformed component, absent CCD atom name, or zero observed atoms is
a data issue. Route generic `Alphafold3Input` construction and ligand/metal
representation details to `input-representation`.

## MSA symptoms

### “Dummy MSA” or query-only fallback

This is expected when the directory is absent, no chain-specific glob matches,
an A3M cannot parse, or no query row has the expected length. Check the exact
ordinary pattern `<file_id><chain>_*.a3m*`, the distillation pattern under
`<pdb-id>_*/a3m*`, gzip content, FASTA headers, and the first sequence length.
A valid file for a different chain or assembly does not satisfy the query.
Record `query-only` and continue only if the experiment explicitly allows
that reduced feature set.

### MSA row or token shape assertion

The structure sequence excludes ligand atoms from the polymer MSA, while the
final token representation may atomize ligands and modified residues. Verify
that the loader's query length matches the chain's polymer residue sequence,
then verify that the final `msa` token axis matches the biomolecule token axis
after ligand insertion and crop masking. Apply the crop mask to `msa`,
`additional_msa_feats`, and `additional_token_feats` together. Do not pad an
incompatible MSA by hand.

### Too few or too many MSA rows

`max_msas_per_chain` is a row cap distributed across matching files. A cap of
one intentionally leaves the query row. If `max_num_msa_tokens` is exceeded,
`PDBInput` deliberately sets the MSA directory aside and installs query-only
features. Lower the cap or raise the budget only after checking memory and
model dimensions. Use normal truncation for reproducible preprocessing; the
lower-level random truncation option is stochastic.

### Incorrect paired MSA

Pairing uses species identifiers, excludes the target marker `-1`, skips
species found in only one chain, and skips species with more than 100 sequences.
Ordinary and distillation headers use different identifier conventions. Check
whether the headers are tab-separated or UniProt-style and whether the correct
`distillation` mode was set. If pairing raises, the loader continues with
unpaired features; log the fallback and inspect species IDs rather than
assuming a biological pairing.

## Template and Kalign symptoms

### No templates or a false template mask

Check the ordinary M8 pattern `<file_id><chain>_*.m8`, the distillation HHR
pattern `<pdb-id>_*/hhr/*.hhr`, the local template mmCIF tree, and the chain
encoded by each hit. Candidates are filtered for query self-hits, identity
strictly inside `(0.3, 0.95)`, positive alignment length, and a template span
of at least ten positions. A missing local structure or a newer release than
the cutoff is skipped. The result can be a valid zero/dummy template tensor.
Record `missing`, `candidate-filtered`, or `cutoff-filtered` separately.

### Template cutoff rejects everything

Ordinary training uses query release minus 60 days; distillation training uses
`2018-04-30`; inference uses `2021-01-12`. Check the structure release date,
template release date, and whether training/inference flags were passed as
intended. The date is a local filter, not a fetch policy.

### `Kalign binary not found`, short-sequence error, or alignment error

Pass an existing local executable through `kalign_binary_path`. Kalign
requires every sequence to be at least six residues long. The realignment
wrapper requires at least 10% matching residues relative to the shorter
sequence and converts process failures into a template alignment error. Test
the executable and input lengths outside a production run. If no local binary
is approved, accept dummy template features or omit templates; do not download
or compile a tool inside this data-pipeline operation.

A missing Kalign path normally causes dummy template features because the
feature constructor skips alignment when the path is absent. `raise_missing`
strictness is a lower-level option and is not the normal directory-loader
behavior.

## Crop and dataset errors

### Invalid crop configuration

The keys must be exactly `contiguous_weight`, `spatial_weight`,
`spatial_interface_weight`, and `n_res`; the three weights must sum to `1.0`
and `n_res > 0`. Training also requires `chains`. Remember that when both
chains are absent, the crop implementation only uses contiguous cropping;
when one chain is selected, interface weight is ignored. A crop size is in
model tokens, not raw residues.

### “No valid mmCIFs / PDBs found”

Confirm the folder exists, is a directory, contains recursive `.cif*` files,
and that the basename IDs survive any sampler/filter selection. With a
sampler, every retained ID must occur in the chain/interface mapping. With
`sample_only_pdb_ids`, ensure at least one retained mapping row has nonzero
sampling mass and a corresponding file.

### Sampler returns a missing PDB or retries exhaust

Compare `sampler.mappings.pdb_id` with the actual file stems, including
`-assembly1`. Check that `filter_out_pdb_ids`, `sample_only_pdb_ids`, and
`pdb_ids_to_keep/skip` were applied to the same ID convention. A missing file
is warned and retried by `PDBDataset.__getitem__` up to 50 attempts; repeated
failure means the layout or mapping must be corrected.

### Clustered sampling is slow or fails

`cluster_based_sample` is explicitly slower than ordinary weighted sampling
and needs enough unique clusters for the requested batch. It samples a cluster
then a row inside it. Use ordinary sampling for a bounded smoke plan, or
reduce the requested cluster-based batch only after checking that changing the
sampling policy is acceptable.

### Sampler weight or mapping error

Verify the exact CSV headers, molecule prefixes (`protein`, `peptide`, `rna`,
`dna`, `ligand`), finite alpha/beta values, nonempty rows, and a positive
cluster size. The sampler normalizes after combining chain and interface rows;
never pre-normalize per file and assume the global distribution is unchanged.
Do not run clustering to repair a missing map during a local preflight.

## Curation and resource failures

### Date or split leakage concern

Use the split-specific inclusive boundaries: training through `2021-09-30`,
validation `2021-10-01` through `2023-01-13`, and evaluation `2023-01-14`
through `2024-04-30`. Validation uses `<=4.5 Å` and `<=2048` tokens; evaluation
uses `<4.5 Å` and `<5120` tokens and excludes NMR. Training's actual script
call uses at most 1000 polymer chains despite its header describing 300. Keep
the chosen policy in the manifest.

### Storage, network, or worker risk

The full PDB acquisition can require up to 700 GB; filtered and clustering
archives are still tens of GB. Stop if capacity, credentials, network access,
worker allocation, or resume semantics are not approved. Filtering and
clustering scripts spawn workers, invoke external tools, write caches and
mmCIFs, and can leave partial outputs. The distillation shell script uses
network downloads and recursive object-storage copy. None belong in a safe
layout check.

### Wrong clustering flag

`--clustering_filtered_pdb_dataset` assumes filtered PDB chains have strict
one-based residue IDs. Do not pass it for arbitrary or AFDB mmCIFs merely
because their files are called “filtered”. If provenance is uncertain, stop
and use the slower general indexing path after a separate approved plan.

## Minimal recovery sequence

1. Run `validate_data_layout.py --help` and then an explicit, read-only
   preflight from an arbitrary CWD.
2. Correct paths, suffixes, headers, dates, crop values, and ID conventions.
3. Parse one small local structure only if the task explicitly allows package
   execution; capture whether assembly expansion succeeded.
4. Add one MSA or template chain at a time, recording query-only/dummy and
   Kalign/cutoff outcomes.
5. Test a single `PDBInput` conversion with a bounded crop before constructing
   a dataset or sampler.
6. Do not proceed to filtering, clustering, acquisition, worker execution,
   writing, or training until the resource and overwrite plan is approved.
