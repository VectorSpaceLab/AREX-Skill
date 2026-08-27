# Model Architecture

This reference gives just enough architecture context to explain AnyDoor’s
configuration and why some paths matter.

## Main components

| Component | Source object | Role |
| --- | --- | --- |
| Control wrapper | `cldm.cldm.ControlLDM` | Wraps the latent diffusion model with control conditioning. |
| Control branch | `cldm.cldm.ControlNet` | Builds the control features from the collage / hint tensor. |
| UNet wrapper | `cldm.cldm.ControlledUnetModel` | Injects the control features into the diffusion backbone. |
| Autoencoder | `ldm.models.autoencoder.AutoencoderKL` | Encodes and decodes the image latent space. |
| Conditioning encoder | `ldm.modules.encoders.modules.FrozenDinoV2Encoder` | Loads the DINOv2 image encoder and its checkpoint. |
| Diffusion helpers | `cldm.ddim_hacked.DDIMSampler`, `ldm.models.diffusion.ddim.DDIMSampler` | Run the sampling loop used by inference. |

## What the config implies

- The conditioning image size is 224x224.
- The generation canvas is 512x512 in the source scripts.
- The control tensor includes the collage image and an extra mask channel.
- The DINOv2 checkpoint path is part of the model config, not just a training
  convenience.

## Why the architecture reference matters

When a user says a config or checkpoint issue looks “deep,” the problem is often
still a path issue. The architecture reference helps explain which field owns
which weight file so the fix stays precise.

## Do not over-explain here

This is not an API manual. Keep the large signature lists and workflow details in
other references or in the source code comments that were already distilled into
this skill tree.
