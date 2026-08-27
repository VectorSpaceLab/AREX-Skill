# Three-D Graph Workflows

## Property Prediction

1. Load `QM93D` or `MD17`.
2. Replace `dataset.data.y` with the target property column when needed.
3. Split with the helper method.
4. Build a `SchNet`, `DimeNetPP`, `SphereNet`, `ComENet`, or `ProNet` model.
5. Call `run().run(device, train_dataset, valid_dataset, test_dataset, model, loss_func, evaluation, ...)`.
6. Monitor the MAE from `ThreeDEvaluator`.

## Protein Classification

1. Prepare the EC or FOLD file layout.
2. Load the dataset with the requested split.
3. Use `ProNet` with the correct output classes.
4. Apply the runner and inspect accuracy.

## 3D Molecule Generation

1. Build `QM93DGEN`.
2. Use `get_idx_split('rand_gen'|'gap_opt'|'alpha_opt')`.
3. Batch with `collate_fn` and train `G_SphereNet`.
4. Generate molecular geometries and evaluate validity or bond-length MMD.
5. Use the `PropOptEvaluator` only when the property evaluation cost is acceptable.
