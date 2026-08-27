# Feature Extraction Workflows

## Fast Coordinate-Based Pipeline

The current CLAM feature path is `extract_features_fp.py`. It expects patch-coordinate files produced by the fast WSI preprocessing pipeline and reads image regions on demand from the original whole-slide images.

Use this command shape for a full run:

```bash
CUDA_VISIBLE_DEVICES=0 python extract_features_fp.py \
  --data_h5_dir DIR_TO_COORDS \
  --data_slide_dir DATA_DIRECTORY \
  --csv_path CSV_FILE_NAME \
  --feat_dir FEATURES_DIRECTORY \
  --slide_ext .svs \
  --model_name resnet50_trunc \
  --batch_size 512 \
  --target_patch_size 224 \
  --no_auto_skip
```

Omit `--no_auto_skip` for the default behavior: CLAM skips a slide when `FEATURES_DIRECTORY/pt_files/<slide_id>.pt` already exists.

## Required Inputs

- `--data_h5_dir`: parent directory containing `patches/<slide_id>.h5` coordinate files.
- `--data_slide_dir`: directory containing readable WSI files named `<slide_id><slide_ext>`.
- `--csv_path`: CSV file with a `slide_id` column; bare slide IDs are safest, and values with the exact `--slide_ext` are stripped by CLAM before path construction.
- `--feat_dir`: output directory where CLAM creates `h5_files/` and `pt_files/`.
- `--slide_ext`: slide suffix used to strip CSV names and reconstruct WSI filenames, for example `.svs`.
- `--model_name`: one of `resnet50_trunc`, `uni_v1`, or `conch_v1`; see `encoder-reference.md` before choosing UNI or CONCH.
- `--batch_size`: number of patches per inference batch; reduce this first for CUDA memory failures.
- `--target_patch_size`: resize target passed to CLAM evaluation transforms; current examples use `224`.

## What CLAM Does Internally

1. `Dataset_All_Bags` reads `csv_path` and returns each row's `slide_id`.
2. For each row, CLAM computes `slide_id = value.split(slide_ext)[0]`.
3. It expects the coordinate file at `data_h5_dir/patches/<slide_id>.h5`.
4. It expects the slide file at `data_slide_dir/<slide_id><slide_ext>` and opens it with OpenSlide.
5. `Whole_Slide_Bag_FP` reads the HDF5 `coords` dataset and uses its `patch_level` and `patch_size` attributes to crop patches from the slide.
6. `get_encoder(model_name, target_img_size=target_patch_size)` loads the encoder and image transforms.
7. CLAM writes an HDF5 file containing `features` and `coords`, then writes a `.pt` tensor containing only features for faster MIL training.

## Output Layout

A successful run produces this structure:

```text
FEATURES_DIRECTORY/
  h5_files/
    slide_1.h5
    slide_2.h5
  pt_files/
    slide_1.pt
    slide_2.pt
```

Each `h5_files/<slide_id>.h5` stores patch `features` plus `coords`. Each `pt_files/<slide_id>.pt` stores the feature tensor used by CLAM training, evaluation, and heatmap workflows.

## Downstream Data Root Layout

Training and evaluation expect a dataset feature directory that contains `pt_files/` below the task-specific data directory. A common layout is:

```text
DATA_ROOT_DIR/
  my_dataset_features/
    h5_files/
      slide_1.h5
    pt_files/
      slide_1.pt
```

When adapting CLAM training/evaluation commands, make `--data_root_dir` point to the parent root expected by the task code and ensure the task-specific dataset path resolves to the feature directory containing `pt_files/`. Use `../training-evaluation/SKILL.md` for dataset CSVs, split files, and task-specific command flags.

## Practical Recipes

### UNI Features

- Request and download UNI weights outside this skill according to the model provider's access rules.
- Set `UNI_CKPT_PATH` to the downloaded `pytorch_model.bin` before running CLAM.
- Use `--model_name uni_v1` and start with a smaller batch size than ResNet if GPU memory is limited.
- Use downstream `--embed_dim 1024` for CLAM training, evaluation, and heatmaps.

### CONCH Features

- Install the optional CONCH package in the CLAM environment and set `CONCH_CKPT_PATH` to the downloaded checkpoint.
- Use `--model_name conch_v1` and reduce `--batch_size` if memory is tight.
- Use downstream `--embed_dim 512`; shape mismatches during training commonly mean a CONCH feature bag is being loaded with a 1024-dimensional model configuration.
