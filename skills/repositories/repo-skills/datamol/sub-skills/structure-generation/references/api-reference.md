# Structure Generation API Reference

Import datamol as `import datamol as dm`. Prefer top-level `dm.*` aliases where available and submodules (`dm.conformers`, `dm.align`, `dm.fragment`, `dm.scaffold`, `dm.reactions`) for grouped workflows.

## Conformers And 3D Features

| API | Key signature | Use when | Parameter guidance |
| --- | --- | --- | --- |
| `dm.conformers.generate` | `generate(mol, n_confs=None, use_random_coords=True, enforce_chirality=True, num_threads=1, rms_cutoff=None, clear_existing=True, align_conformers=True, minimize_energy=False, sort_by_energy=True, method=None, forcefield="UFF", ewindow=inf, eratio=inf, energy_iterations=200, warning_not_converged=0, random_seed=19, add_hs=True, ignore_failure=False, embed_params=None, verbose=False)` | Add 3D conformers to one molecule. | Use `n_confs=1-10` for examples; default is 50/200/300 by rotatable-bond count. `method` accepts `ETDG`, `ETKDG`, `ETKDGv2`, `ETKDGv3`; `None` maps to `ETKDGv3`. Set `minimize_energy=True` for energies; set `rms_cutoff` to prune near-duplicates. |
| `dm.conformers.cluster` | `cluster(mol, rms_cutoff=1, already_aligned=False, centroids=True)` | Reduce many conformers by RMSD. | `centroids=True` returns one molecule with representative conformers; `False` returns one molecule per cluster. Set `already_aligned=True` only after alignment. |
| `dm.conformers.rmsd` | `rmsd(mol)` | Compute all-by-all conformer RMSD. | Requires at least two conformers. |
| `dm.conformers.sasa` | `sasa(mol, conf_id=None, n_jobs=1)` | Compute FreeSASA values for conformers. | Requires existing 3D conformers. `conf_id=None` computes all; `int` or list selects conformers. Keep `n_jobs=1` for deterministic small examples. |
| `dm.conformers.get_coords` | `get_coords(mol, conf_id=-1)` | Extract conformer coordinates. | Raises if no conformer exists. |
| `dm.conformers.center_of_mass` | `center_of_mass(mol, use_atoms=True, digits=None, conf_id=-1)` | Compute mass-weighted or geometric center. | `use_atoms=False` gives geometric center; `digits` rounds output. |
| `dm.conformers.keep_conformers` | `keep_conformers(mol, indices_to_keep=-1, assign_id=True, copy=True)` | Keep selected conformer IDs/indices. | With `assign_id=True`, retained conformers are renumbered from 0. |
| `dm.conformers.align_conformers` | `align_conformers(mols, ref_id=0, copy=True, conformer_id=-1, backend="crippenO3A")` | Align 3D molecules to a reference. | Every molecule must already have at least one conformer. `backend` is `crippenO3A` or `O3A`. Returns `(aligned_mols, scores)`. |

## Alignment And Reordering

| API | Key signature | Use when | Parameter guidance |
| --- | --- | --- | --- |
| `dm.align.template_align` | `template_align(mol, template=None, copy=True, use_depiction=True, remove_confs=True, auto_select_coord_gen=False)` | Generate 2D depiction coordinates matching a template or MCS. | Accepts SMILES or Mol for `mol` and `template`. If `template=None`, returns the molecule. `use_depiction=True` is preferred for drawing; `False` uses `rdMolAlign.AlignMol`. |
| `dm.align.auto_align_many` | `auto_align_many(mols, partition_method="anon-scaffold", copy=True, cluster_cutoff=0.7, allow_r_groups=True, **kwargs)` | Align a molecule series/list by common cores. | `partition_method`: `scaffold`, `strip-scaffold`, `anon-scaffold`, `anongraph-scaffold`, or `cluster`. Adds `dm.auto_align_many.cluster_id` and `dm.auto_align_many.core` properties. |
| `dm.reorder_mol_from_template` | `reorder_mol_from_template(mol, mol_template, enforce_atomic_num=False, enforce_bond_type=False, ambiguous_match_mode="No", verbose=True)` | Reorder atom indices to match a template graph. | Useful for XYZ/template atom ordering. `ambiguous_match_mode`: `no`, `hs-only`, `first`, `best`, `best-first`. Returns `None` when no acceptable graph match exists. |

## Fragmentation And Assembly

| API | Key signature | Use when | Parameter guidance |
| --- | --- | --- | --- |
| `dm.fragment.brics` | `brics(mol, singlepass=True, remove_parent=False, sanitize=True, fix=True)` | BRICS fragmentation. | `singlepass=True` keeps decomposition bounded; `remove_parent=True` drops the original/parent fragment when present. |
| `dm.fragment.frag` | `frag(mol, remove_parent=False, sanitize=True, fix=True)` | Fraggle-style fragmentation. | Returns the input plus fragments unless `remove_parent=True`. |
| `dm.fragment.recap` | `recap(mol, remove_parent=False, sanitize=True, fix=True)` | RECAP decomposition. | Good for retrosynthetic-like decomposition. |
| `dm.fragment.anybreak` | `anybreak(mol, remove_parent=False, sanitize=True, fix=True)` | Try BRICS first, then fall back to Fraggle. | Use as a robust general fragmentation default. |
| `dm.fragment.mmpa_cut` | `mmpa_cut(mol, rdkit_pattern=False)` | Produce MMPA cut records. | Returns strings shaped like `smiles,core,chains`. Can become large for bigger molecules. |
| `dm.fragment.break_mol` | `break_mol(mol, minFragmentSize=1, silent=True, onlyUseReactions=[], randomize=False, mode="brics", returnTree=False)` | Recursively break molecules by BRICS/datamol reaction rules. | `mode`: `brics`, `rxn`, or other/combined. Use `returnTree=True` to inspect the fragmentation graph. Keep `randomize=False` for reproducibility. |
| `dm.fragment.build` | `build(ll_mols, max_n_mols=inf, mode="brics", frag_rxn=None, ADD_RNXS=[])` | Generate products from lists of fragments. | Always set `max_n_mols` for agent workflows. `ll_mols` is a list of fragment lists. |
| `dm.fragment.assemble_fragment_order` | `assemble_fragment_order(fragmentlist, seen=None, allow_incomplete=False, max_n_mols=inf, RXNS=None)` | Sequentially assemble fragments under BRICS-like rules. | Limit `max_n_mols`; `allow_incomplete=True` yields partial builds. |

## Scaffolds And Fuzzy Scaffolds

| API | Key signature | Use when | Parameter guidance |
| --- | --- | --- | --- |
| `dm.to_scaffold_murcko` | `to_scaffold_murcko(mol, make_generic=False)` | Extract Murcko scaffold. | `make_generic=True` converts atoms/bonds to a generic scaffold. |
| `dm.make_scaffold_generic` | `make_scaffold_generic(mol, include_bonds=False)` | Generalize a scaffold/molecule. | Mutates the molecule object; copy first if preserving atom/bond identity matters. `include_bonds=True` makes bond orders generic too. |
| `dm.strip_mol_to_core` | `strip_mol_to_core(mol, bond_cutter=None)` | Guess and retain a molecular core/ring system. | Uses a default non-ring bond cutter when none is supplied. |
| `dm.compute_ring_system` | `compute_ring_system(mol, include_spiro=True)` | Return ring-system atom index sets. | `include_spiro=False` keeps spiro-linked rings separate. |
| `dm.scaffold.fuzzy_scaffolding` | `fuzzy_scaffolding(mols, enforce_subs=None, n_atom_cuttoff=8, additional_templates=None, ignore_non_ring=False, mcs_params=None)` | Find fuzzy scaffolds across an analog set. | Returns `(all_scaffolds, df_scaffold_infos, df_scaffold_groups)`. Use `enforce_subs` to retain required side chains, `additional_templates` to seed cores, and restrictive `mcs_params` for large sets. |

## Reactions And Attachments

| API | Key signature | Use when | Parameter guidance |
| --- | --- | --- | --- |
| `dm.reactions.rxn_from_smarts` | `rxn_from_smarts(rxn_smarts)` | Parse reaction SMARTS. | Calls `Initialize`; validate with `is_reaction_ok`. |
| `dm.reactions.rxn_to_smarts` | `rxn_to_smarts(rxn)` | Serialize a reaction to SMARTS. | Useful for logging or round-tripping. |
| `dm.reactions.rxn_from_block` | `rxn_from_block(rxn_block, sanitize=False)` | Parse RXN block text. | Use `sanitize=True` only when needed; invalid blocks may fail earlier. |
| `dm.reactions.rxn_from_block_file` | `rxn_from_block_file(rxn_block_path, sanitize=False)` | Parse a local/fsspec RXN block file. | Runtime skills should avoid depending on external source files. |
| `dm.reactions.rxn_to_block` | `rxn_to_block(rxn, separate_agents=False, force_V3000=False)` | Serialize a reaction to RXN block text. | `force_V3000` depends on RDKit version support. |
| `dm.reactions.is_reaction_ok` | `is_reaction_ok(rxn, enable_logs=False)` | Check basic RDKit reaction sanity. | `enable_logs=True` reports preprocessing counts. |
| `dm.reactions.apply_reaction` | `apply_reaction(rxn, reactants, product_index=None, single_product_group=False, as_smiles=False, rm_attach=False, disable_logs=True, sanitize=True)` | Run a reaction on a tuple of reactant molecules. | `single_product_group=False` keeps all product groups. Set `as_smiles=True` for compact results; `rm_attach=True` removes dummy attachment points. |
| `dm.reactions.select_reaction_output` | `select_reaction_output(product, product_index=None, single_product_group=True, rm_attach=False, as_smiles=False, sanitize=True)` | Post-process raw RDKit reaction output. | Beware `single_product_group=True` selects a random group; use `False` for deterministic complete output. |
| `dm.reactions.can_react` | `can_react(rxn, mol)` | Check whether a molecule can occupy any reactant slot. | Use before expensive enumeration of reactant combinations. |
| `dm.reactions.find_reactant_position` | `find_reactant_position(rxn, mol)` | Identify reactant template position. | Returns `-1` when no template matches. |
| `dm.reactions.inverse_reaction` | `inverse_reaction(rxn)` | Swap reactants/products for retrosynthetic checks. | Validate the inverse before applying. |
| `dm.reactions.convert_attach_to_isotope` | `convert_attach_to_isotope(mol_or_smiles, same_isotope=False, as_smiles=False)` | Convert dummy attachments like `[*:1]` to isotope-marked dummies like `[1*]`. | `same_isotope=True` maps all attachment points to `[1*]`; `as_smiles=True` returns SMILES. |
| `dm.reactions.num_attachment_points` | `num_attachment_points(mol_or_smiles)` | Count dummy attachment points. | Accepts Mol or SMILES. |
| `dm.reactions.open_attach_points` | `open_attach_points(mol, fix_atom_map=False, bond_type=dm.SINGLE_BOND)` | Add dummy attachment points to atoms with implicit valence. | Respects atoms protected with `_protected=1`. |

## Isomers And Tautomers

| API | Key signature | Use when | Parameter guidance |
| --- | --- | --- | --- |
| `dm.enumerate_tautomers` | `enumerate_tautomers(mol, n_variants=20, max_transforms=1000, reassign_stereo=True, remove_bond_stereo=True, remove_sp3_stereo=True)` | Enumerate tautomeric states. | Bound `n_variants`; stereo may be reassigned/removed around tautomeric centers. |
| `dm.enumerate_stereoisomers` | `enumerate_stereoisomers(mol, n_variants=20, undefined_only=False, rationalise=True, timeout_seconds=None, clean_it=True)` | Enumerate atom and bond stereoisomers. | Use `undefined_only=True` to preserve assigned stereo. Use `timeout_seconds` and small `n_variants`. If RDKit raises on stereo cleanup, retry with `clean_it=False`. |
| `dm.count_stereoisomers` | `count_stereoisomers(mol, n_variants=20, undefined_only=False, rationalise=True, timeout_seconds=None, clean_it=True, precise=False)` | Estimate or compute stereoisomer count. | `precise=False` is faster upper-bound style; `precise=True` enumerates and can be expensive. |
| `dm.enumerate_structisomers` | `enumerate_structisomers(mol, n_variants=20, allow_cycle=False, allow_double_bond=False, allow_triple_bond=False, depth=None, timeout_seconds=None)` | Enumerate structural isomers. | Most combinatorial API in this sub-skill; set `depth`, `n_variants`, and `timeout_seconds`. |
| `dm.canonical_tautomer` | `canonical_tautomer(mol)` | Normalize a molecule to RDKit's canonical tautomer. | Useful before deduplicating tautomer sets. |
| `dm.remove_stereochemistry` | `remove_stereochemistry(mol, copy=True)` | Strip all stereo annotations. | `copy=True` preserves original molecule. |
