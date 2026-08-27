# Dataset layout

## ImageNet code cache

- Input root: an ImageFolder-style tree with class subdirectories.
- Output root: `${code_path}/imagenet${image_size}_codes/` and `${code_path}/imagenet${image_size}_labels/`.
- Code payload shape: `[1, augmentation_count, token_count]` where `augmentation_count` is `2` for flip mode and `10` for ten-crop mode.
- Label payload shape: `[1]`.
- File naming: dense integer filenames such as `0.npy`, `1.npy`, `2.npy`, ...
- Consumer: `dataset/imagenet.py::build_imagenet_code`.

## T5 feature cache

- Input root: a directory of `.jsonl` files.
- Output root: `${t5_path}/<jsonl_stem>/<line_index>.npy`.
- Payload shape: `[1, token_count, 2048]` after trimming to the valid attention length.
- The `line_index` is the row number inside the source `.jsonl` file.
- `short_t5_feat_path` should mirror the same subfolder names and filename convention as `t5_feat_path`.
- Consumer: `dataset/t2i.py`.

## OpenImages manifest

- Manifest path: `${data_path}/image_paths.json` by default.
- Entries are relative paths such as `openimages_0001/000123.jpg`.
- The loader joins each entry against `data_path` before opening the image.
- Default folder scan range: `openimages_0001` through `openimages_0047`.

## Common layout mistakes

- Using a flat folder with the ImageNet extractor.
- Writing T5 features to a directory whose basename does not match the `.jsonl` stem.
- Renaming a T5 cache root without keeping the same nested subfolder names.
- Leaving a partial `.npy` tree with gaps in the numeric filenames.
- Writing OpenImages manifest entries as absolute paths instead of relative ones.
