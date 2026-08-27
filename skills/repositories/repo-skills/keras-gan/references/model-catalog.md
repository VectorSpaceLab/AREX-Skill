# Keras-GAN Model Catalog

Use this catalog to route natural user requests to the correct sub-skill and script family.

## Standalone MNIST-style generators

Read [../sub-skills/mnist-generators/SKILL.md](../sub-skills/mnist-generators/SKILL.md) for these models.

| Model | Script/class | Best-fit tasks | Important notes |
| --- | --- | --- | --- |
| Vanilla GAN | `gan/gan.py` / `GAN` | Smallest baseline MLP GAN on MNIST. | Binary cross-entropy, `Adam(0.0002, 0.5)`, `latent_dim=100`. |
| DCGAN | `dcgan/dcgan.py` / `DCGAN` | Convolutional MNIST generator/discriminator baseline. | Dense-to-7x7 generator and conv discriminator. |
| Conditional GAN | `cgan/cgan.py` / `CGAN` | Label-conditioned digit generation. | Label embeddings multiply noise and image features. |
| Auxiliary Classifier GAN | `acgan/acgan.py` / `ACGAN` | Label-conditioned generation plus auxiliary class prediction. | Training calls `save_model()` at sample intervals; create `saved_model/`. |
| Semi-Supervised GAN | `sgan/sgan.py` / `SGAN` | Discriminator predicts real digit labels plus a fake class. | Uses 11-class label output. |
| InfoGAN | `infogan/infogan.py` / `INFOGAN` | Interpretable categorical latent-code experiments. | `latent_dim=72` combines 62 Gaussian values and 10 one-hot code values. |
| LSGAN | `lsgan/lsgan.py` / `LSGAN` | Least-squares GAN objective comparison. | Uses MSE loss rather than binary cross-entropy. |
| BGAN | `bgan/bgan.py` / `BGAN` | Boundary-seeking GAN objective comparison. | Custom `boundary_loss` can need numerical clipping in ports. |
| BiGAN | `bigan/bigan.py` / `BIGAN` | Joint image and latent representation learning. | Includes encoder, generator, discriminator, and `bigan_generator`. |
| Adversarial Autoencoder | `aae/aae.py` / `AdversarialAutoencoder` | Autoencoder with latent discriminator. | `save_model()` references `self.generator` even though the decoder is named `self.decoder`. |
| CoGAN | `cogan/cogan.py` / `COGAN` | Coupled generators/discriminators on synthetic two-domain MNIST. | Rotates part of MNIST with SciPy to form a second domain. |
| DualGAN | `dualgan/dualgan.py` / `DUALGAN` | Dual learning / cycle-style translation on flattened synthetic MNIST domains. | Uses Wasserstein losses and MAE cycle outputs. |
| WGAN | `wgan/wgan.py` / `WGAN` | Wasserstein critic with weight clipping. | Uses valid label `-1`, fake label `+1`, RMSprop, `n_critic=5`. |
| WGAN-GP | `wgan_gp/wgan_gp.py` / `WGANGP` | Wasserstein gradient penalty comparison. | Uses private legacy `keras.layers.merge._Merge` and fixed interpolation batch size 32. |

## Image-to-image translation

Read [../sub-skills/image-translation/SKILL.md](../sub-skills/image-translation/SKILL.md) for these workflows.

| Model | Script/class | Data contract | Best-fit tasks |
| --- | --- | --- | --- |
| CycleGAN | `cyclegan/cyclegan.py` / `CycleGAN` | Unpaired `trainA/trainB/testA/testB` domains, default `apple2orange`, 128x128 RGB. | Unpaired domain translation with cycle and identity losses. |
| DiscoGAN | `discogan/discogan.py` / `DiscoGAN` | In this repo, paired side-by-side `train/val` images, default `edges2shoes`, 128x128 RGB. | Paired educational cross-domain relation learning; adapt deliberately for unpaired folders. |
| Pix2Pix | `pix2pix/pix2pix.py` / `Pix2Pix` | Paired side-by-side `train/test/val` images, default `facades`, 256x256 RGB. | Conditional image translation where B is condition and A is target. |

## Domain adaptation and restoration

Read [../sub-skills/domain-and-restoration/SKILL.md](../sub-skills/domain-and-restoration/SKILL.md) for these workflows.

| Model | Script/class | Data contract | Best-fit tasks |
| --- | --- | --- | --- |
| CC-GAN | `ccgan/ccgan.py` / `CCGAN` | Keras MNIST resized to 32x32 grayscale with random 10x10 masks. | Context-conditional MNIST inpainting with semi-supervised labels. |
| Context Encoder | `context_encoder/context_encoder.py` / `ContextEncoder` | Keras CIFAR-10 cats/dogs, 32x32 RGB, random 8x8 missing patches. | Missing-patch prediction and inpainting experiments. |
| PixelDA | `pixelda/pixelda.py` / `PixelDA` | MNIST and MNIST-M cached arrays under `datasets/` or network-prepared source artifacts. | Pixel-level domain adaptation plus classifier training. |
| SRGAN | `srgan/srgan.py` / `SRGAN` | CelebA-like images directly under `datasets/img_align_celeba/`; VGG19 ImageNet weights for perceptual loss. | 4x image super-resolution from 64x64 LR to 256x256 HR. |

## Selection shortcuts

- If the request names a paper/model acronym exactly, route by the table above.
- If the request is about validating folders or image pairs, use `image-translation` or `domain-and-restoration` rather than `mnist-generators`.
- If the request is about installing or modernizing dependencies, start with [compatibility-and-install.md](compatibility-and-install.md) and [troubleshooting.md](troubleshooting.md), then route to the affected sub-skill.
- If the request is simply "train Keras-GAN", ask which model and dataset. The repository has no single unified training command.
