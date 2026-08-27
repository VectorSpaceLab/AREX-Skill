# Dynamic option registry and default coupling

The command-line parser is assembled in stages. Custom model and dataset hooks are part of that parser assembly, so defaults must be placed in the hook that owns them rather than assumed from a README command.

## Injection order

1. `BaseOptions.initialize` adds shared model, dataset, preprocessing, checkpoint, device, and logging flags; `TrainOptions` or `TestOptions` adds phase-specific flags.
2. The parser performs a preliminary `parse_known_args` to discover the requested `--model`.
3. The model registry imports `models.<model>_model` and returns that class's `modify_commandline_options` method.
4. The model hook adds model-specific arguments and rewrites model defaults. The parser is parsed again so a model-set `dataset_mode` becomes visible.
5. The parser now discovers the resulting `--dataset_mode` and calls the dataset registry for `data.<mode>_dataset`.
6. The dataset hook adds dataset-specific arguments and rewrites data defaults. The final parse produces the options used by the model and dataset constructors.

**Consequence:** the dataset hook runs after the model hook. If both hooks call `set_defaults` for the same option, the later dataset default normally wins. Make this precedence intentional and visible in the reference contract.

## Ownership rules for custom hooks

### Model hook owns architecture and objective defaults

Use the model hook for:

- a model-specific `dataset_mode` coupling, such as a paired model selecting `aligned`;
- generator/discriminator defaults (`netG`, `netD`, `n_layers_D`, `norm`);
- loss weights and training-only flags;
- model-only restrictions, such as rejecting training for a test-only model.

Use `is_train` to avoid exposing or requiring training-only options during test parsing.

### Dataset hook owns data shape and layout defaults

Use the dataset hook for:

- `input_nc` and `output_nc` when the dataset has a fixed channel contract;
- `direction` when only one direction is meaningful;
- dataset-specific path, sampling, or metadata options;
- safe limits for a template or bounded fixture.

The constructor should still assert or validate the invariants that make the defaults meaningful. For example, a colorization-style dataset expects one L input channel, two `ab` output channels, and `AtoB` direction.

## Verified built-in couplings

| Selected mode | Effective defaults to preserve unless intentionally overridden |
| --- | --- |
| train `cycle_gan` | `dataset_mode=unaligned`, `netG=resnet_9blocks`, `norm=instance`, `gan_mode=lsgan`, `pool_size=50`, `no_dropout=True`, cycle weights `lambda_A=10`, `lambda_B=10`, identity weight `lambda_identity=0.5` |
| train `pix2pix` | `dataset_mode=aligned`, `netG=unet_256`, `norm=batch`, `gan_mode=vanilla`, `pool_size=0`, `lambda_L1=100` |
| train `colorization` | pix2pix network/objective defaults plus `dataset_mode=colorization`, `input_nc=1`, `output_nc=2`, `direction=AtoB` |
| test `test` | `dataset_mode=single`, `netG=resnet_9blocks`, `norm=instance`, empty `model_suffix`, `load_size=crop_size` from test options |
| test `pix2pix` | `dataset_mode=aligned`, `netG=unet_256`, `norm=batch` |
| test `cycle_gan` | `dataset_mode=unaligned`, `netG=resnet_9blocks`, `norm=instance`, `no_dropout=True` |
| test `colorization` | `dataset_mode=colorization`, `input_nc=1`, `output_nc=2`, `direction=AtoB` |

These values come from the runtime registry/default probes and should be treated as compatibility defaults, not generic GAN recommendations.

## Network factory and channel implications

The bundled factory accepts:

- generators: `resnet_9blocks`, `resnet_6blocks`, `unet_128`, `unet_256`;
- discriminators: `basic`, `n_layers`, `pixel`;
- normalization: `batch`, `instance`, `none`, and the repository's synchronized batch option spelling (`syncbatch`).

Override the options only when the custom data or model requires it:

- override `--netG` when image size, receptive field, skip connections, or compute budget require a different bundled generator;
- override `--netD` and optionally `--n_layers_D` when patch scale or pixel-level discrimination is part of the model contract;
- override `--norm` only with a deliberate train/test and checkpoint plan; normalization modules affect state-dict compatibility;
- override `--input_nc` and `--output_nc` whenever the tensors emitted by the dataset are not the default RGB `3/3` pair. A grayscale pix2pix-like path commonly uses `input_nc=1`; a Lab colorization path uses `1/2`;
- if the custom model calls `define_D` for a conditional discriminator, its input channel count must include every tensor concatenated before the discriminator (pix2pix uses `input_nc + output_nc`).

For multi-GPU or finished command execution, route to [`translation-workflows`](../../translation-workflows/SKILL.md); this sub-skill only records the extension contract and default implications.

## CLI validation checklist

- Run the helper name check before parsing.
- Run the native parser/default probe for the selected model and dataset when available.
- Confirm the final parsed `dataset_mode`, channel counts, `netG`, `netD`, `norm`, and direction match both `__getitem__` and `set_input`.
- Keep training and test overrides aligned with the checkpoint architecture.
- If a default is changed by both model and dataset hooks, state which hook wins and why.
