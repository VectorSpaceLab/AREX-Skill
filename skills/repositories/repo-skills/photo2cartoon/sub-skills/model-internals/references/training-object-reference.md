# Training Object Reference

Evidence used: `models/UGATIT_sadalin_hourglass.py`, `models/networks.py`, `dataset.py`, and the README training section.

## Trainer identity

`UgatitSadalinHourglass` is the training/test wrapper around the architecture stack.

It owns:

- two generators: `genA2B` and `genB2A`
- two global discriminators: `disGA` and `disGB`
- two local discriminators: `disLA` and `disLB`
- the face-ID model wrapper: `FaceFeatures('models/model_mobilefacenet.pth', device)`
- the optimizer pair and all loss objects
- checkpoint save/load and the training/test loops

## Build-model contract

`build_model()` wires the following pieces together:

| Component | Contract |
| --- | --- |
| `train_transform` | `RandomHorizontalFlip` -> `Resize((img_size + 30, img_size + 30))` -> `RandomCrop(img_size)` -> `ToTensor()` -> `Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))` |
| `test_transform` | `Resize((img_size, img_size))` -> `ToTensor()` -> `Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))` |
| `ImageFolder` roots | `dataset/<name>/trainA`, `trainB`, `testA`, `testB` |
| generator class | `ResnetGenerator(ngf=ch, img_size=img_size, light=light)` |
| discriminator classes | `Discriminator(input_nc=3, ndf=ch, n_layers=7)` for global and `n_layers=5` for local |
| face-ID model | `FaceFeatures('models/model_mobilefacenet.pth', device)` |
| losses | `L1Loss`, `MSELoss`, `BCEWithLogitsLoss` |
| optimizers | Adam with `betas=(0.5, 0.999)` and `weight_decay=0.0001` |

The transform normalization means the training tensors are in the same `[-1, 1]` range used by the generator output and the helper utilities.

## Loss graph

The trainer combines these losses:

- adversarial MSE loss for each global/local discriminator pair
- CAM MSE loss for discriminator CAM logits
- cycle reconstruction L1 loss
- identity L1 loss
- CAM BCE loss on generator CAM logits
- face-ID cosine distance loss from `FaceFeatures.cosine_distance`

Key weights are exposed as CLI args:

- `adv_weight`
- `cycle_weight`
- `identity_weight`
- `cam_weight`
- `faceid_weight`

## Checkpoint key map

Training checkpoints are dictionaries with these module keys:

| Key | Module | Typical consumer |
| --- | --- | --- |
| `genA2B` | photo -> cartoon generator | inference and training |
| `genB2A` | cartoon -> photo generator | training and test previews |
| `disGA` | global discriminator for domain A | training |
| `disGB` | global discriminator for domain B | training |
| `disLA` | local discriminator for domain A | training |
| `disLB` | local discriminator for domain B | training |

The trainer saves and loads these exact names. If a checkpoint is missing any of them, loading into the training object should be treated as incomplete.

## Save and resume behavior

- `save(dir, step)` writes `dataset_params_%07d.pt`.
- Every 1000 steps the trainer also writes a latest snapshot named `dataset_params_latest.pt` in the result directory.
- `load(dir, step)` expects the same dictionary structure and loads each module state into the corresponding model.
- `pretrained_weights` loads the same dictionary shape directly with `torch.load(..., map_location=self.device)`.
- When multi-GPU is active, the code saves and loads `.module.state_dict()`.

## Rho and weight clipping

After each optimizer step the trainer applies two clippers:

- `RhoClipper(0, rho_clipper)` constrains `rho` in `adaLIN` and `LIN`.
- `WClipper(0, w_clipper)` constrains `w_gamma` and `w_beta` in `SoftAdaLIN`.

These clippers are part of the model contract. If a ported trainer omits them, the normalization layers can drift away from the source behavior.

## Practical checks

- Use the architecture reference to confirm tuple shapes before loading a checkpoint.
- Use the smoke script to validate a checkpoint key map before attempting a full training resume.
- Route dataset layout and long-running training questions to `../data-and-training/`.

