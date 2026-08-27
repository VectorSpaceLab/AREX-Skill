# Molecular Generation Troubleshooting

## Dataset Downloads

- `QM9`, `ZINC250k`, `ZINC800`, and `MOSES` download CSVs or processed data when instantiated.
- If you only need API guidance, use the bundled smoke script rather than a real dataset constructor.

## Invalid Molecules or Low Validity

- Use `check_chemical_validity` and `check_valency` first.
- Convert radicals with `convert_radical_electrons_to_hydrogens` when the source molecule is chemically valid but needs sanitization.
- If validity is low, inspect the atom list and adjacency tensor channels before blaming the generator.

## Property Evaluator Assertions

- `PropOptEvaluator` needs at least three valid molecules.
- `ConstPropOptEvaluator` expects `inp_smiles` and four optimized molecule lists keyed by similarity threshold.
- If a property score is missing, confirm you passed RDKit `Mol` objects, not raw strings.

## Shape and Channel Errors

- One-shot generation expects a batch-first adjacency tensor with four bond channels and an atom tensor whose channel order matches the dataset atom list.
- Mismatched atom lists produce wrong molecules even when tensors have the right shape.

## Checkpoint and Device Issues

- `GraphAF` and `GraphDF` can fall back to CPU in some configurations, but generator configs often include a `use_gpu` flag.
- `GraphEBM`/`JTVAE` can also be expensive to initialize; confirm the checkpoint path before requesting a full run.
