# Molecular Graph Generation API Reference

## Datasets

- `QM9(root='./', prop_name='penalized_logp', use_aug=False, one_shot=False)`.
- `ZINC250k(root='./', prop_name='penalized_logp', use_aug=False, one_shot=False)`.
- `ZINC800(root='./', method='jt', prop_name='penalized_logp', use_aug=False, one_shot=False)`.
- `MOSES(root='./', prop_name=None, use_aug=False, one_shot=False)`.
- Shared base: `PygDataset(root, name, prop_name, ...)`.

## Generators

- `GraphAF()` with `train_rand_gen`, `run_rand_gen`, `train_prop_optim`, `run_prop_optim`, `train_const_prop_opt`, `run_const_prop_opt`.
- `GraphDF()` with the same generator-style family of methods.
- `GraphEBM(n_atom, n_atom_type, n_edge_type, hidden, device=None)`.
- `JTVAE(list_smiles, build_vocab=True, device=None)`.
- `Generator` is the abstract base class for new graph generators.

## Evaluators

- `RandGenEvaluator.eval({'mols': [...], 'train_smiles': [...]})` returns validity, uniqueness, and novelty percentages.
- `PropOptEvaluator(prop_name='plogp'|'qed').eval({'mols': [...]})` returns the top-3 property scores.
- `ConstPropOptEvaluator.eval({'mols_0': ..., 'mols_2': ..., 'mols_4': ..., 'mols_6': ..., 'inp_smiles': [...]})` returns thresholded similarity and improvement metrics.

## Helpers

- `check_chemical_validity(mol)`.
- `check_valency(mol)`.
- `convert_radical_electrons_to_hydrogens(mol)`.
- `calculate_min_plogp(mol)`.
- `reward_target_molecule_similarity(mol, target)`.
- `gen_mol_from_one_shot_tensor(adj, x, atomic_num_list, correct_validity=True, largest_connected_comp=True)`.
