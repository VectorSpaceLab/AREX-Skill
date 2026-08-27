# DeepLabCut Data Formats For Labels And Trainsets

This reference describes the runtime formats this sub-skill owns. It is intentionally self-contained and uses placeholder paths such as `<project>` instead of machine-specific locations.

## Project-level assumptions

A project is ready for this sub-skill when these `config.yaml` fields are already meaningful:

- `project_path`: project root directory.
- `scorer`: the annotator/scorer name used in annotation files.
- `video_sets`: mapping of video paths to crop metadata; each video's stem determines the corresponding `labeled-data/<video-stem>/` folder.
- `TrainingFraction`: list of fractions such as `[0.8]` or `[0.95]`.
- `iteration`: integer used in trainset and model folder names.
- Standard projects: `bodyparts: [part1, part2, ...]` and `multianimalproject: false` or absent.
- Multi-animal projects: `multianimalproject: true`, `bodyparts: MULTI!`, `individuals`, `multianimalbodyparts`, `uniquebodyparts`, and usually `identity` and `default_track_method`.
- Engine selection: `engine: pytorch` or `engine: tensorflow` when a non-default is needed. DeepLabCut 3 defaults to PyTorch if no engine is set.

New-project creation and broad configuration design belong to the setup sub-skill. This sub-skill validates and uses the configuration for data work.

## `labeled-data/` layout

For every video listed in `config.yaml`, DeepLabCut expects a per-video label folder named after the video stem:

```text
<project>/
├── config.yaml
├── videos/
│   └── <video-stem>.<ext>
└── labeled-data/
    └── <video-stem>/
        ├── img0000.png
        ├── img0001.png
        ├── CollectedData_<scorer>.h5
        └── CollectedData_<scorer>.csv
```

Important implications:

- Avoid duplicate video basenames in one project. DeepLabCut resolves label folders by video stem, so two configured videos named `camera1.avi` in different directories can collide in `labeled-data/camera1/`.
- Annotation row indices should identify images relative to the project, commonly as a three-level MultiIndex: `("labeled-data", "<video-stem>", "img0000.png")`.
- Older or external CSV files may store the row path as one slash-separated string; `convertcsv2h5` and internal row normalization can convert compatible rows to a MultiIndex.
- The HDF key used by DeepLabCut label tables is `df_with_missing`.

## Standard single-animal annotation table

Standard labels use a Pandas column MultiIndex with three levels:

```text
level 0: scorer      e.g. synthetic
level 1: bodyparts   e.g. nose, tailbase
level 2: coords      x, y
```

Example columns:

```text
(synthetic, nose, x)
(synthetic, nose, y)
(synthetic, tailbase, x)
(synthetic, tailbase, y)
```

Rules:

- The first column level must match `config.yaml` `scorer` for training dataset creation. Labels under another scorer can be ignored during the merge step.
- Bodypart spelling, case, and spacing must match `config.yaml` `bodyparts` exactly.
- Training labels are x/y coordinates. If imported annotation data includes `likelihood` columns, DeepLabCut's training-data formatter drops those columns before creating training files, but a clean label table should normally contain only `x` and `y`.
- Missing or occluded points should be `NaN`, not zero, unless zero is truly a labeled image coordinate.

## Multi-animal annotation table

Multi-animal labels use a four-level Pandas column MultiIndex:

```text
level 0: scorer        e.g. synthetic
level 1: individuals   named animals plus optional single
level 2: bodyparts     multi-animal or unique bodypart names
level 3: coords        x, y
```

For multi-animal body parts, columns are repeated for each named individual:

```text
(synthetic, animal_0, nose, x)
(synthetic, animal_0, nose, y)
(synthetic, animal_1, nose, x)
(synthetic, animal_1, nose, y)
```

For unique bodyparts, DeepLabCut stores them under the special individual name `single`:

```text
(synthetic, single, perch, x)
(synthetic, single, perch, y)
```

Rules:

- `individuals` in `config.yaml` lists only trackable animals. DeepLabCut appends `single` internally when `uniquebodyparts` is non-empty.
- `multianimalbodyparts` are bodyparts that can occur once per animal. `uniquebodyparts` are scene-level or single-object bodyparts that should not be connected to animal-specific skeleton edges.
- If animal identities are visually distinguishable, label the same real animal with the same individual name across frames. If they are indistinguishable, consistency within each frame is the key requirement for training grouping; temporal identity linkage is handled later by tracking workflows.
- `check_labels(..., visualizeindividuals=True)` colors by individual; `False` colors by bodypart. Running both can expose different labeling mistakes.

## CSV header conventions

DeepLabCut CSV annotation files are usually written by `DataFrame.to_csv()` from the HDF table:

- Standard CSVs have three column-header rows for `scorer`, `bodyparts`, and `coords`.
- Multi-animal CSVs have four column-header rows for `scorer`, `individuals`, `bodyparts`, and `coords`.
- External CSV imports must preserve the relative image path row information and the expected header levels.
- `convertcsv2h5(config, scorer=<target>)` can rewrite the scorer level while creating the HDF file.

## Training-dataset layout

`create_training_dataset` merges per-video label files into a trainset folder and creates shuffle-specific files. The core layout is:

```text
<project>/
├── training-datasets/
│   └── iteration-<iteration>/
│       └── UnaugmentedDataSet_<Task><date>/
│           ├── CollectedData_<scorer>.h5
│           ├── CollectedData_<scorer>.csv
│           ├── metadata.yaml
│           ├── <Task>_<scorer><trainPercent>shuffle<shuffle>.mat        # standard projects
│           ├── <Task>_<scorer><trainPercent>shuffle<shuffle>.pickle     # multi-animal projects
│           └── Documentation_data-<Task>_<trainPercent>shuffle<shuffle>.pickle
└── dlc-models-pytorch/ or dlc-models/
    └── iteration-<iteration>/
        └── <Task><date>-trainset<trainPercent>shuffle<shuffle>/
            ├── train/
            │   └── pytorch_config.yaml or pose_cfg.yaml
            └── test/
                └── pose_cfg.yaml
```

Notes:

- PyTorch shuffles create `dlc-models-pytorch/.../train/pytorch_config.yaml`; TensorFlow shuffles use `dlc-models/.../train/pose_cfg.yaml`.
- `metadata.yaml` records shuffles, train fractions, engines, and reusable split ids. New DeepLabCut 3 flows rely on it for copying existing splits and inferring shuffle engines.
- The documentation pickle stores the train/test indices and train fraction for one shuffle. `create_training_dataset_from_existing_split` loads these indices and may pad them internally with `-1` while preserving exact rounded `TrainingFraction` ratios.
- Model folders created here contain configuration files only; actual weights and snapshots are produced by training, which is outside this sub-skill.

## Split semantics

- `mergeandsplit(config, trainindex=0, uniform=True)` merges labels and returns train/test indices without creating model config files. Use it when a split must be frozen or customized.
- `uniform=True` uses `TrainingFraction[trainindex]` and samples across all labeled rows.
- `uniform=False` performs leave-one-video-folder-out: `trainindex` selects the video folder whose rows become the test set.
- `create_training_dataset(..., Shuffles=[...], trainIndices=[...], testIndices=[...])` consumes explicit splits. The number of `Shuffles`, train index lists, and test index lists must match.

## Conversion outputs

`convertcsv2h5` reads each configured `labeled-data/<video-stem>/CollectedData_<scorer>.csv`, optionally rewrites the scorer level, and writes the matching `.h5` file.

`convert2_maDLC` converts single-animal annotation files into multi-animal format using the multi-animal fields in `config.yaml`. It backs up the original single-animal files as `CollectedData_<scorer>singleanimal.h5` and `.csv`, then overwrites `CollectedData_<scorer>.h5/.csv` with the multi-animal table.
