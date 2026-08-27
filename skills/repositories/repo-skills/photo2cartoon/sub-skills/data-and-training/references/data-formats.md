# Data Formats

## Split layout

The trainer expects four domain folders under the dataset root:

| Split | Role | Loader behavior |
|---|---|---|
| `trainA` | Portrait domain for training | Shuffled, batched with `--batch_size` |
| `trainB` | Cartoon domain for training | Shuffled, batched with `--batch_size` |
| `testA` | Portrait domain for evaluation | Batch size `1`, no shuffle |
| `testB` | Cartoon domain for evaluation | Batch size `1`, no shuffle |

The code instantiates all four loaders unconditionally, so a missing split will fail before training begins. Training is unpaired: each step draws a batch from `trainA` and a batch from `trainB` independently, so filenames do not need to match across domains.

## Supported image files

`dataset.py` accepts the same suffix set as the bundled validator:

- `.jpg`
- `.jpeg`
- `.png`
- `.ppm`
- `.bmp`
- `.pgm`
- `.tif`

Matching is case-insensitive because the loader lowercases filenames before checking the suffix.

## `ImageFolder` contract

`ImageFolder(root)` in this repo is a simple recursive image list:

- it walks every subdirectory under `root`
- it keeps every file whose final suffix matches the extension list above
- it returns `PIL.Image.convert('RGB')`
- it assigns a constant target value of `0` for every sample
- it raises `RuntimeError("Found 0 files in subfolders of: ...")` when no supported files are found

Implications:

- split names, not class labels, define the data domain
- nested folders are allowed
- unsupported files are ignored by the loader and may lead to an empty split

## Batch preprocessing output

The batch preprocessor source behavior is exposed through the bundled preprocessing command builder. Use it to validate paths and print the source-compatible command instead of copying an unchecked command by hand:

```bash
python ../preprocessing/scripts/build_preprocess_command.py \
  --repo-root /path/to/photo2cartoon-checkout \
  --data-path /path/to/raw-portrait-folder \
  --save-path /path/to/preprocessed-output-folder
```

Add `--execute` only after preprocessing assets and dependencies are verified.

Expected source behavior:

- read each source image with OpenCV
- expect a flat input folder of readable image files; the script iterates `os.listdir(...)` and does not recurse into subdirectories
- convert OpenCV BGR input to RGB before face preprocessing
- run the face alignment / segmentation pipeline
- skip an input when preprocessing returns `None`
- replace the background with white
- save a sequential zero-padded PNG such as `0000.png`, `0001.png`, ...

Important notes:

- output filenames do not preserve the original source names
- output order follows the source directory traversal order
- the saved folder can be smaller than the input folder if face detection fails on some images

The generated portraits belong in `trainA` / `testA`; the cartoon-side data belongs in `trainB` / `testB`.

## Validation checks before training

Run the bundled checker against the dataset root that contains the four splits:

```bash
python scripts/validate_dataset_layout.py --dataset-root /path/to/dataset/photo2cartoon
```

For stricter reviews:

```bash
python scripts/validate_dataset_layout.py --dataset-root /path/to/dataset/photo2cartoon --check-images --strict
```

Use this to catch:

- missing split folders
- zero supported images in a split
- unsupported extensions
- corrupted images when `--check-images` is enabled

The helper exits non-zero when fatal errors are present, and `--json` emits a machine-readable summary when you want to automate the check.
