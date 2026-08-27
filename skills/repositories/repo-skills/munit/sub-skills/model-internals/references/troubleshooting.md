# Model-internals troubleshooting

Use this table for architecture, checkpoint, and porting failures. Environment installation belongs to `../environment-and-setup/`; dataset path/layout failures belong to `../data-and-configuration/`; end-user train/test command issues belong to the workflow sub-skills.

| Symptom | Likely cause | Safe diagnosis | Fix or next action |
|---|---|---|---|
| `Please assign weight and bias before calling AdaIN!` | `AdaptiveInstanceNorm2d.forward` ran before `AdaINGen.assign_adain_params` assigned dynamic parameters. | Check whether code called `decoder(content)` directly or split `decode` into pieces. | Route style through the MLP and call `assign_adain_params` before every decoder forward, or call `AdaINGen.decode(content, style)`. |
| Generator checkpoint has size mismatch in style encoder or MLP | Config `gen.style_dim` differs from the checkpoint's training config. | Compare current config `gen.style_dim` with checkpoint metadata or the original experiment config. | Keep `style_dim` unchanged for checkpoint reuse, or train/convert a new checkpoint with a deliberate mapping. |
| First or last convolution state dict size mismatch | `input_dim_a`/`input_dim_b` or RGB/grayscale assumptions changed. | Inspect config input dimensions and inference image conversion behavior. | Keep dimensions compatible with checkpoints or convert first/last layer weights intentionally. |
| Discriminator state dict size mismatch | `dis.dim`, `dis.n_layer`, `dis.num_scales`, normalization, or spectral norm changed. | Run static config inspection and compare discriminator architecture surfaces. | Load only compatible checkpoints or retrain discriminators after architecture edits. |
| `Unsupported padding type`, `Unsupported normalization`, or `Unsupported activation` assertion | Config or extension used an option not implemented by `Conv2dBlock`/`LinearBlock`. | Check `gen.pad_type`, `dis.pad_type`, `gen.activ`, `dis.activ`, and `dis.norm`. | Use supported values or implement the new branch in the relevant block and update validation. |
| `Unsupported GAN type` assertion | `dis.gan_type` is neither `lsgan` nor `nsgan`. | Inspect config `dis.gan_type`. | Use `lsgan` for the bundled behavior or `nsgan` if intentionally using BCE-on-sigmoid semantics; add a new loss branch only with tests. |
| `nsgan` port produces different losses | Port changed sigmoid+BCE semantics. | Compare old `F.sigmoid` + binary cross entropy against any new logits-based loss. | Preserve `torch.sigmoid` + BCE for exact behavior, or use `BCEWithLogitsLoss` only after accepting numerical/semantic changes. |
| `Variable(..., volatile=True)` fails | Modern PyTorch removed `volatile`. | Search inference/batch code for `volatile=True`. | Wrap inference in `with torch.no_grad():` and remove `Variable`. |
| `module 'torch.nn.functional' has no attribute 'sigmoid'` | Modern PyTorch deprecates/removes `F.sigmoid`. | Search discriminator losses. | Replace with `torch.sigmoid` for minimal behavior preservation, or refactor to logits loss deliberately. |
| PyYAML raises Loader error or unsafe-load warning | Config loader uses `yaml.load(stream)` without a Loader. | Run a config-only static check. | Replace with `yaml.safe_load(stream)` for plain configs. |
| Import fails for `torch.utils.serialization.load_lua` | Modern PyTorch removed Torch7 Lua weight loading. | Check whether VGG utilities are imported or used. | Use a legacy PyTorch environment, require preconverted VGG weights, or replace the conversion path. |
| Trainer construction unexpectedly starts network download | `vgg_w > 0` and no converted VGG weight exists. | Inspect `vgg_w` and configured VGG model path before construction. | Keep `vgg_w: 0` for static tests, provide preconverted VGG weights, or make download an explicit setup step. |
| Old checkpoint load reports unexpected InstanceNorm running-stat keys | Checkpoint came from an older PyTorch InstanceNorm layout. | Try the distilled conversion logic conceptually: remove known InstanceNorm running mean/var keys for generator encoders/decoders. | Use/update the state dict conversion helper; do not ignore all key mismatches blindly. |
| `VAEGen.forward` errors with tuple-related attribute failure | The forward path treats the tuple returned by `encode` as a tensor. | Reproduce with a tiny CPU-only unit after porting, or inspect the flow statically. | Use `encode`/`decode` directly like the trainer, or patch `forward` to unpack `(hiddens, noise)`. |
| CPU-only model test fails at `.cuda()` | Legacy code unconditionally moves tensors/modules to CUDA. | Grep for `.cuda()` in trainer, networks, utilities, and entrypoints. | Replace with device-aware tensor creation before claiming CPU support; otherwise route real runs to a compatible CUDA runtime. |
| `get_scheduler` returns `NotImplementedError` object instead of scheduler | Unsupported `lr_policy` was configured. | Inspect `lr_policy`; supported values are `constant` and `step`. | Use a supported policy or implement and test a new scheduler branch. |
| Resume selects the wrong checkpoint | Resume helper sorts matching `.pt` filenames lexicographically and picks the last. | List generator/discriminator checkpoint filenames and check zero-padding/key substrings. | Preserve `gen_%08d.pt`/`dis_%08d.pt` naming or implement explicit checkpoint selection. |

## Minimal safe checklist before a port

- Static inspector passes on current source and target config.
- `gen.style_dim`, `input_dim_*`, `gen.dim`, `gen.n_downsample`, `gen.n_res`, `dis.dim`, `dis.n_layer`, and `dis.num_scales` are intentionally kept or checkpoint migration is planned.
- AdaIN decode path still assigns dynamic parameters before decoder forward.
- Deprecated PyTorch APIs have one-for-one replacements with loss semantics documented.
- VGG asset loading is explicit and never hidden inside a static check.
- Actual training/inference validation is routed through the workflow sub-skills and authorized separately.
