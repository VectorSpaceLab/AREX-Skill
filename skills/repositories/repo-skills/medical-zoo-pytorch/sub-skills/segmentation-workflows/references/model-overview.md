# Model overview

This page summarizes the 3D segmentation model families exposed by the factory and the common `BaseModel` interface.

## Factory summary

| Factory id | Class | Input guidance | Output form | Notes |
| --- | --- | --- | --- | --- |
| `UNET3D` | `UNet3D` | Use a cubic 3D tensor with the desired number of modalities; 32³ is the safest smoke shape. | Single logits tensor. | Deep 3D U-Net with skip connections and deep-supervision style internals. |
| `VNET` | `VNet` | Keep `inChannels` compatible with the 16-channel input transition; 1, 2, or 4 are the practical choices. | Single logits tensor. | Full V-Net. The factory uses `elu=False`. |
| `VNET2` | `VNetLight` | Same channel rule as `VNET`. | Single logits tensor. | Lighter V-Net variant. The factory uses `elu=False`. |
| `DENSENET1` | `SinglePathDenseNet` | Any positive channel count works; 12³ or 16³ is a good smoke size. | Single logits tensor. | Single-stream dense model. |
| `DENSENET2` | `DualPathDenseNet` | Use 2 or 3 channels only. | Single logits tensor. | Dual/tri-stream late fusion; the source channel math is fragile and is skipped by the default all-case smoke. |
| `DENSENET3` | `DualSingleDenseNet` | Use 2 or 3 channels only. | Single logits tensor. | Early-fusion dense variant. |
| `HYPERDENSENET` | `HyperDenseNet_2Mod` or `HyperDenseNet` | 2 channels selects the 2-modality class, 3 channels selects the 3-modality class. | Single logits tensor with reduced spatial size. | The architecture crops aggressively; the bundled smoke checks use `22³ -> 4³` for the 2-channel branch and `20³ -> 2³` for the 3-channel branch. |
| `SKIPDENSENET3D` | `SkipDenseNet3D` | Any positive channel count; 32³ is a good smoke size. | Single logits tensor. | Skip-connected dense segmentation network. |
| `DENSEVOXELNET` | `DenseVoxelNet` | Any positive channel count; 8³ is a good smoke size. | Tuple `(main_logits, aux_logits)`. | Return both outputs if you compute loss or shape checks. |
| `RESNET3DVAE` | `ResNet3dVAE` | Any positive channel count; keep each spatial dimension divisible by 8. | Tuple `(seg_logits, vae_out, mu, logvar)`. | Segmentation plus VAE regularization path. |
| `RESNETMED3D` | `ResNetMed3D` via `generate_resnet3d` | Any positive channel count; keep each spatial dimension divisible by 8. | Single logits tensor. | The factory hardcodes depth 18. |
| `HIGHRESNET` | `HighResNet3D` | Any positive channel count; 32³ is a good smoke size. | Single logits tensor. | Dilated residual 3D network. |

## `BaseModel` interface

All segmentation models inherit the common base behavior:

| Method | Purpose | Important behavior |
| --- | --- | --- |
| `forward(x)` | Standard forward pass. | Some models return a tensor; some return tuples. |
| `test()` | Source-side smoke helper. | Some classes import extra summary helpers at module import time. The bundled smoke scripts avoid these extras. |
| `device` | Current parameter device. | Uses the first parameter. |
| `save_checkpoint(directory, epoch, loss, optimizer=None, name=None)` | Save a training checkpoint. | Writes the main checkpoint and a `_BEST` copy when the loss improves. |
| `restore_checkpoint(path, optimizer=None)` | Restore a checkpoint. | Returns the saved epoch. |
| `count_params()` | Count parameters. | Returns total and trainable counts. |
| `inference(input_tensor)` | Run eval-mode inference. | Returns a CPU tensor and strips tuple outputs down to the first tensor. |

## Factory notes

- The factory expects `args.model`, `args.opt`, `args.lr`, `args.inChannels`, `args.classes`, and `args.dim`.
- The optimizer branch uses a tiny default weight decay.
- The factory also exposes 2D and COVID branches, but this sub-skill owns only the 3D segmentation workflow.
- If you need a depth other than 18 for `RESNETMED3D`, call the model generator directly instead of the factory.

## Recommended smoke shapes

- `UNET3D`: `1 x 2 x 32 x 32 x 32`
- `VNET` / `VNET2`: `1 x 2 x 32 x 32 x 32`
- `DENSENET1` / `DENSENET2` / `DENSENET3`: `1 x 2 x 12 x 12 x 12`
- `HYPERDENSENET`: `1 x 2 x 22 x 22 x 22 -> 1 x 4 x 4 x 4 x 4` for the 2-modality path, or `1 x 3 x 20 x 20 x 20 -> 1 x 4 x 2 x 2 x 2` for the 3-modality path
- `SKIPDENSENET3D`: `1 x 2 x 32 x 32 x 32`
- `DENSEVOXELNET`: `1 x 2 x 8 x 8 x 8`
- `RESNET3DVAE`: `1 x 2 x 16 x 16 x 16`
- `RESNETMED3D`: `1 x 2 x 16 x 16 x 16`
- `HIGHRESNET`: `1 x 2 x 32 x 32 x 32`
