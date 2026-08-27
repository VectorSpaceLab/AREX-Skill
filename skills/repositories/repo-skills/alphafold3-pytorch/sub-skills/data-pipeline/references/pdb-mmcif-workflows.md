# PDB and mmCIF workflows

This reference describes the package's structure-data boundary. It is intentionally
about local parsing, feature preparation, and dataset contracts; it is not a
recipe for downloading or curating a full PDB/AFDB release.

## Choose the input contract first

There are three materially different cases:

- **Curated PDB mmCIF:** a local `.cif`/`.cif.gz` file whose release date,
  assembly choice, residue numbering, CCD coverage, and filtering policy are
  known. `PDBInput` may expand it to the default biological assembly.
- **Arbitrary mmCIF:** a local structure that may lack assembly metadata,
  complete connectivity, strict one-based residue numbering, or the headers
  expected by the curation scripts. Parse it as a structure, and do not claim
  that it is a filtered PDB example.
- **AFDB/PDB distillation:** an AFDB-style local mmCIF plus a tab-separated
  UniProt-to-PDB mapping. This uses the distillation-specific dataset contract
  and searches MSA/template material through the associated PDB IDs; it is not
  equivalent to an ordinary PDB sample.

Before conversion, record whether the operation is training, inference, or
 distillation. Training/validation needs an explicit crop; inference does not
crop in `PDBDataset` and `PDBInput` conversion is allowed to retain the full
structure. Missing MSA/templates are supported fallbacks, not evidence that
those biological features were available.

## `PDBInput` contract

The installed package exposes this dataclass (defaults shown where they are
operationally important):

```text
PDBInput(
  mmcif_filepath=None, biomol=None, chains=(None, None),
  cropping_config=None, msa_dir=None, templates_dir=None,
  add_atom_ids=False, add_atompair_ids=False, directed_bonds=False,
  custom_atoms=None, custom_bonds=None,
  training=None, inference=None, distillation=False,
  distillation_multimer_sampling_ratio=2/3,
  distillation_pdb_ids=None, distillation_template_mmcif_dir=None,
  resolution=None, constraints=None, constraints_ratio=0.1,
  max_msas_per_chain=None, max_num_msa_tokens=None,
  max_templates_per_chain=None, num_templates_per_chain=None,
  max_num_template_tokens=None, max_length=None,
  cutoff_date=None, kalign_binary_path=None,
  extract_atom_feats_fn=..., extract_atompair_feats_fn=...
)
```

Use exactly one of `mmcif_filepath` or `biomol`. A filepath must already
exist and end in `.cif` or `.cif.gz`; other extensions are rejected. `biomol`
is an already constructed `Biomolecule` and bypasses file parsing, but the
same downstream feature and CCD requirements still apply. `chains` is a pair
of chain IDs used by training crops; `None` means no selected chain. An empty
string is treated as a null chain during conversion.

If `cropping_config` is present, its keys must be exactly:

```text
contiguous_weight, spatial_weight, spatial_interface_weight, n_res
```

The three weights must sum exactly to `1.0` in the package constructor and
`n_res` must be positive. Training conversion asserts that a crop config and
chain selection exist. Inference should omit the crop config. `cutoff_date`
is parsed as `%Y-%m-%d` and the structure's release date must not be later
than it. `max_length` is checked before cropping. `max_num_msa_tokens` and
`max_num_template_tokens` can force a feature fallback when the configured
per-chain cap would exceed the total token budget; set those caps deliberately
rather than treating the fallback as a successful search.

## Local conversion sequence

The normal `PDBInput` transform is:

1. Parse the file with `parse_mmcif_object`, or use the supplied `Biomolecule`.
2. For an ordinary PDB file, select the first available assembly from mmCIF
   assembly metadata. A file ID containing `assembly` and a distillation input
   use the parsed structure without another assembly expansion. For a compressed
   PDB filepath, `pdb_input_to_molecule_input` also derives `file_id` with one
   `splitext`, so the file ID includes the `.cif` part; MSA/template filenames
   must follow that exact derived ID or the loader will fall back. If assembly
   metadata is incomplete, the parser warns and the input biomolecule is
   returned rather than inventing an assembly.
3. Read the release date and resolution. A missing distillation release date
   is an error; an explicit `cutoff_date` rejects a later release.
4. Build a one-residue-per-token view for each chain. Ligands and modified
   polymer residues can be atomized, so their atoms become tokens; polymers
   remain residue tokens. CCD SMILES are required for ligand canonicalization.
5. Load MSA and template features before cropping. This is important because
   the crop masks are then applied to the MSA and pairwise template dimensions.
6. During non-inference operation, sample one of the configured crop modes and
   update the biomolecule, chain indices, MSA, token features, and template
   pair dimensions together.
7. Convert through `MoleculeInput` to `AtomInput`; collate with
   `pdb_inputs_to_batched_atom_input` when a model-facing batch is required.

The conversion is bounded by a 60-second per-input timeout in the package.
A timeout or a parse/CCD/crop error should be surfaced and investigated, not
silently retried as proof of a valid example.

## Dataset classes and signatures

### `PDBDataset`

```text
PDBDataset(
  folder,
  sampler=None,
  sample_type="default",
  contiguous_weight=0.2,
  spatial_weight=0.4,
  spatial_interface_weight=0.4,
  crop_size=384,
  training=None, inference=None,
  filter_out_pdb_ids=None, sample_only_pdb_ids=None,
  return_atom_inputs=False,
  **pdb_input_kwargs
)
```

`folder` must be an existing directory. The class recursively collects files
matching `*.cif*`; it applies Python's single `os.path.splitext` to each
basename, so `foo.cif` becomes ID `foo` but `foo.cif.gz` becomes ID `foo.cif`.
This compressed-file quirk can prevent sampler matching; use plain `.cif` in
curated dataset trees or make the mapping use the exact derived ID. If a
`WeightedPDBSampler` is supplied, only IDs present in its `pdb_id` mapping are
retained. `filter_out_pdb_ids` and `sample_only_pdb_ids` are applied to
the unsampled file set, or are checked against sampler IDs when a sampler is
present; contradictory sampler/filter sets raise an assertion.

Without a sampler, integer indexing follows the collected file mapping. With a
sampler, `get_item` samples a chain or interface tuple from `sample()` by
default, or `cluster_based_sample()` when `sample_type="clustered"`. The
selected tuple becomes `PDBInput.chains=(chain_id_1, chain_id_2)`. The dataset
installs a crop config from the three weights and `crop_size`; it removes that
config when `inference=True`. `return_atom_inputs=True` immediately performs
the expensive local conversion. `__getitem__` retries a missing file/result
up to `max_attempts` (default 50), so a persistent broken layout should be
fixed rather than hidden by retries.

### `PDBDistillationDataset`

```text
PDBDistillationDataset(
  folder,
  contiguous_weight=0.2,
  spatial_weight=0.4,
  spatial_interface_weight=0.4,
  crop_size=384,
  training=None, inference=None,
  filter_out_pdb_ids=None, sample_only_pdb_ids=None,
  return_atom_inputs=False,
  multimer_sampling_ratio=2/3,
  uniprot_to_pdb_id_mapping_filepath=None,
  **pdb_input_kwargs
)
```

The mapping filepath is required in practice. It is read as tab-separated
rows with three fields (UniProt accession, database column, PDB ID); the
middle database field is dropped. The dataset applies one `splitext` to each
local mmCIF basename and then takes the second hyphen-separated field as the
UniProt accession (the checked-in AFDB naming pattern is for example
`AF-P01112-F1-model_v4.cif.gz`). A differently named AFDB file can therefore
fail before biological parsing. The dataset keeps local mmCIF basenames whose
accession part is present in that mapping. Each mapped PDB ID is normalized to
lowercase plus `-assembly1` and passed as
`PDBInput.distillation_pdb_ids`. The returned input sets `distillation=True`
and carries the configured multimer ratio. With more than one chain, the
conversion samples a chain pair with probability `2/3` by default and a
single chain otherwise; this is stochastic and must not be described as a
fixed deterministic selection. The same crop, inference, filtering, and
50-attempt retry behavior as `PDBDataset` applies, but the class has no
weighted sampler argument.

## mmCIF parsing and assembly behavior

`mmcif_parsing.parse` consumes an mmCIF string and returns `ParsingResult`:
`mmcif_object` is an `MmcifObject` or `None`, and `errors` maps `(file_id,
chain_id)` to caught errors. It can use author or internal chain/residue IDs;
the default is author IDs. It constructs a first-model Biopython structure,
chain sequences, missing-residue positions, chemical components, entity/chain
mappings, release/resolution header values, raw parsed metadata, and
`struct_conn` bonds. Only model 1 is processed. A file with no complex chains
or a malformed loop returns an error result when the default catch-all mode is
used. `parse_mmcif_object` reads plain or gzip-compressed files and raises the
first parse error instead of returning an empty object.

The parser preserves missing SEQRES positions and distinguishes non-polymer
components, waters, and polymers. Author residue numbering is not required to
be integer-like in mmCIF generally, but this implementation converts the
used author sequence number to `int`; insertion-code or inconsistent residue
fixtures may therefore fail during biomolecule conversion. Treat such failures
as input incompatibility, not as permission to relabel a structure silently.

`get_assembly` reads `_pdbx_struct_assembly`, assembly-generation, and
operation metadata. If any required category is absent, it warns and returns
the input biomolecule. Otherwise the lowest sorted assembly ID is the default;
an explicit unknown ID raises `KeyError`. Operation expressions are expanded
and coordinate transforms are applied to the selected asym IDs. Assembly
choice changes chain count and coordinates, so record the file ID and chosen
assembly semantics in an experiment manifest.

## mmCIF writing and safe boundaries

The package writer is an output-producing operation, not a validator:

```text
write_mmcif_from_filepath_and_id(input_filepath, output_filepath, file_id, **kwargs)
write_mmcif(
  mmcif_object, output_filepath,
  gapless_poly_seq=True,
  insert_orig_atom_names=True,
  insert_alphafold_mmcif_metadata=True,
  sampled_atom_positions=None, b_factors=None
)
```

The writer parses the input, chooses its assembly, optionally replaces only
masked/observed atom positions, converts through `Biomolecule`, and writes an
mmCIF string. `sampled_atom_positions` must have shape equal to the flattened
observed-atom positions; supplied B-factors must match the same mask. It may
write a file and can fail after creating a partial output, so do not call it
from the safe layout validator. Cropped structures may not be compatible with
writing directly from the original filepath; write from the matching parsed
/cropped biomolecule instead and check the output locally before publication.

`pdb_dataset_to_atom_inputs` is also a mutating, parallel conversion helper:
it chooses a random permutation of dataset indices by default, creates an
`<dataset-stem>.atom-inputs` directory when no output is supplied, writes
`<index>.pt` files, and can return an `AtomDataset`. It accepts `n_jobs` and
`overwrite_existing`. It is reference-only for planning; never imply that
`validate_data_layout.py` performs this conversion.

## CCD preflight

The package's input module looks for `data/ccd_data/components_smiles.json`
at import time. If absent but `components.cif` exists, it reads the CCD and
writes the JSON cache; if neither is available, ligand canonicalization fails
with a missing-CCD message. The repository fixture includes the JSON cache,
but a portable deployment should pass or stage the required CCD assets using
an explicit resource plan. Do not import the package merely to check a path
when that import-side cache creation would be unacceptable.
