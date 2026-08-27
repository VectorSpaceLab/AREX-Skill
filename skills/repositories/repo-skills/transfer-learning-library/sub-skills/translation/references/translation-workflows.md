# Translation Workflows

Use this reference when a user wants to add image/domain translation to a TLLib workflow without reopening the original examples. The original benchmark trainers are large, dataset-dependent, and optional; this file distills the reusable choices and validation sequence.

## Choose the translation mechanism

| User intent | Prefer | Why | Route after translation |
| --- | --- | --- | --- |
| Lightweight target-domain style perturbation for segmentation or dense prediction | `FourierTransform` / FDA | No learned generator; mixes low-frequency amplitude from target images. | Use the adapted images in a segmentation/domain-adaptation pipeline, then route to `domain-adaptation`. |
| Apply an already-trained image-to-image generator to dataset items | CycleGAN `Translation` transform | Wraps a PyTorch generator as a PIL transform and can be inserted in dataset preprocessing. | Route model/dataset concerns to `vision-data-models` and adaptation loss/training to `domain-adaptation`. |
| Train a full unpaired image translation model | CycleGAN components | TLLib has generators, discriminators, GAN losses, and `ImagePool`, but full training is dataset/GPU-heavy. | Treat as an external long-running training workflow; validate components first with the bundled smoke. |
| Preserve semantic labels during translated-image training | `SemanticConsistency` | Adds cross-entropy consistency between translated predictions and source labels. | Route segmentation/classification training details to `domain-adaptation`. |
| Preserve person re-identification identity similarity | SPGAN `SiameseNetwork` + `ContrastiveLoss` | Adds identity constraints around translation. | Route re-id datasets/models/metrics to `vision-data-models`. |

## Safe workflow: apply a trained CycleGAN generator

1. Confirm the installed package imports and run `scripts/tllib_translation_smoke.py` from this sub-skill.
2. Reconstruct the generator with exactly the same factory, base filters, norm type, channel count, and dropout setting used when the checkpoint was trained.
3. Load the checkpoint on CPU first with `torch.load(path, map_location='cpu')` and strip a leading `module.` prefix if the checkpoint came from `DataParallel`.
4. Set `generator.eval()` and freeze parameters with `set_requires_grad(generator, False)`.
5. Wrap it with `cyclegan.Translation(generator, device=target_device, mean=(0.5,0.5,0.5), std=(0.5,0.5,0.5))`.
6. Convert source images to RGB before passing them through the transform.
7. Validate one tiny or representative image before inserting the transform into a dataset pipeline.

Minimal skeleton:

```python
import torch
from PIL import Image
import tllib.translation.cyclegan as cyclegan
from tllib.translation.cyclegan.util import set_requires_grad

net_g = cyclegan.resnet_9(ngf=64, norm='instance')
state = torch.load('generator.pth', map_location='cpu')
state = state.get('netG_S2T', state)
state = {k.replace('module.', '', 1): v for k, v in state.items()}
net_g.load_state_dict(state, strict=True)
net_g.eval()
set_requires_grad(net_g, False)
translate = cyclegan.Translation(net_g, device=torch.device('cpu'))
out = translate(Image.open('sample.png').convert('RGB'))
```

Replace the file names with user-provided paths. Do not assume a source-checkout example directory exists.

## Safe workflow: FDA preprocessing

1. Collect a small list of target-domain image paths that are already local and licensed for use.
2. Resize source and target images to the same spatial size before FDA if later transforms expect fixed dimensions.
3. Use a writable amplitude cache directory; set `rebuild=True` when target images changed.
4. Instantiate `FourierTransform(image_list, amplitude_dir, beta=1, rebuild=True)`.
5. Apply it to source-domain PIL images and inspect output size/mode.
6. Insert the transform before random crop or heavy augmentation in segmentation/adaptation workflows.

FDA is not a downloader and should not be used to fetch target images. If target paths are missing, fix the dataset/list first through `vision-data-models`.

## Safe workflow: semantic consistency

Use `SemanticConsistency` when translated images should retain source semantic labels:

```python
from tllib.translation.cycada import SemanticConsistency
criterion = SemanticConsistency(ignore_index=(255,))
loss = criterion(translated_logits, source_labels.clone())
```

Clone labels because TLLib modifies ignored targets in place. Match logits and label shapes exactly (`N x C x H x W` with `N x H x W`, or `N x C` with `N`).

## Safe workflow: SPGAN-style identity consistency

For re-identification translation, use the SPGAN components as auxiliary pieces, not as a standalone benchmark runner:

1. Keep images at the expected re-id shape (`3 x 256 x 128`) unless you have verified the Siamese fully connected size.
2. Build pairs and labels explicitly: TLLib's contrastive loss convention uses `0` for positive/same-identity and `1` for negative/different pairs.
3. Compute the contrastive term on Siamese features, then combine with GAN/cycle losses in the user's training loop.
4. Route dataset splits, camera IDs, and re-id metrics to `vision-data-models`.

## Validation checklist

- Component smoke passes without downloads.
- Generator/discriminator input channels match image channels.
- Checkpoint keys match the reconstructed factory and norm choices.
- Images are RGB or intentionally converted to the channel count the model expects.
- FDA target amplitudes are rebuilt after changing target image lists.
- Semantic labels are cloned before `SemanticConsistency` if reused later.
- Full training requests explicitly acknowledge GPU, dataset, checkpoint, and runtime requirements.
