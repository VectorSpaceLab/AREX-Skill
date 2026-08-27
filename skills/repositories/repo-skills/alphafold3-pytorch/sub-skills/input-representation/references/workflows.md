# Input workflows

These workflows are deliberately bounded. They construct features and validate
contracts; they do not acquire data, train, launch a server, or select a model
checkpoint.

## 1. Direct sequence/SMILES construction

Use this for a template-free, MSA-free input description.

```python
from alphafold3_pytorch import (
    Alphafold3Input,
    alphafold3_inputs_to_batched_atom_input,
)

inp = Alphafold3Input(
    proteins=["AG"],
    ss_rna=["C"],
    ds_dna=["AT"],
    ligands=["CCO"],
    metal_ions=["Zn"],
    add_atom_ids=True,
    add_atompair_ids=True,
)
batch = alphafold3_inputs_to_batched_atom_input(inp, atoms_per_window=27)
model_kwargs = batch.model_forward_dict()
```

Before handing `model_kwargs` to the model, record `m`, `n`, the feature last
dimensions, and the maximum atom-pair id. Set the model embedding dimensions to
match those observations. A direct input does not create MSA or template
features from a PDB; route those requirements to [data-pipeline](../../data-pipeline/SKILL.md).

## 2. Double-stranded nucleic acids

Pass only the supplied strand in `ds_dna` or `ds_rna`. The converter appends the
reverse complement and assigns separate chain/entity metadata. The string
reverse-complement mapping is:

- DNA: `A↔T`, `C↔G`, then reverse the sequence.
- RNA: `A↔U`, `C↔G`, then reverse the sequence.

For integer tensors, the implementation expects the package's compact ordering
`A,C,G,T/U,N`; the tensor complement is an index lookup followed by a flip.
Validate that `reverse_complement(reverse_complement(x)) == x` for synthetic
cases before using an integer sequence in a larger batch.

## 3. Mixed complex with custom embeddings

A useful preflight includes a short protein, a dsDNA entity, a ligand SMILES,
and a metal. Set `add_atom_ids=True` and supply a custom atom list containing
all symbols emitted by the SMILES and ion. Set `add_atompair_ids=True` and
`directed_bonds=True` only if the downstream model was configured for the
corresponding category count. Then validate:

- token category columns are mutually exclusive;
- atom count equals the sum of `molecule_atom_lens`;
- all nonnegative index fields are in `[0,m)`;
- frame triples are either valid or all `-1`;
- atom ids and pair ids are within the configured embedding ranges; and
- pairwise features are symmetric where the reference-space construction
  requires symmetry.

`misc_molecule_ids` is not a reliable direct entity route in the current
converter. Represent a miscellaneous chemical component as a ligand SMILES only
when its SMILES and desired atomization are known.

## 4. Unequal batch and windowing

Construct two valid inputs with different token and atom counts. Convert them
with:

```python
batch = alphafold3_inputs_to_batched_atom_input(
    [short_input, longer_input],
    atoms_per_window=27,
)
```

The result is padded to the largest dimensions. Check `molecule_atom_lens==0`
for padded tokens and `missing_atom_mask==True` for padded atoms. Integer index
fields use `-1`; float features use zero. Windowing turns full pair features into
`[b,nw,w,2w,dapi]` only once. Calling collation again on an already windowed
pair tensor should leave it windowed, but do not change the configured `w`
midstream.

The generic collator may duplicate successfully transformed examples when an
input fails conversion. For a reproducible validator or benchmark, call
`maybe_transform_to_atom_input(..., raise_exception=True)` for every item and
stop on the first failure rather than accepting a duplicated batch.

## 5. Atom serialization round trip

Use a temporary or deliberately versioned `.pt` target:

```python
from alphafold3_pytorch import atom_input_to_file, file_to_atom_input

path = atom_input_to_file(atom_input, target, overwrite=False)
restored = file_to_atom_input(path)
assert torch.equal(atom_input.atom_inputs, restored.atom_inputs)
```

The writer creates parent directories and refuses an existing path unless
`overwrite=True`. The loader uses `weights_only=True`; files containing arbitrary
Python objects or old unsupported serialization content may not load. Compare
all tensor fields, not just `atom_inputs`, before treating the round trip as
valid. `AtomDataset` requires at least one `.pt` file and returns the same
`AtomInput` type.

## 6. Missing atoms and labels

For a polymer-only example, supply one missing-index entry per residue molecule,
with local atom indices. Convert, then verify the missing mask and that token
centers/frame atoms which refer to missing atoms became `-1`. Do not silently
invent coordinates for missing atoms.

Current direct conversion has an awkward invariant when nonempty
`missing_atom_indices` is combined with atomized multi-atom ligands: it checks
both molecule-list length and expanded token-list length. If that case is
needed, preflight it and stop on a clear validation error; use an explicit
`AtomInput` with a correctly constructed `missing_atom_mask` only after the
atom-level contract has been independently checked.

## 7. Prediction coordinates to Biomolecule/mmCIF

For a standalone direct-input export:

1. Convert the same `Alphafold3Input` to learn its token count `n`.
2. Supply one unbatched coordinate array shaped `[n,47,3]` to
   `alphafold3_input_to_biomolecule`.
3. Inspect `Biomolecule.atom_positions`, `atom_mask`, `chemid`, `chemtype`,
   residue indices, and chain ids.
4. Render with `to_inference_mmcif` using a chosen file id.

Do not pass model sampling output `[b,m,3]` directly to this standalone
converter. For model execution and its structure-returning option, use
[model-inference](../../model-inference/SKILL.md); for existing mmCIF metadata,
ligand naming, and parser round trips, use [data-pipeline](../../data-pipeline/SKILL.md).

The direct conversion intentionally uses compact 47-slot residue constants.
Ligands and metal ions use the ligand-compatible fallback constants, and the
current helper does not preserve a full chemical-component table or complete
ligand naming metadata. Treat the resulting mmCIF as a compatible structural
output and inspect it before publication.

## 8. Difficult synthetic usability cases

1. **Mixed entity case:** protein `AG`, dsDNA `AT`, ssRNA `C`, ligand `CCO`, and
   `Zn`, with atom/pair ids, directed bonds, a custom atom vocabulary, and a
   missing polymer atom. Expected checks: reverse-complement expansion,
   category counts, ascending indices, missing-mask propagation, and an
   actionable rejection if the known missing-index/list invariant is violated.
2. **Unequal round trip:** a short protein-only input and a longer protein +
   ligand input are converted together with a small window size, serialized in
   temporary files, reloaded, and compared field-by-field. Expected checks:
   window shape, zero/true padding, `-1` indices, unchanged unpadded tensors,
   and deterministic entity summaries.
