# Porting and extension guide

Use this guide before changing architecture code, moving MUNIT to a modern PyTorch stack, or loading old checkpoints into modified modules.

## Safe extension workflow

1. Decide whether the change is model-internal or user-facing. If it changes CLI behavior, config schema, dataset assumptions, checkpoint commands, or run outputs, also update the owning workflow sub-skill.
2. Run the static inspector on the current checkout and target config to capture baseline class signatures, config keys, and legacy markers.
3. Edit one surface at a time: generator, discriminator, trainer losses, device handling, checkpoint loading, or utility side effects.
4. Add a tiny CPU/static check first. Do not use full training/inference as the first validation step.
5. Only after static checks pass, move to legacy CUDA runtime checks through the training or inference sub-skill with explicit user approval.

## Style dimension and checkpoint compatibility

`gen.style_dim` is not a cosmetic hyperparameter. It is used by:

- `MUNIT_Trainer.style_dim`;
- fixed sampling tensors `s_a` and `s_b`;
- random style sampling in generator/discriminator updates;
- inference style sampling;
- `StyleEncoder(..., style_dim, ...)` output channels; and
- the AdaIN MLP input dimension.

Changing `style_dim` requires a new or converted generator checkpoint. A checkpoint trained with one style dimension will not load cleanly into a generator with another style dimension because style encoder and MLP tensor shapes change. If a user wants to reuse a checkpoint, keep `style_dim` identical and modify only compatible inference-side sampling behavior.

## AdaIN parameter assignment

AdaIN residual blocks store `weight` and `bias` as dynamically assigned tensors. The contract is:

```text
style -> MLP -> assign_adain_params(...) -> Decoder(content)
```

Do not bypass `AdaINGen.decode`. If a port splits generator components or calls the decoder directly, ensure each `AdaptiveInstanceNorm2d` layer receives batch-flattened weight and bias slices before forward. The assertion text for a missed assignment is: `Please assign weight and bias before calling AdaIN!`.

For a modern implementation, keep the per-sample AdaIN behavior. The original implementation reshapes `[N, C, H, W]` to `[1, N*C, H, W]` and runs batch normalization with repeated dummy running stats and flattened per-sample parameters.

## Device handling modernization

The legacy code calls `.cuda()` directly in trainers, discriminators, VAE noise creation, VGG preprocessing, train/test entrypoints, and batch inference. A modern port should:

- derive a `device` from input tensors or an explicit argument;
- replace `.cuda()` and `.cuda(device_id)` with `.to(device)` or tensor factory calls using `device=x.device`;
- create random style/noise tensors with the same dtype/device as the relevant input or hidden tensor;
- keep static inspection and config validation CPU-only; and
- avoid claiming CPU training/inference support until all unconditional CUDA paths are removed and tested.

## Deprecated PyTorch APIs

| Legacy pattern | Modern replacement guidance |
|---|---|
| `Variable(tensor)` | Tensors already track gradients in modern PyTorch; usually remove `Variable`. |
| `Variable(..., volatile=True)` | Use `with torch.no_grad():` around inference. |
| `F.sigmoid(x)` before BCE | Use `torch.sigmoid(x)` if preserving exact behavior, or refactor to `BCEWithLogitsLoss` with raw logits after checking loss semantics. |
| `tensor.data` for target shape/device | Prefer `torch.zeros_like(out)`/`torch.ones_like(out)` and explicit `requires_grad=False`. |
| `torch.utils.serialization.load_lua` | Removed from modern PyTorch. Convert VGG weights externally, vendor a safe converter, or require a preconverted `vgg16.weight`. |
| `torch.load(path)` without `map_location` | Use `map_location` when loading on CPU or different devices; document checkpoint device expectations. |

Keep loss semantics stable when changing `nsgan`: the original applies sigmoid then binary cross entropy. Switching to logits loss changes numerical behavior unless handled deliberately.

## PyYAML modernization

The config loader uses `yaml.load(stream)` without a Loader argument. In modern PyYAML this can warn or fail depending on version. Use `yaml.safe_load(stream)` for plain experiment configs unless the user intentionally needs custom YAML tags. Keep config values simple scalars/nested dictionaries so they remain portable.

## VGG perceptual-loss side effects

When `vgg_w > 0`, trainer construction calls a utility that can:

1. create a `models` directory under the configured output root;
2. run a network download command for `vgg16.t7` if no local file exists;
3. read Torch7 weights through `load_lua`; and
4. save converted `vgg16.weight`.

For static checks, keep `vgg_w: 0` or require a preexisting converted weight. For modern ports, remove implicit downloads from constructors and make VGG asset acquisition an explicit user-approved setup step.

## InstanceNorm state dict conversion

The checkpoint conversion helper removes selected old InstanceNorm running-stat keys from generator state dicts for MUNIT and UNIT. This exists because early PyTorch InstanceNorm behavior/state differed across versions.

When porting:

- inspect missing and unexpected keys rather than forcing `strict=False` without review;
- decide whether modern `InstanceNorm2d` should track running stats;
- update the conversion key list if module numbering changes; and
- test both MUNIT and UNIT checkpoint paths because their generator module names differ (`enc_content`/`dec` versus `enc`/`dec`).

## Extending supported options

The block constructors raise assertions for unsupported padding, normalization, activation, initialization, scheduler, and GAN values. To add a new option:

1. Add it to the relevant constructor/helper branch.
2. Add it to config validation and references.
3. Confirm checkpoint impact: adding normalization or spectral norm changes parameter names and shapes.
4. Add a static test that instantiates only tiny CPU blocks if the environment supports it, or a source-text/config validation when model construction is unsafe.

Do not simply add a new string to configs; unsupported values fail during module construction.

## VAE/UNIT caution

`UNIT_Trainer` uses `VAEGen.encode` and `VAEGen.decode` directly. The standalone `VAEGen.forward` path should be treated as suspect until tested because it assigns the `(hiddens, noise)` tuple returned by `encode` to one variable before calling tensor methods. If a port exposes `VAEGen.forward`, correct and test this path explicitly.
