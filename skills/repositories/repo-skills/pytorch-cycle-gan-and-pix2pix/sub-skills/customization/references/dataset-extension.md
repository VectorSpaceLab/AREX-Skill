# Dataset extension contract

This repository discovers datasets from the `--dataset_mode` value. A custom dataset selected with `--dataset_mode my_data` must be present as `data/my_data_dataset.py` and must define a class whose name normalizes to `MyDataDataset` under the repository's case-insensitive, underscore-stripping lookup.

Use [`../scripts/check_extension_names.py`](../scripts/check_extension_names.py) for a safe import-free name check before trying the training or test parser. Choose a Python-module-safe registry name: letters, digits, and underscores, with no leading digit or dash.

## Required naming and inheritance

| Item | Contract |
| --- | --- |
| CLI selector | `--dataset_mode <mode>` |
| Python file | `data/<mode>_dataset.py` |
| Class | `<Mode>Dataset`, for example `my_data` -> `MyDataDataset` |
| Base class | direct or compatible subclass of `BaseDataset` |
| Import behavior | the registry imports `data.<mode>_dataset` and searches for a matching dataset class |

The lookup strips underscores from `<mode>`, appends `dataset`, and compares class names case-insensitively. Therefore `my_data_dataset.py` must contain a class whose normalized name is `mydatadataset`; `MyDataset` is not sufficient.

## Required methods

| Method | Purpose | Safe pattern |
| --- | --- | --- |
| `modify_commandline_options(parser, is_train)` | Optional static hook to add dataset flags or set data-specific defaults. | Set data-layout/channel defaults here and return the parser. |
| `__init__(self, opt)` | Save options, collect paths, build transforms, and validate small invariants. | Call `BaseDataset.__init__(self, opt)` first so `self.opt` and `self.root` exist. |
| `__len__(self)` | Return the number of samples exposed to the dataloader. | Return a deterministic integer; for two domains, return the intended paired or max length. |
| `__getitem__(self, index)` | Load one sample and return a dictionary of tensors and metadata. | Return CPU tensors and strings/paths; the model moves tensors to `self.device` in `set_input`. |

## Data dictionary contracts

The dataset dictionary must match the model's `set_input`. Existing models use these conventions:

| Model family | Expected keys | Notes |
| --- | --- | --- |
| CycleGAN-style unpaired translation | `A`, `B`, `A_paths`, `B_paths` | `A` and `B` are domain tensors; `--direction BtoA` swaps which domain is treated as input. |
| pix2pix-style paired translation | `A`, `B`, `A_paths`, `B_paths` | `A` is input and `B` is target for `AtoB`; transforms should preserve spatial alignment. |
| colorization | `A`, `B`, `A_paths`, `B_paths` | `A` is the L channel (`input_nc=1`); `B` is Lab `ab` channels (`output_nc=2`). |
| one-sided test model | `A`, `A_paths` | Used for generator-only inference on one collection. |
| custom model | Whatever `set_input` consumes | Either emit the standard keys above or update `set_input` and all visuals/losses that depend on them. |

A common safe path for new paired image datasets is to emit standard `A`/`B` keys so an existing pix2pix-like model can be reused. A common safe path for new one-sided inference datasets is to emit `A`/`A_paths` so the test model contract is satisfied.

## Image loading and transforms

The base data utilities provide reusable behavior:

- Recursive image discovery accepts common image extensions such as JPG, JPEG, PNG, PPM, BMP, TIF, and TIFF with upper- and lower-case variants.
- The default image loader converts images to RGB.
- `get_transform(opt, grayscale=False, convert=True)` applies resize/scale/crop/no-op sizing, optional horizontal flip, tensor conversion, and normalization to `[-1, 1]`.
- Use `get_params(opt, image.size)` once for paired data and pass the same params to both domain transforms so random crop and flip stay aligned.
- Use `grayscale=True` when `input_nc` or `output_nc` is `1`; otherwise RGB normalization expects three channels.
- `--preprocess none` rounds image dimensions to a multiple of 4; `resize_and_crop` and crop-based modes assume `load_size >= crop_size`.

## Dataset defaults

Use `modify_commandline_options` for data-owned defaults. Examples of safe ownership:

| Dataset need | Prefer setting |
| --- | --- |
| Lab colorization split | `input_nc=1`, `output_nc=2`, `direction="AtoB"` |
| Bounded toy/template dataset | `max_dataset_size` or a dataset-specific option |
| Grayscale-only input | `input_nc=1` and matching transforms |
| Dataset-specific path convention | a new `--<dataset>_...` option with a clear default |

If a model and dataset both set the same option, the dataset hook is applied after the model hook. Use [`option-registry.md`](option-registry.md) to decide where the default belongs and document the coupling.

## Minimal review checklist

- File and class name pass [`../scripts/check_extension_names.py`](../scripts/check_extension_names.py).
- `BaseDataset.__init__(self, opt)` is called first.
- `__len__` cannot return zero for the intended data root.
- `__getitem__` returns all keys consumed by the model `set_input`.
- Tensor channel counts match `--input_nc` and `--output_nc` after any `--direction` swap.
- Paired crops/flips share transform params; unpaired data may randomize domains independently.
- Raw data layout, pair conversion, and dataset asset download issues are routed to [`data-preparation`](../../data-preparation/SKILL.md).
