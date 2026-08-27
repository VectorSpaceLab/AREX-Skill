# CLAM Training Data Formats

Use this reference before generating splits, training, or evaluating. CLAM training operates on extracted slide-level feature bags, not raw WSI files.

## Dataset CSV Schema

A CLAM dataset CSV must contain at least:

| Column | Required | Meaning | Notes |
| --- | --- | --- | --- |
| `case_id` | yes | Patient/case identifier | Used for patient-level grouping when `patient_strat=True`; multiple slides can share one case. |
| `slide_id` | yes | Slide feature basename | Must match `<slide_id>.pt` under `pt_files/`; keep zero padding and string types intact. |
| `label` | default label column | Slide-level class label | Can be replaced with a custom `label_col`, but CLAM creates an internal `label` column. |
| custom label columns | optional | Alternate labels | Pass the selected column as `label_col` in custom task branches. |
| `source` | optional | Dataset source key | `Generic_MIL_Dataset` can use a `data_dir` dict and route by this field. |

The built-in dummy CSVs use:

```csv
case_id,slide_id,label
patient_0,slide_0,tumor_tissue
```

For custom tasks, every non-ignored label value in the selected label column must exist in `label_dict`, for example `{'subtype_1': 0, 'subtype_2': 1, 'subtype_3': 2}`. Missing labels raise a key lookup failure during dataset preparation.

## Feature Folder Layout

`main.py` and `eval.py` construct dataset-specific feature paths under `--data_root_dir`. The dataset object then loads one tensor per slide from `pt_files/`:

```text
DATA_ROOT_DIR/
  tumor_subtyping_resnet_features/
    h5_files/
      slide_0.h5
    pt_files/
      slide_0.pt
```

Important alignment rules:

- `slide_id` values are basenames only; do not include `.pt` or `.h5` extensions.
- ResNet50 and UNI features are documented as 1024-dimensional, so use `--embed_dim 1024`.
- CONCH features are documented as 512-dimensional, so use `--embed_dim 512`.
- The built-in task branches expect feature subfolders named `tumor_vs_normal_resnet_features` or `tumor_subtyping_resnet_features`; custom tasks usually require editing those branch paths.

## Dataset Classes

`Generic_WSI_Classification_Dataset` reads CSV metadata, maps labels, optionally filters rows, and creates split IDs. Its verified constructor shape is:

```text
Generic_WSI_Classification_Dataset(csv_path='dataset_csv/ccrcc_clean.csv', shuffle=False, seed=7, print_info=True, label_dict={}, filter_dict={}, ignore=[], patient_strat=False, label_col=None, patient_voting='max')
```

`Generic_MIL_Dataset(data_dir, **kwargs)` extends the WSI dataset with feature loading from `pt_files/` by default, or `h5_files/` after `load_from_h5(True)`.

## Split Files

`create_splits_seq.py` writes split directories named:

```text
splits/<task>_<int(label_frac * 100)>/
```

Each fold produces:

| File | Contents |
| --- | --- |
| `splits_<fold>.csv` | Three columns: `train`, `val`, `test`; values are slide IDs. |
| `splits_<fold>_bool.csv` | Boolean one-hot split membership by slide ID. |
| `splits_<fold>_descriptor.csv` | Per-label counts for train/val/test. |

`main.py` resolves split paths as follows:

- If `--split_dir` is omitted, it uses `splits/<task>_<int(label_frac * 100)>`.
- If `--split_dir custom_name` is provided, it uses `splits/custom_name`.
- `--k`, `--k_start`, and `--k_end` determine which `splits_<fold>.csv` files are read.

## Patient Stratification and Voting

`create_splits_seq.py` uses `Generic_WSI_Classification_Dataset` with `patient_strat=True` for both bundled tasks, so slides from one case stay together. `patient_voting='max'` assigns a patient label by maximum slide label, while `patient_voting='maj'` assigns the modal slide label and is used by the bundled tumor subtyping split branch.

Training and evaluation task branches use `Generic_MIL_Dataset` with `patient_strat=False` and read the fold CSVs produced earlier. Patient grouping therefore happens during split creation, not during minibatch loading.

## Custom Task Checklist

For a new training task:

1. Add the task name to parser `choices` in the split, training, and evaluation entrypoints.
2. Add matching dataset branches with the intended `csv_path`, `data_dir`, `label_dict`, `label_col`, `ignore`, and `patient_voting` values.
3. Generate splits with the same task name and label fraction expected by training.
4. Use `MIL_fc` only for two classes and `MIL_fc_mc` indirectly via `--model_type mil` for more than two classes.
5. Use `--subtyping` for multiclass CLAM training, because the bundled training branch asserts it for the subtyping task.
