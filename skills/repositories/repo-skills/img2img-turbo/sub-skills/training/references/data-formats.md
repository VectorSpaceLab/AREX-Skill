# Training Data Formats

This reference captures the data contracts used by the paired Pix2Pix-Turbo and unpaired CycleGAN-Turbo training loaders. Validate data before launching training with the bundled [validator](../scripts/validate_training_dataset.py).

## Paired Pix2Pix-Turbo dataset

Use this schema when every conditioning image has a corresponding target image and a text prompt.

```text
data/
└── <dataset_name>/
    ├── train_A/
    │   ├── 000000.png
    │   ├── 000001.png
    │   └── ...
    ├── train_B/
    │   ├── 000000.png
    │   ├── 000001.png
    │   └── ...
    ├── train_prompts.json
    ├── test_A/
    │   ├── 000000.png
    │   ├── 000001.png
    │   └── ...
    ├── test_B/
    │   ├── 000000.png
    │   ├── 000001.png
    │   └── ...
    └── test_prompts.json
```

### Paired prompt JSON

`train_prompts.json` and `test_prompts.json` are JSON objects mapping exact image names to captions:

```json
{
  "000000.png": "violet circle with orange background",
  "000001.png": "blue square with yellow background"
}
```

Loader behavior to preserve:

- For `split="train"`, the loader opens `<dataset>/train_A/<json-key>` and `<dataset>/train_B/<json-key>`.
- For `split="test"`, the loader opens `<dataset>/test_A/<json-key>` and `<dataset>/test_B/<json-key>`.
- The JSON keys define the paired examples. Extra images in the directories are ignored by the loader unless they are named in the JSON.
- Missing files named by a prompt key fail later with file-open errors; catch them with the validator first.
- Prompt values are tokenized as captions. Use non-empty strings; very long captions are truncated by the tokenizer at its model maximum length.

### Paired image extension expectations

The paired loader does not glob by extension; it opens the exact filenames from the prompt JSON. In practice, use ordinary PIL-readable image filenames such as `.png`, `.jpg`, `.jpeg`, `.bmp`, or `.gif`, and keep the same filename in `A` and `B` for each prompt key.

The bundled validator treats missing JSON-keyed files as errors and reports unreferenced image-like files as warnings, because the source loader would ignore those extras.

## Image preparation strings

The training loaders use named transform strings:

| Name | Transform behavior |
| --- | --- |
| `resized_crop_512` | Resize shortest/target dimension to 512 with Lanczos, then center-crop 512. This is the paired train/test default. |
| `resize_286_randomcrop_256x256_hflip` | Resize to 286×286, random-crop 256×256, then random horizontal flip. This is used by the documented unpaired training command. |
| `resize_256` or `resize_256x256` | Resize to 256×256. |
| `resize_512` or `resize_512x512` | Resize to 512×512. |
| `no_resize` | Leave the image size unchanged. This is used by the documented unpaired validation/inference handoff. |

Paired conditioning images are converted to tensors in `[0, 1]`; paired target images are normalized to `[-1, 1]`. Unpaired source and target images are both normalized to `[-1, 1]` after their selected transform.

### Paired validation expectations

Before training, confirm:

1. `train_A`, `train_B`, `test_A`, and `test_B` exist.
2. `train_prompts.json` and `test_prompts.json` exist, parse as JSON objects, and are not empty.
3. Every key in each prompt JSON exists as a file in both the matching `A` and `B` split directories.
4. Captions are strings.
5. `test_B` contains the target-domain validation images if `--track_val_fid` will be used, because the paired training loop computes FID reference features from `test_B` only when that flag is enabled.

Example validation command from this `training/` sub-skill directory:

```bash
python sub-skills/training/scripts/validate_training_dataset.py --mode paired --dataset-folder data/my_fill50k
```

## Unpaired CycleGAN-Turbo dataset

Use this schema when source-domain and target-domain images are not paired one-to-one.

```text
data/
└── <dataset_name>/
    ├── train_A/
    │   ├── 000000.jpg
    │   ├── 000001.jpg
    │   └── ...
    ├── train_B/
    │   ├── 000000.jpg
    │   ├── 000001.jpg
    │   └── ...
    ├── fixed_prompt_a.txt
    ├── fixed_prompt_b.txt
    ├── test_A/
    │   ├── 000000.jpg
    │   ├── 000001.jpg
    │   └── ...
    └── test_B/
        ├── 000000.jpg
        ├── 000001.jpg
        └── ...
```

`fixed_prompt_a.txt` contains the fixed caption for domain A, and `fixed_prompt_b.txt` contains the fixed caption for domain B. For example, in a horse-to-zebra run, domain A may be horses and domain B may be zebras; A→B validation/inference uses the target-domain prompt from `fixed_prompt_b.txt`.

### Unpaired image extension rules

The unpaired loader and validation code use extension globs instead of prompt JSON keys:

- Training split directories `train_A` and `train_B` are scanned for top-level `*.jpg`, `*.jpeg`, `*.png`, `*.bmp`, and `*.gif` files.
- Validation/test directories `test_A` and `test_B` are scanned by the training script for top-level `*.jpg`, `*.jpeg`, `*.png`, and `*.bmp` files.
- Uppercase extensions such as `.JPG` are not matched by those lowercase glob patterns on case-sensitive filesystems. Rename to lowercase extensions for predictable training.
- Validation GIFs are not collected by the training script; use `.jpg`, `.jpeg`, `.png`, or `.bmp` in `test_A` and `test_B`.

### Unpaired validation expectations

Before training, confirm:

1. `train_A`, `train_B`, `test_A`, and `test_B` exist.
2. `fixed_prompt_a.txt` and `fixed_prompt_b.txt` exist and are non-empty.
3. `train_A` and `train_B` each contain at least one image with a training-supported extension.
4. `test_A` and `test_B` each contain at least one image with a validation-supported extension, because FID reference features are prepared from both validation domains at startup.
5. Domain direction is recorded: `a2b` means A→B and should use the target-domain prompt; `b2a` means B→A and should use the source-domain prompt.

Example validation command from this `training/` sub-skill directory:

```bash
python sub-skills/training/scripts/validate_training_dataset.py --mode unpaired --dataset-folder data/my_horse2zebra
```

## Example dataset destinations

The safe downloader preserves the source dataset names:

- `--dataset fill50k --output-dir data` extracts a paired example dataset expected at `data/my_fill50k`.
- `--dataset horse2zebra --output-dir data` extracts an unpaired example dataset expected at `data/my_horse2zebra`.

It requires `--yes` before network download/extraction:

```bash
bash sub-skills/training/scripts/download_example_dataset.sh --dataset fill50k --output-dir data --yes
bash sub-skills/training/scripts/download_example_dataset.sh --dataset horse2zebra --output-dir data --yes
```
