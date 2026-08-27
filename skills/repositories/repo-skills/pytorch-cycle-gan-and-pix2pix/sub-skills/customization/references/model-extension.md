# Model extension contract

This repository discovers models by registry name, not by a hand-written registry table. A custom model selected with `--model my_model` must be present as `models/my_model_model.py` and must define a subclass whose name normalizes to `MyModelModel` under the repository's case-insensitive, underscore-stripping lookup.

Use the checker in [`../scripts/check_extension_names.py`](../scripts/check_extension_names.py) when in doubt. Choose a Python-module-safe registry name: letters, digits, and underscores, with no leading digit or dash.

## Required naming and inheritance

| Item | Contract |
| --- | --- |
| CLI selector | `--model <model>` |
| Python file | `models/<model>_model.py` |
| Class | `<Model>Model`, for example `my_data` -> `MyDataModel` |
| Base class | direct or compatible subclass of `BaseModel` |
| Import behavior | the registry imports `models.<model>_model` and searches its classes without constructing every object in the package |

The registry compares class names case-insensitively after removing underscores from the model name and appending `model`. Acronym styling is flexible (`CycleGanModel` and `CycleGANModel` have the same registry key), but missing words are not flexible (`MyModel` is not a match for `my_data`).

## Required methods

Every concrete model must implement these methods:

| Method | Purpose | Safe pattern |
| --- | --- | --- |
| `modify_commandline_options(parser, is_train)` | Optional static hook to add model flags or set model defaults before final CLI parse. | Gate training-only flags with `if is_train:` and return the parser. |
| `__init__(self, opt)` | Initialize model state, lists, networks, losses, and optimizers. | Call `BaseModel.__init__(self, opt)` before touching `self.device`, `self.isTrain`, or checkpoint paths. |
| `set_input(self, input)` | Unpack a dataset dictionary into model tensors and metadata. | Move tensors with `.to(self.device)` here; set `self.image_paths` for result naming. |
| `forward(self)` | Compute generated/intermediate tensors. | Called by both `optimize_parameters` and test-time `BaseModel.test()`. |
| `optimize_parameters(self)` | Run one training update. | Call `forward`, zero gradients, compute/backprop losses, and step optimizers. Test-only models may implement this as a no-op. |

## Required lists and attribute conventions

After `BaseModel.__init__`, define these lists explicitly:

| Field | What it controls | Required matching attributes |
| --- | --- | --- |
| `self.loss_names` | Losses printed and saved by training. | For each name `X`, set `self.loss_X` before losses are collected. |
| `self.visual_names` | Images/tensors displayed and saved by train/test visualizers. | For each name `X`, set `self.X` before visuals are collected. |
| `self.model_names` | Network checkpoints to save/load and networks to initialize/print. | For each name `X`, define `self.netX`. |
| `self.optimizers` | Optimizers used to build schedulers and update learning rates. | Include every optimizer that needs a scheduler during training. |

`model_names` is also the checkpoint naming contract. A list entry `"G"` maps to `self.netG` and to files such as `<epoch>_net_G.pth`. A list entry `"G_A"` maps to `self.netG_A` and `<epoch>_net_G_A.pth`. If a one-sided test model uses a suffix, the list entry must include it (for example `"G" + opt.model_suffix`) and the matching `self.netG<suffix>` attribute must exist.

`BaseModel.setup(opt)` initializes and prints all networks named in `model_names`, loads them for test or continued training, moves them to the configured device, wraps them for distributed execution when active, and builds schedulers from `self.optimizers` during training. Keep network attributes and `model_names` consistent before setup runs.

## Network factory choices

Built-in model examples construct networks through the repository factory functions. Prefer these before writing an architecture from scratch:

| Option | Supported values | When to use or override |
| --- | --- | --- |
| `--netG` | `resnet_9blocks`, `resnet_6blocks`, `unet_128`, `unet_256` | ResNet generators are the CycleGAN default; U-Net generators are the pix2pix default. Use `resnet_6blocks` or `unet_128` for smaller/faster experiments, and keep the same value at test time as at training time. |
| `--netD` | `basic`, `n_layers`, `pixel` | `basic` is the default PatchGAN. Use `n_layers` with `--n_layers_D` to vary discriminator depth. Use `pixel` only for a 1x1 PixelGAN-style discriminator. |
| `--norm` | `instance`, `batch`, `none`, `syncbatch` | CycleGAN defaults to instance normalization; pix2pix defaults to batch normalization. Changing normalization changes module structure and checkpoint compatibility. |
| `--input_nc`, `--output_nc` | integer channel counts | Keep at `3/3` for RGB-to-RGB. Set to `1` for grayscale inputs or `2` for Lab `ab` outputs only when the dataset returns matching tensors. |

## Built-in default patterns to copy deliberately

| Model mode | Default coupling and lists |
| --- | --- |
| `cycle_gan` | Uses unaligned data, ResNet generator, instance normalization, least-squares GAN loss, no dropout, two generators (`G_A`, `G_B`) and two discriminators (`D_A`, `D_B`) during training; only generators load during test. |
| `pix2pix` | Uses aligned paired data, U-Net 256 generator, batch normalization, vanilla GAN loss, no image pool, L1 loss weight `100`, one generator `G` and one discriminator `D` during training; only `G` loads during test. |
| `colorization` | Reuses pix2pix behavior but couples to the colorization dataset, with `input_nc=1`, `output_nc=2`, and Lab-to-RGB visualization outputs. |
| `test` | Test-only generator application; automatically selects single-image data and loads only generator `G` plus optional `model_suffix`. |
| `template` | Minimal regression-style paired-image baseline; useful as a contract example, not as a full architecture recommendation. |

## Minimal review checklist

- File and class name pass [`../scripts/check_extension_names.py`](../scripts/check_extension_names.py).
- `BaseModel.__init__(self, opt)` is called first in `__init__`.
- `loss_names`, `visual_names`, `model_names`, and `optimizers` match actual attributes.
- All dataset tensors consumed in `set_input` are moved to `self.device`.
- `model_names` matches the intended checkpoint file names for both train and test.
- `--netG`, `--netD`, `--norm`, `--input_nc`, and `--output_nc` defaults match the dataset output tensors and are stable between training and testing.
- If command execution is now needed, switch to [`translation-workflows`](../../translation-workflows/SKILL.md).
