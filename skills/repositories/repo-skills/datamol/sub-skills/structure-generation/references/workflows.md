# Structure Generation Workflows

These workflows assume molecules have already been parsed and cleaned. For invalid SMILES, salts, neutralization, or file I/O, route through `molecule-io-prep` first.

## Conformer Generation, SASA, And 3D Features

1. Parse and sanitize the input molecule.
2. Generate bounded conformers:
   ```python
   mol = dm.to_mol("CC(=O)Oc1ccccc1C(=O)O")
   mol3d = dm.conformers.generate(
       mol,
       n_confs=5,
       rms_cutoff=0.5,
       minimize_energy=True,
       forcefield="UFF",
       random_seed=19,
       num_threads=1,
   )
   ```
3. Inspect conformer count and energy properties:
   ```python
   n_confs = mol3d.GetNumConformers()
   props = mol3d.GetConformer(0).GetPropsAsDict()
   ```
4. Compute features only after conformers exist:
   ```python
   coords = dm.conformers.get_coords(mol3d, conf_id=0)
   center = dm.conformers.center_of_mass(mol3d, conf_id=0)
   sasa_values = dm.conformers.sasa(mol3d, conf_id=None, n_jobs=1)
   ```
5. For many conformers, cluster or keep selected ones:
   ```python
   centroids = dm.conformers.cluster(mol3d, rms_cutoff=1.0, centroids=True)
   best = dm.conformers.keep_conformers(mol3d, indices_to_keep=0)
   ```

Use `ignore_failure=True` only when processing a batch where failed molecules can be recorded and skipped. If `generate` returns `None`, do not call coordinate/SASA APIs on that molecule.

## Alignment And Reordering

### 2D Template Alignment

Use this for depictions or matched layout before visualization:

```python
template = dm.to_mol("c1ccccc1")
query = dm.to_mol("COc1ccccc1")
aligned = dm.align.template_align(query, template=template, use_depiction=True)
```

If the template is not a direct substructure, datamol computes an MCS pattern. For large or dissimilar molecules, MCS can be slow; pre-filter by scaffold or similarity before aligning many molecules.

### Align Many Molecules By Core

```python
mols = [dm.to_mol(s) for s in smiles_list]
aligned = dm.align.auto_align_many(mols, partition_method="anon-scaffold")
cluster_ids = [m.GetIntProp("dm.auto_align_many.cluster_id") for m in aligned]
cores = [m.GetProp("dm.auto_align_many.core") for m in aligned]
```

Choose `partition_method` by intent:

- `scaffold`: preserve element/bond identity in Murcko scaffolds.
- `strip-scaffold`: cut down to guessed core/ring system.
- `anon-scaffold`: generic atoms, bond order kept; robust for related analogs.
- `anongraph-scaffold`: generic atoms and generic bonds.
- `cluster`: use fingerprint clustering first; sensitive to `cluster_cutoff`.

### 3D Conformer Alignment

```python
mols = [dm.conformers.generate(dm.to_mol(s), n_confs=1) for s in smiles_list]
aligned_mols, scores = dm.conformers.align_conformers(mols, ref_id=0, backend="crippenO3A")
```

Every input must contain a conformer. Use `backend="O3A"` when MMFF atom typing is preferred, but expect hydrogens to be temporarily added and removed.

### Reorder Atoms From Template

```python
reordered = dm.reorder_mol_from_template(
    mol,
    mol_template,
    ambiguous_match_mode="best-first",
    enforce_atomic_num=False,
    enforce_bond_type=False,
)
if reordered is None:
    # Graphs do not match or the match is ambiguous.
    ...
```

Use explicit hydrogens consistently in both `mol` and `mol_template`; mixed implicit/explicit hydrogens often prevent a match.

## Fragmentation And Assembly

### Choose A Fragmenter

```python
mol = dm.to_mol("CCCOCc1cc(c2ncccc2)ccc1")
brics_frags = dm.fragment.brics(mol, remove_parent=True)
recap_frags = dm.fragment.recap(mol, remove_parent=True)
robust_frags = dm.fragment.anybreak(mol, remove_parent=True)
```

- Start with `anybreak` for general robust fragmentation.
- Use `brics` for BRICS-compatible fragment libraries and assembly.
- Use `recap` for retrosynthetic-style cuts.
- Use `mmpa_cut` when the desired output is MMPA records, not molecules.

### Recursive Break Tree

```python
leaves, all_nodes, tree = dm.fragment.break_mol(
    mol,
    mode="brics",
    minFragmentSize=1,
    randomize=False,
    returnTree=True,
)
```

Keep `randomize=False` for reproducible agent outputs. Inspect `leaves` as SMILES and use the tree only in local analysis, not as a persistent runtime dependency.

### Bounded Assembly

```python
fragment_groups = [[dm.to_mol("CCCO"), dm.to_mol("CCCCO")], [dm.to_mol("CCC")]]
products = list(dm.fragment.build(fragment_groups, max_n_mols=10, mode="brics"))
```

For ordered assembly:

```python
frags = dm.fragment.brics(mol)[:2]
products = list(dm.fragment.assemble_fragment_order(frags, max_n_mols=4))
```

Always bound assembly with `max_n_mols`; fragment combinations and reaction rules grow quickly.

## Scaffold And Fuzzy Scaffold Workflows

### Basic Murcko And Generic Scaffolds

```python
mol = dm.to_mol("COc1ccc(OC(C)C(=O)N)c(Br)c1")
scaffold = dm.to_scaffold_murcko(mol)
generic = dm.make_scaffold_generic(dm.copy_mol(scaffold), include_bonds=False)
ring_systems = dm.compute_ring_system(mol, include_spiro=True)
```

`make_scaffold_generic` mutates the molecule, so copy first if the original scaffold is needed later.

### Strip To Core

```python
core = dm.strip_mol_to_core(mol)
```

Use this when substituents obscure the ring/core system. If the default cutter is too broad or narrow, provide a custom SMARTS molecule as `bond_cutter`.

### Fuzzy Scaffolding Across Analogs

```python
mols = [dm.to_mol(s) for s in smiles_list]
required = [dm.from_smarts("c1ccccc1")]
scaffolds, scaffold_infos, scaffold_groups = dm.scaffold.fuzzy_scaffolding(
    mols,
    enforce_subs=required,
    n_atom_cuttoff=6,
    ignore_non_ring=False,
    mcs_params={"timeout": 5},
)
```

Use fuzzy scaffolding for analog sets where Murcko scaffolds are too strict. Keep `mcs_params` bounded for large sets, and inspect both returned dataframes to explain which molecules and R-groups support each scaffold.

## Reaction Application And Attachment Points

### Parse And Validate Reaction SMARTS

```python
rxn_smarts = "[C:1]" "(=[O:2])O.[N:3]>>[C:1]" "(=[O:2])[N:3]"
rxn = dm.reactions.rxn_from_smarts(rxn_smarts)
if not dm.reactions.is_reaction_ok(rxn):
    raise ValueError("Reaction failed RDKit validation")
```

### Check Reactants And Apply

```python
acid = dm.to_mol("CC(=O)O")
amine = dm.to_mol("NCC")
if dm.reactions.can_react(rxn, acid) and dm.reactions.can_react(rxn, amine):
    products = dm.reactions.apply_reaction(
        rxn,
        reactants=(acid, amine),
        product_index=0,
        single_product_group=False,
        as_smiles=True,
        sanitize=True,
    )
```

`apply_reaction` returns all product groups when `single_product_group=False`. Prefer that mode for deterministic workflows. If only one product is desired, select by index after sorting/normalizing the SMILES rather than relying on random group selection.

### Attachment Point Workflows

```python
scaffold = dm.to_mol("O=C(NC[1*])NCc1ccnc(OCc2ccccc2)c1")
fragment = dm.to_mol("CC(O[1*])C(F)(F)F")
join_smarts = "[1*]" "[*:1].[1*]" "[*:2]>>[*:1]" "[*:2]"
join = dm.reactions.rxn_from_smarts(join_smarts)
products = dm.reactions.apply_reaction(
    join,
    (scaffold, fragment),
    product_index=0,
    single_product_group=False,
    rm_attach=True,
    as_smiles=True,
)
```

Use `convert_attach_to_isotope` when source structures use `[*:1]` style dummy atoms but joining SMARTS expects isotope-labeled dummies such as `[1*]`. Use `num_attachment_points` to verify that expected handles exist before applying reactions.

## Isomer And Tautomer Enumeration

### Tautomers

```python
mol = dm.to_mol("OC1=CC2CCCCC2N=C1")
tautomers = dm.enumerate_tautomers(mol, n_variants=10, max_transforms=100)
canonical = dm.canonical_tautomer(mol)
```

Canonical tautomers are useful for deduplication; enumeration is useful when every state should be scored.

### Stereoisomers

```python
mol = dm.to_mol("CC=CC")
count = dm.count_stereoisomers(mol, undefined_only=True, precise=False)
stereoisomers = dm.enumerate_stereoisomers(
    mol,
    n_variants=8,
    undefined_only=True,
    timeout_seconds=2,
)
```

Use `undefined_only=True` when existing stereochemistry should remain fixed. If cleanup raises an RDKit error for complex stereo annotations, retry with `clean_it=False` and document the fallback.

### Structural Isomers

```python
mol = dm.to_mol("CCCCC")
structural = dm.enumerate_structisomers(
    mol,
    n_variants=5,
    allow_cycle=False,
    allow_double_bond=False,
    allow_triple_bond=False,
    depth=1,
    timeout_seconds=2,
)
```

Structural isomer enumeration is combinatorial. Keep conservative defaults unless the user explicitly asks for broader chemistry; increase `depth` and `allow_*` flags one at a time.
