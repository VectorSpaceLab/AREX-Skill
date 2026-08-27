# Data Labeling And Training-Dataset Workflows

Use these workflows after a DeepLabCut project exists and `config.yaml` has the right project, scorer, video, bodypart, individual, and engine settings.

## Quick API map

| API | Use for | Key cautions |
| --- | --- | --- |
| `deeplabcut.extract_frames(config, mode="automatic", algo="kmeans"/"uniform", crop=False/True, userfeedback=True/False, videos_list=None)` | Select images from configured videos into `labeled-data/<video-stem>/`. | `manual` opens a GUI. `crop="GUI"` opens a GUI. `mode="match"` can overwrite matched camera labels. In automation, set `userfeedback=False` only for disposable or confirmed outputs. |
| `deeplabcut.check_labels(config, scale=1, dpi=100, draw_skeleton=True, visualizeindividuals=True)` | Render labeled images for visual inspection. | It reports folders without `CollectedData_<scorer>.h5`; it does not train or fix labels. For maDLC, run with both individual and bodypart color modes when debugging. |
| `deeplabcut.create_training_dataset(config, num_shuffles=1, Shuffles=None, userfeedback=True, trainIndices=None, testIndices=None, net_type=None, detector_type=None, augmenter_type=None, engine=None, ...)` | Merge labels, create train/test splits, write trainset files and model config folders. | It dispatches to multi-animal creation when `multianimalproject: true`. It can create/overwrite shuffles; `userfeedback=True` protects existing shuffles. |
| `deeplabcut.mergeandsplit(config, trainindex=0, uniform=True)` | Get explicit train/test indices for frozen, repeated, or leave-one-folder-out splits. | Returns indices only; pass them into `create_training_dataset` to create files. |
| `deeplabcut.create_training_dataset_from_existing_split(config, from_shuffle, from_trainsetindex=0, shuffles=[...], net_type=None, engine=None, ...)` | Create new shuffles with the same split as an existing shuffle. | Requires existing `metadata.yaml` and documentation pickle for the source shuffle. |
| `deeplabcut.create_training_model_comparison(config, trainindex=0, num_shuffles=1, net_types=[...], augmenter_types=[...], userfeedback=False)` | Create multiple shuffles for architecture/augmentation comparisons using the same split. | Can create many shuffles and a comparison log. Check engine/model compatibility first. |
| `deeplabcut.convertcsv2h5(config, userfeedback=True, scorer=None)` | Convert edited or externally generated annotation CSV files to HDF. | The CSV header and row index must match DeepLabCut format. `scorer` rewrites the scorer level. |
| `deeplabcut.convert2_maDLC(config, userfeedback=True, forceindividual=None)` | Convert older single-animal labels to multi-animal label tables. | Requires maDLC fields in `config.yaml`; creates `singleanimal` backups and overwrites active label files. |

## Workflow 1: Extract frames safely

1. Confirm that every desired video is in `config.yaml` `video_sets` and has a unique stem.
2. Set `numframes2pick`, `start`, and `stop` in `config.yaml` so extraction samples the relevant behavior window.
3. Choose the extraction method:
   - `algo="uniform"`: faster and good when behavior/postures are spread through the video.
   - `algo="kmeans"`: slower but useful when visually diverse postures are sparse; tune `cluster_step`, `cluster_resizewidth`, and `cluster_color` for long or color-critical videos.
   - `mode="manual"`: use only in an interactive session with GUI support.
4. Run automatic extraction for all configured videos or a selected subset:

```python
import deeplabcut

config_path = "<project>/config.yaml"
deeplabcut.extract_frames(
    config_path,
    mode="automatic",
    algo="kmeans",
    crop=False,
    userfeedback=False,
    videos_list=None,  # or a list of configured video paths
)
```

5. Inspect `labeled-data/<video-stem>/` for extracted `img*.png` files before opening the labeling GUI.

Cautions:

- `crop=True` uses crop coordinates from `config.yaml`; `crop="GUI"` asks the user to draw them.
- If extracted frames are too similar, delete unwanted images before labeling or extract additional frames from specific videos.
- For multi-animal projects, include frames with close interactions and occlusions; automatic sampling alone often misses rare interactions.

## Workflow 2: Check labels before creating a trainset

Run this after labeling with the GUI, importing external annotations, converting CSVs, or converting single-animal labels to maDLC.

```python
import deeplabcut

config_path = "<project>/config.yaml"
deeplabcut.check_labels(config_path, draw_skeleton=True)
```

For multi-animal projects, inspect both color modes:

```python
deeplabcut.check_labels(config_path, visualizeindividuals=True)
deeplabcut.check_labels(config_path, visualizeindividuals=False)
```

Expected output: each `labeled-data/<video-stem>/` folder gains rendered label-check images in a labeled-output subfolder. Review those images manually before creating shuffles.

If labels are wrong, do not create a training dataset yet. Reopen the labeling GUI or edit/import labels, save, regenerate HDF if needed, and rerun `check_labels`.

## Workflow 3: Create the first training dataset shuffle

Use this when labels have passed visual checks and you only need the trainset and model configuration files.

```python
import deeplabcut

config_path = "<project>/config.yaml"
splits = deeplabcut.create_training_dataset(
    config_path,
    num_shuffles=1,
    userfeedback=True,
    engine=deeplabcut.Engine.PYTORCH,  # omit if config.yaml already selects the engine
)
print(splits)
```

Expected outputs:

- Merged `training-datasets/iteration-<n>/UnaugmentedDataSet_<Task><date>/CollectedData_<scorer>.h5/.csv`.
- Shuffle data and documentation files under that trainset folder.
- `metadata.yaml` under that trainset folder.
- A corresponding `dlc-models-pytorch/.../<Task><date>-trainset<percent>shuffle<id>/train/` and `test/` folder for PyTorch, or `dlc-models/...` for TensorFlow.

Boundary: after this point, route training, evaluating, and analyzing videos to the training/evaluation sub-skill.

## Workflow 4: Create a frozen or leave-one-folder-out split

Use `mergeandsplit` when the exact train/test indices matter.

Uniform split using `TrainingFraction[0]`:

```python
import deeplabcut

config_path = "<project>/config.yaml"
train_idx, test_idx = deeplabcut.mergeandsplit(config_path, trainindex=0, uniform=True)
deeplabcut.create_training_dataset(
    config_path,
    Shuffles=[3],
    trainIndices=[train_idx],
    testIndices=[test_idx],
    userfeedback=True,
)
```

Leave one video folder out:

```python
train_idx, test_idx = deeplabcut.mergeandsplit(config_path, trainindex=0, uniform=False)
deeplabcut.create_training_dataset(
    config_path,
    Shuffles=[4],
    trainIndices=[train_idx],
    testIndices=[test_idx],
    userfeedback=True,
)
```

Use leave-one-folder-out to test generalization to a held-out session or camera/video folder. Ensure there are enough labels outside the held-out folder before training.

## Workflow 5: Reuse an existing split for comparisons

Preferred DeepLabCut 3 method:

```python
import deeplabcut

config_path = "<project>/config.yaml"
deeplabcut.create_training_dataset_from_existing_split(
    config_path,
    from_shuffle=1,
    from_trainsetindex=0,
    shuffles=[10, 11, 12],
    net_type="resnet_50",
    userfeedback=True,
    engine=deeplabcut.Engine.PYTORCH,
)
```

Use this to compare architectures or hyperparameters without changing which images are in train and test. If the source shuffle is missing from `metadata.yaml` or its documentation pickle is gone, recreate the source shuffle or repair metadata before copying the split.

Legacy comparison helper:

```python
shuffle_ids = deeplabcut.create_training_model_comparison(
    config_path,
    trainindex=0,
    num_shuffles=1,
    net_types=["resnet_50", "resnet_101"],
    augmenter_types=["imgaug"],
    userfeedback=False,
)
```

This helper can create several shuffles in one call. Confirm model/augmenter compatibility with the selected engine before using it in an expensive run.

## Workflow 6: Import external labels through CSV/HDF

1. Create or reuse a project whose `config.yaml` bodypart names exactly match the external labels.
2. For each video or image set, create `labeled-data/<video-stem>/` and place images there.
3. Write `CollectedData_<scorer>.csv` or `.h5` with the DeepLabCut row and column layout described in the data-format reference.
4. Ensure `video_sets` includes a video path whose stem matches each label folder; a dummy video entry can be enough for format conversion, but real videos are needed for normal extraction and later analysis workflows.
5. Convert CSVs to HDF when needed:

```python
import deeplabcut

deeplabcut.convertcsv2h5(
    "<project>/config.yaml",
    userfeedback=False,
    scorer="<config-scorer>",
)
```

6. Run `check_labels` before creating any trainset.

## Workflow 7: Convert a single-animal project to maDLC labels

Use when existing single-animal `CollectedData_<scorer>.h5/.csv` files should become multi-animal-style labels.

1. Back up the project.
2. Edit `config.yaml` to include multi-animal fields:

```yaml
multianimalproject: true
bodyparts: MULTI!
individuals:
  - animal_0
uniquebodyparts: []
multianimalbodyparts:
  - nose
  - tailbase
identity: false
```

3. Convert labels:

```python
import deeplabcut

deeplabcut.convert2_maDLC(
    "<project>/config.yaml",
    userfeedback=True,
    forceindividual=None,  # or a configured individual name
)
```

4. Confirm that `CollectedData_<scorer>singleanimal.h5/.csv` backups exist.
5. Run `check_labels` in both multi-animal color modes.
6. Create a training dataset only after the converted labels look correct.

## Workflow 8: Generate a tiny safe fixture project

The bundled script creates a disposable standard or multi-animal DeepLabCut-style project with config, images, video, HDF labels, and CSV labels. It does not import DeepLabCut, train, download models, or open a GUI.

```bash
python scripts/create_tiny_dlc_project.py ./tiny-dlc-standard --mode standard
python scripts/create_tiny_dlc_project.py ./tiny-dlc-multi --mode multianimal
python scripts/create_tiny_dlc_project.py ./tiny-dlc-both --mode both
```

Useful checks with a DeepLabCut installation:

```python
import deeplabcut

config_path = "tiny-dlc-standard/config.yaml"
deeplabcut.check_labels(config_path)
deeplabcut.convertcsv2h5(config_path, userfeedback=False, scorer="synthetic")
# Optional format smoke; this creates config files but does not train.
deeplabcut.create_training_dataset(config_path, userfeedback=False)
```

Delete tiny fixtures when finished. They are intentionally too small for meaningful model quality.
