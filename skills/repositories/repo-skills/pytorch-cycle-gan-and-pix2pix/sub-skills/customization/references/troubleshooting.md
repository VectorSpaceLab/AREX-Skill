# Customization troubleshooting

Use the name checker first, then compare the model's `set_input` contract with the dataset dictionary. Do not start a full training run until the parser can import both classes and the option defaults agree with the tensor shapes.

| Symptom or error | Likely cause | Fix |
| --- | --- | --- |
| `In models.<name>_model.py, there should be a subclass of BaseModel...` followed by an immediate exit | The file is missing, the class stem is wrong, or the class does not inherit from `BaseModel`. The model registry currently reports this mismatch with `exit(0)`, so an apparently successful process can still have created no model. | Use `models/<name>_model.py`; define `<Mode>Model` with the normalized name `<name>` + `Model`; inherit from `BaseModel`; run [`../scripts/check_extension_names.py`](../scripts/check_extension_names.py). |
| `NotImplementedError: In data.<name>_dataset.py, there should be a subclass of BaseDataset...` | Dataset file/class mismatch or missing `BaseDataset` inheritance. | Use `data/<name>_dataset.py`; define `<Mode>Dataset`; call `BaseDataset.__init__(self, opt)`; rerun the checker. |
| `ModuleNotFoundError` for the custom module | The file is not under the repository's `models/` or `data/` package, the selector contains a typo, or the package is being invoked from a different checkout than expected. | Verify the selector, file location, and active repository before changing Python import settings. Do not rename only the class; the filename must also match. |
| `KeyError: 'A'`, `KeyError: 'B'`, `KeyError: 'A_paths'`, or `KeyError: 'B_paths'` in `set_input` | The dataset dictionary does not contain the keys consumed by the selected model. | Either return the standard keys from `__getitem__` or change `set_input` to consume the custom schema. Keep path keys if the visualizer/results code needs source names. |
| Model construction succeeds, then `AttributeError` appears while collecting visuals or losses | A name in `visual_names` or `loss_names` does not correspond to `self.<name>` or `self.loss_<name>` for the current code path. | Make the lists conditional when outputs differ between train/test, or define every listed attribute before `get_current_visuals()` / `get_current_losses()` is called. |
| Setup/save/load reports a missing `net...` attribute | A string in `model_names` has no matching `self.net<name>` attribute, or a suffix was added to the list but not to the attribute. | Align `model_names`, network attributes, and checkpoint names. For suffix-based test loading, use both `self.netG<suffix>` and `"G<suffix>"`. |
| `RuntimeError` or `size mismatch` while loading a checkpoint | Training and test used different `netG`, `netD`, `norm`, `input_nc`, `output_nc`, generator depth, dropout, or model suffix. | Reuse the exact architecture/channel defaults used to create the checkpoint. If the custom contract changed, use a new experiment/checkpoint directory rather than forcing incompatible weights. |
| `AssertionError` in a colorization-like dataset | The dataset expects `input_nc=1`, `output_nc=2`, or `direction=AtoB`, but a model hook or CLI override changed them. | Let the dataset hook set those defaults, then confirm the final parser output. Only override them when the custom model and data dictionary are changed together. |
| `RuntimeError` from convolution channel mismatch during `forward` | Dataset tensors and `--input_nc`/`--output_nc` disagree, or `--direction BtoA` swaps the effective channel counts. | Inspect the actual tensor shapes returned by `__getitem__`, compute the effective input/output channels after direction handling, and update transforms plus parser defaults together. |
| `Expected all tensors to be on the same device` or a CPU/GPU mismatch in the model | `set_input` kept dataset tensors on CPU, or a custom tensor created in `forward`/loss code was not placed on `self.device`. | Move incoming tensors with `.to(self.device)` in `set_input`; create new tensors on `self.device` or derive them from existing tensors. The dataset should normally return CPU tensors. |
| `self.device` or `self.isTrain` is missing | `BaseModel.__init__(self, opt)` was skipped or called after network/loss setup. | Call the base initializer first in `__init__`; then define lists, networks, losses, and optimizers. |
| Defaults appear to be ignored | The wrong selector was parsed, a model setter changed `dataset_mode`, or the dataset setter overwrote a shared default later in the parse sequence. | Review [`option-registry.md`](option-registry.md); inspect the final parsed values, not only the base parser defaults; move ownership of shared defaults to one hook. |
| A custom model trains but the test parser selects an unexpected dataset | The model hook sets a training-oriented `dataset_mode` for both phases, or `TestOptions`/`TestModel` defaults were not considered. | Use `is_train` in the model hook and define an explicit test-time dataset contract. For one-sided inference, the test model's single-image contract expects `A` and `A_paths`. |
| DDP or synchronized normalization fails after customization | The custom model changed `norm` without keeping the distributed/runtime path consistent, or the checkpoint was created with another normalization layer. | Keep normalization spelling and behavior consistent with the active repository runtime; validate CPU/parser behavior first and route complete DDP command construction to [`translation-workflows`](../../translation-workflows/SKILL.md). |

## Two high-value synthetic diagnoses

### 1. `my_data_dataset.py` with `MyDataset`

Run the helper with `--kind dataset --name my_data` and an optional repository root. It should report the expected file `my_data_dataset.py` and class `MyDataDataset`, then fail the text check because `MyDataset` normalizes to `mydataset`, not `mydatadataset`. Rename the class to `MyDataDataset` or change the selector/file name consistently; do not patch the registry lookup.

### 2. Grayscale pix2pix-like path

For a grayscale input and two-channel target, make the dataset emit `A` with one channel and `B` with two channels, set `input_nc=1`, `output_nc=2`, and keep `direction=AtoB`. The model's `set_input` must still read `A`, `B`, `A_paths`, and `B_paths`, and its generator/discriminator definitions must use the same channel counts. If a conditional discriminator concatenates input and output, its input channel count is `1 + 2 = 3`. A mismatch usually surfaces first as a convolution channel error or a checkpoint state-dict mismatch.

## Escalation boundaries

- Finished train/test/inference commands, checkpoint downloads, and backend selection: [`translation-workflows`](../../translation-workflows/SKILL.md).
- Raw data roots, pair conversion, image layout, and asset acquisition: [`data-preparation`](../../data-preparation/SKILL.md).
- New architecture design not implied by the bundled factory/template contract: record the unresolved design as a long-tail gap instead of inventing a generic recipe here.
