# Checkpoints and inputs

## Weight source and device policy

The bundled scripts are deliberately offline:

- They always construct with `pretrained=False`; there is no `--pretrained`
  flag and no implicit model-store or network request.
- `--checkpoint FILE` is optional and means an existing local file only. The
  path must be a regular file; no download or cache lookup is attempted.
- The provider, model name, classifier count, input-channel count, and
  checkpoint must agree. The scripts use three input channels and default to
  1000 classes; set `--classes` to the checkpoint's classifier count.
- The default device/context is CPU. PyTorch loads with
  `torch.load(FILE, map_location=torch.device("cpu"))`; Gluon loads with
  `net.load_parameters(FILE, ctx=mx.cpu(), ignore_extra=False)`.

A Gluon checkpoint should be a parameter file accepted by MXNet Gluon's
`load_parameters`. A PyTorch checkpoint should be a serialized state dict or a
mapping containing a `state_dict` mapping. PyTorch DataParallel checkpoints
whose keys start with `module.` can be used with `--remove-module`. Loading is
strict otherwise: missing keys, unexpected keys, and shape mismatches fail
rather than silently producing a partial model.

Do not use a checkpoint saved for another architecture or class count. Do not
solve a classifier mismatch by changing normalization or dropping keys.
Reconstruct the exact model first. The CPU remapping caveat prevents a CUDA
serialization device error; it does not make an incompatible checkpoint
compatible.

## ImageNet RGB preprocessing

For ImageNet-style classification, the scripts implement the repository's
validation convention:

1. If `--image` is supplied, read it with Pillow and convert it to RGB. The
   conversion avoids BGR/RGB mistakes from libraries whose default is BGR.
2. Preserve aspect ratio and resize the shorter side to
   `ceil(input_size / resize_inv_factor)`. Defaults are `input_size=224`,
   `resize_inv_factor=0.875`, and therefore a 256-pixel shorter side.
3. Take a centered square crop of `input_size x input_size` pixels.
4. Convert to float32, divide by `255.0`, then normalize channel-wise:

   ```text
   mean = (0.485, 0.456, 0.406)
   std  = (0.229, 0.224, 0.225)
   normalized = (rgb / 255 - mean) / std
   ```

5. Transpose HWC to CHW and add the batch dimension. The provider receives
   NCHW `(1, 3, 224, 224)` by default.

When `--image` is omitted, the scripts create an all-zero RGB image and still
apply the same normalization. This is a deterministic shape/device smoke, not
an ImageNet accuracy test. A non-default `--input-size` is supported by the
input pipeline, but the selected model must support that spatial size and the
checkpoint must correspond to the resulting architecture.

## Output contract

Both scripts print:

```text
input_shape=(1, 3, H, W)
output_shape=(1, C)
device=...
parameter_count=...
topk=[(zero_based_index, probability), ...]
```

`C` must equal `--expected-classes` when supplied, otherwise `--classes`;
`--top-k` is capped at `C`. A top-k result has no label or accuracy meaning
because labels are not bundled and the default input is synthetic.

## Runnable commands

From the sub-skill directory:

```bash
python scripts/infer_gluon.py --help
python scripts/infer_pytorch.py --help
python scripts/infer_gluon.py --model resnet18
python scripts/infer_pytorch.py --model resnet18
```

From the repository root, use the path to this directory:

```bash
python skills/disco/imgclsmob/sub-skills/model-inference/scripts/infer_gluon.py --model resnet18
python skills/disco/imgclsmob/sub-skills/model-inference/scripts/infer_pytorch.py --model resnet18
```

The two smoke invocations require the corresponding provider runtime to be
installed, but require no dataset, image, checkpoint, or network access.
