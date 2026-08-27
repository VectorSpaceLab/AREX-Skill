# Options and configuration

This reference collects the option defaults that directly affect data loading and the smoke checks in this sub-skill.

## Parsing rules

- `BaseOptions.parse()` prints the parsed configuration, sets CUDA device IDs when `gpu_ids` is not `-1`, and creates `<checkpoints_dir>/<name>`.
- `save=False` suppresses `opt.txt` writes, but it does not suppress the directory creation side effect.
- `TrainOptions` adds `continue_train`; `TestOptions` does not.
- For that reason, parser smoke and utility scripts should call `TestOptions().parse(save=False)`.

## Data-affecting defaults

| Option | Default | Why it matters |
| --- | --- | --- |
| `dataroot` | `./datasets/cityscapes/` | Root used by `AlignedDataset` to build the phase folders. |
| `phase` | `train` for training, `test` for testing | Chooses `train_*` vs `test_*` folders. |
| `label_nc` | `35` | Selects label-map loading and the Cityscapes colormap path. |
| `no_instance` | `False` | Keeps instance maps in the loader path. |
| `use_encoded_image` | `False` | Controls whether test-time image folders are required. |
| `load_features` | `False` | Adds the optional `<phase>_feat` lookup; detailed cache layout lives in instance-features. |
| `batchSize` | `1` | Tiny smoke fixtures should keep this at 1 so `AlignedDataset.__len__` does not floor the sample count to zero. |
| `nThreads` | `2` | Fine for normal runs; smoke scripts usually lower it to 0 or 1. |
| `serial_batches` | `False` | Training shuffles by default; test smoke usually sets this to `True`. |
| `no_flip` | `False` | Training defaults to random flip; test smoke usually sets this to `True`. |
| `loadSize` | `1024` | Used by `scale_width` and `scale_width_and_crop`. |
| `fineSize` | `512` | Used by crop modes. |
| `resize_or_crop` | `scale_width` | Safe default for modern torchvision and the bundled smoke fixture. |
| `netG` | `global` | Affects the `none` preprocessing path because the power-of-two rounding depends on the generator topology. |
| `n_downsample_global` | `4` | Used by the `none` preprocessing path to choose the rounding base. |
| `n_local_enhancers` | `1` | Also affects the `none` preprocessing path when `netG=local`. |
| `max_dataset_size` | `inf` | Prevents artificial truncation unless a smoke script overrides it. |
| `gpu_ids` | `0` | Pass `-1` for CPU-only data checks. |

## Safe smoke overrides

Use these overrides when validating the bundled fixture:

- `--gpu_ids -1`
- `--checkpoints_dir <scratch>`
- `--results_dir <scratch>`
- `--batchSize 1`
- `--nThreads 0` for data-only smoke or `1` for test-style smoke
- `--serial_batches` and `--no_flip` for test-style smoke
- `save=False` when parsing `TestOptions`

## Legacy resize-and-crop caveat

`data/base_dataset.py` still contains the `resize_and_crop` branch that calls `torchvision.transforms.Scale`.

On modern torchvision releases such as 0.28.0, `Scale` is gone. The safe choices are:

- keep the default `scale_width`
- use `scale_width_and_crop` or `crop` when you need cropping
- use `none` when you want the loader to round dimensions to a multiple of the generator base
- patch the loader to `torchvision.transforms.Resize` if you must preserve the legacy `resize_and_crop` behavior

## Shape and transform notes

- `AlignedDataset` returns `label`, `inst`, `image`, `feat`, and `path`
- the train smoke should see `image` as a real tensor and the test smoke should see `image=0` unless `use_encoded_image` is enabled
- `tensor2label` uses the Cityscapes color map when `label_nc=35`
- `tensor2im` expects normalized image tensors and returns an RGB numpy array
