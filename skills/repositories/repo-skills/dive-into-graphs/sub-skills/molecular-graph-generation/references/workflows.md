# Molecular Graph Generation Workflows

## Random Generation

1. Choose `QM9` or `ZINC250k` for property-driven molecule generation, or `ZINC800` for the smaller optimization dataset.
2. Load the dataset with `use_aug=True` when the generator expects augmented one-shot graphs.
3. Batch with `torch_geometric.loader.DenseDataLoader` for one-shot tensors.
4. Train `GraphAF` or `GraphDF` with the model config from the example files and save checkpoints at the configured interval.
5. Generate molecules from a checkpoint and evaluate them with `RandGenEvaluator`.

## Property Optimization

1. Start from the same dataset family and property configuration.
2. Fine-tune the pretrained generator with `train_prop_optim` or `train_prop_opt`.
3. Generate with `run_prop_optim` or `run_prop_opt`.
4. Use `PropOptEvaluator` to return the top-3 molecules and their property scores.

## Constrained Optimization

1. Prepare source molecules as RDKit `Mol` objects or SMILES strings depending on the generator.
2. Use the constrained training path for the selected generator.
3. Generate candidate molecules with the similarity threshold settings from the example configuration.
4. Validate improvement and similarity with `ConstPropOptEvaluator`.

## One-Shot Conversion

- The one-shot tensor format uses a 4-channel adjacency tensor and an atom-channel tensor.
- `gen_mol_from_one_shot_tensor` converts those tensors back into RDKit molecules.
- Use `check_chemical_validity` and `check_valency` after conversion before scoring or ranking outputs.
