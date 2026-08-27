# Three-D Graphs API Reference

## Datasets

- `QM93D(root='dataset/')`.
- `MD17(root='dataset/', name='benzene_old')`.
- `ECdataset(root, split='train'|'Val'|'Test')`.
- `FOLDdataset(root, split='train'|'validation'|'test')`.
- `QM93DGEN(root='./qm9_3Dgen', subset_idxs=None)` for 3D generation.

## Property-Regression Methods

- `run()` returns a training/validation/testing runner.
- `SchNet(energy_and_force=False, cutoff=10.0, num_layers=6, hidden_channels=128, out_channels=1, num_filters=128, num_gaussians=50)`.
- `DimeNetPP(energy_and_force=False, cutoff=5.0, num_layers=4, hidden_channels=128, out_channels=1, int_emb_size=64, basis_emb_size=8, out_emb_channels=256, num_spherical=7, num_radial=6, envelope_exponent=5, num_before_skip=1, num_after_skip=2, num_output_layers=3)`.
- `SphereNet(energy_and_force=False, cutoff=5.0, num_layers=4, hidden_channels=128, out_channels=1, int_emb_size=64, basis_emb_size_dist=8, basis_emb_size_angle=8, basis_emb_size_torsion=8, out_emb_channels=256, num_spherical=7, num_radial=6, envelope_exponent=5, num_before_skip=1, num_after_skip=2, num_output_layers=3)`.
- `ComENet(...)` and `ProNet(...)` for the other included 3D workflows.

## 3D Generation Methods

- `G_SphereNet()` with `.train(...)` and `.generate(...)`.
- `collate_fn(data_batch_list)` for 3D generation batches.

## Evaluators

- `ThreeDEvaluator.eval({'y_true': ..., 'y_pred': ...})` returns MAE.
- `dig.ggraph3D.evaluation.RandGenEvaluator.eval_validity(mol_dicts)` returns chemical validity percent.
- `dig.ggraph3D.evaluation.RandGenEvaluator.eval_bond_mmd(...)` returns bond-length MMD values.
- `dig.ggraph3D.evaluation.PropOptEvaluator.eval(mol_dicts)` returns mean/best/good-percent summaries.
