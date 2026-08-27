# Weighted PDB sampling and cropping

Weighted sampling is a dataset-selection policy layered above local mmCIF
loading. It does not replace structural validation, cropping, or MSA/template
preflight. The sampler consumes completed cluster mapping CSVs and uses NumPy
random choice; it does not construct clusters.

## Mapping inputs

`WeightedPDBSampler` has this constructor:

```text
WeightedPDBSampler(
  chain_mapping_paths,
  interface_mapping_path,
  batch_size,
  beta_chain=0.5,
  beta_interface=1.0,
  alpha_prot=3.0,
  alpha_nuc=3.0,
  alpha_ligand=1.0,
  pdb_ids_to_skip=None,
  pdb_ids_to_keep=None,
)
```

`chain_mapping_paths` can be one CSV path or a list. Each chain CSV needs
`pdb_id`, `chain_id`, `molecule_id`, and `cluster_id`; the sampler extracts the
molecule type from the prefix of `molecule_id`. Interface mappings need the
chain/interface columns recorded in the curation reference. The sampler
concatenates the chain maps, offsets cluster IDs between multiple chain-map
files, computes chain and interface weights, converts chain rows to
`chain_id_1=<chain_id>, chain_id_2=""`, offsets interface cluster IDs after
chain clusters, and concatenates both row types.

`pdb_ids_to_skip` is applied before weighting. `pdb_ids_to_keep` subsets the
mapping columns to the PDB IDs supplied. An empty or mismatched map is a hard
problem: the sampler cannot infer missing chain/interface rows from mmCIFs.
Keep mapping files and mmCIFs from the same split and snapshot.

## Weight formula

The per-row weight is exactly:

```text
(beta / cluster_size) * (
    alpha_prot * n_prot
  + alpha_nuc * n_nuc
  + alpha_ligand * n_ligand
)
```

For a chain, `n_prot`, `n_nuc`, and `n_ligand` are one-hot counts based on
`protein`/`peptide`, `rna`/`dna`, or `ligand`. For an interface, the counts
are the sums for its two molecule types. `cluster_size` is the number of rows
in the relevant cluster. The constructor uses `beta_chain=0.5`,
`beta_interface=1.0`, and protein/nucleic-acid/ligand alphas `3/3/1` unless
overridden. After both row types are combined, all weights are divided by
their total and passed as a probability vector to NumPy. Thus inverse cluster
size reduces the dominance of large clusters, while molecule-type alphas and
chain/interface betas change the relative mass.

There is no sampler seed parameter. `sample()` is stochastic and samples with
NumPy's default replacement behavior:

```text
sample(batch_size) -> [(pdb_id, chain_id_1, chain_id_2), ...]
```

`cluster_based_sample(batch_size)` first chooses cluster IDs, then chooses a
row inside each cluster using that cluster's normalized row weights. It is
explicitly slower and requires at least as many selectable clusters as the
requested sample. Do not call it as a deterministic balancing guarantee.

`__len__` returns `len(mapping) // batch_size`, while the iterator is an
unbounded generator that repeatedly samples batches and yields PDB IDs. The
mapping is precomputed at construction and can take minutes on a full data
set. A local preflight should inspect paths and headers instead of importing
and constructing the sampler.

## Integrating with `PDBDataset`

Pass the sampler to:

```text
PDBDataset(
  folder=<filtered mmCIF root>,
  sampler=sampler,
  sample_type="default" or "clustered",
  sample_only_pdb_ids=<optional set>,
  contiguous_weight=0.2,
  spatial_weight=0.4,
  spatial_interface_weight=0.4,
  crop_size=384,
  training=True,
  ...
)
```

At construction, `PDBDataset` retains only `.cif*` basenames whose ID is in
`sampler.mappings.pdb_id`. With the default sample type, each `get_item` calls
`sampler.sample(1)`; with `sample_type="clustered"`, it calls
`cluster_based_sample(1)`. The sampled chain IDs are inserted into
`PDBInput.chains`, which controls interface-aware crop selection. If
`sample_only_pdb_ids` is supplied, the dataset repeatedly samples until the
result is in that set. Ensure the set has nonzero sampler mass; an empty or
impossible selection can loop rather than produce a useful diagnostic.

`filter_out_pdb_ids` and `sample_only_pdb_ids` are not silent remappers. When a
sampler is present, their IDs are checked against sampler mappings and
contradictory exclusion/selection assertions can fail. The structure tree
must still contain every sampled file; a mapping row without a file returns a
warning and triggers `PDBDataset.__getitem__` retries.

The trainer configuration layer can construct a sampler from
`train_weighted_sampler` with `chain_mapping_paths` and
`interface_mapping_path`, then passes it as `train_sampler`. Keep that
configuration ownership in `training-configuration`; this reference only
specifies the data-side contract.

## Crop policy

`Biomolecule.crop` samples one of three crop functions using the configured
weights:

- **contiguous:** sequence-contiguous selection across chains;
- **spatial:** select tokens near a sampled reference token; and
- **spatial-interface:** select a reference token that is near another chain,
  then choose spatial neighbors.

With both `chain_1` and `chain_2`, all three weights are eligible. With only
one selected chain, interface weight is forced to zero. With no selected
chain, only the contiguous branch is eligible (the spatial weights are
ignored by the crop implementation). `n_res` is clamped to the biomolecule's
available token count. Spatial tie breaks add a small deterministic index
increment after the random reference choice; the overall crop remains
random.

The standard dataset defaults are `0.2/0.4/0.4` and `crop_size=384`. `PDBInput`
requires the exact four-key config and an exact weight sum of `1.0`; the
validator uses a tight numeric consistency check before the package is
constructed. Training conversion also requires a crop config and chain IDs.
After a crop, the conversion applies the same sorted crop mask to the MSA
residue axis, additional token/MSA features, and both template pair axes. If
these masks are not carried together, the eventual MSA/token or template
shape assertion is the useful failure signal.

The crop size is a token count, not an atom count. Ligands and modified
residues may be atomized and therefore consume one token per atom. A local
plan should set `crop_size` from the expected tokenized biomolecule, not from
raw residue count alone.

## Preflight assertions for weighted sampling

Before constructing a sampler or dataset, check locally:

1. every chain CSV and the interface CSV exists and has the required headers;
2. all mapping paths are files with `.csv` extension and are readable;
3. cluster IDs and PDB IDs are present and the interface rows refer to chain
   IDs in their own row;
4. each mapped PDB ID has a corresponding `.cif`/`.cif.gz` file in the data
   root, unless it is intentionally excluded before sampler construction;
5. `batch_size` is positive and the intended cluster count can support a
   cluster-based batch;
6. `alpha_*` and `beta_*` values are finite and reflect the experiment's
   declared policy; and
7. crop weights, `crop_size`, `training`/`inference`, and selected chains are
   consistent with the intended path.

The bundled validator checks paths, suffixes, required CSV headers, and crop
configuration. It does not calculate biological cluster membership or import
Polars/NumPy to construct sampling probabilities.
