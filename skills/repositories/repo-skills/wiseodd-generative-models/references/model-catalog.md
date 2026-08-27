# Model Catalog

## Purpose

Use this catalog to route user requests to the correct family sub-skill and to identify the relative source artifact labels captured from the repository snapshot. The generated skill bundles the catalog and compatibility helpers; it does not bundle the full long-running training scripts.

If the user is actively working in a checkout of the same repository, confirm the checkout matches `repo-provenance.md` before relying on a relative source artifact label.

## Shared conventions

- The repository is a legacy script collection, not a package or CLI.
- Scripts are MNIST training loops with constants embedded in source files.
- TensorFlow examples use TF1 placeholder/session style and the old `tensorflow.examples.tutorials.mnist.input_data` loader.
- PyTorch examples often still depend on that TensorFlow MNIST loader.
- Many scripts save sample images under a working-directory-local `out/` folder.

## GAN family

| Model family | Relative source artifact label(s) | Framework coverage | When to choose |
| --- | --- | --- | --- |
| Vanilla GAN | `GAN/vanilla_gan/gan_tensorflow.py`; `GAN/vanilla_gan/gan_pytorch.py` | TensorFlow + PyTorch | Default baseline when the user only asks for a classic GAN. |
| Conditional GAN | `GAN/conditional_gan/cgan_tensorflow.py`; `GAN/conditional_gan/cgan_pytorch.py` | TensorFlow + PyTorch | Label-conditioned digit generation. |
| InfoGAN | `GAN/infogan/infogan_tensorflow.py`; `GAN/infogan/infogan_pytorch.py` | TensorFlow + PyTorch | Latent-code control or disentanglement. |
| WGAN | `GAN/wasserstein_gan/wgan_tensorflow.py`; `GAN/wasserstein_gan/wgan_pytorch.py` | TensorFlow + PyTorch | Wasserstein critic baseline. |
| WGAN-GP / improved WGAN | `GAN/improved_wasserstein_gan/wgan_gp_tensorflow.py` | TensorFlow only | Gradient-penalty WGAN. |
| Mode-regularized GAN | `GAN/mode_regularized_gan/mode_reg_gan_tensorflow.py`; `GAN/mode_regularized_gan/mode_reg_gan_pytorch.py` | TensorFlow + PyTorch | Mode-coverage regularization. |
| COGAN | `GAN/coupled_gan/cogan_tensorflow.py`; `GAN/coupled_gan/cogan_pytorch.py` | TensorFlow + PyTorch | Coupled generation from shared latent structure. |
| ACGAN | `GAN/auxiliary_classifier_gan/ac_gan_tensorflow.py`; `GAN/auxiliary_classifier_gan/ac_gan_pytorch.py` | TensorFlow + PyTorch | Auxiliary class-prediction discriminator. |
| LSGAN | `GAN/least_squares_gan/lsgan_tensorflow.py`; `GAN/least_squares_gan/lsgan_pytorch.py` | TensorFlow + PyTorch | Least-squares discriminator objective. |
| BGAN | `GAN/boundary_seeking_gan/bgan_tensorflow.py`; `GAN/boundary_seeking_gan/bgan_pytorch.py` | TensorFlow + PyTorch | Boundary-seeking loss. |
| EBGAN | `GAN/ebgan/ebgan_tensorflow.py`; `GAN/ebgan/ebgan_pytorch.py` | TensorFlow + PyTorch | Energy-style discriminator. |
| f-GAN | `GAN/f_gan/f_gan_tensorflow.py`; `GAN/f_gan/f_gan_pytorch.py` | TensorFlow + PyTorch | f-divergence formulation. |
| GAP | `GAN/generative_adversarial_parallelization/gap_pytorch.py` | PyTorch only | Generative Adversarial Parallelization. |
| DiscoGAN | `GAN/disco_gan/discogan_tensorflow.py`; `GAN/disco_gan/discogan_pytorch.py` | TensorFlow + PyTorch | Unpaired cross-domain translation. |
| DualGAN | `GAN/dual_gan/dualgan_tensorflow.py`; `GAN/dual_gan/dualgan_pytorch.py` | TensorFlow + PyTorch | Two-domain dual-learning translation. |
| ALI / BiGAN | `GAN/ali_bigan/ali_bigan_tensorflow.py`; `GAN/ali_bigan/ali_bigan_pytorch.py` | TensorFlow + PyTorch | Joint encoder-generator adversarial inference. |
| BEGAN | `GAN/boundary_equilibrium_gan/began_tensorflow.py`; `GAN/boundary_equilibrium_gan/began_pytorch.py` | TensorFlow + PyTorch | Boundary equilibrium control. |
| MAGAN | `GAN/magan/magan_tensorflow.py`; `GAN/magan/magan_pytorch.py` | TensorFlow + PyTorch | Margin adaptation / mode-collapse mitigation. |
| Softmax GAN | `GAN/softmax_gan/softmax_gan_tensorflow.py`; `GAN/softmax_gan/softmax_gan_pytorch.py` | TensorFlow + PyTorch | Softmax discriminator objective. |
| GibbsNet | `GAN/gibbsnet/gibbsnet_pytorch.py` | PyTorch only | Iterative adversarial inference. |

## VAE family

| Model family | Relative source artifact label(s) | Framework coverage | When to choose |
| --- | --- | --- | --- |
| Vanilla VAE | `VAE/vanilla_vae/vae_tensorflow.py`; `VAE/vanilla_vae/vae_pytorch.py` | TensorFlow + PyTorch | Default unsupervised MNIST VAE. |
| Conditional VAE | `VAE/conditional_vae/cvae_tensorflow.py`; `VAE/conditional_vae/cvae_pytorch.py` | TensorFlow + PyTorch | Label-conditioned generation. |
| Denoising VAE | `VAE/denoising_vae/dvae_tensorflow.py`; `VAE/denoising_vae/dvae_pytorch.py` | TensorFlow + PyTorch | Reconstruct clean images from corrupted inputs. |
| Adversarial Autoencoder | `VAE/adversarial_autoencoder/aae_tensorflow.py`; `VAE/adversarial_autoencoder/aae_pytorch.py` | TensorFlow + PyTorch | Adversarial latent regularization. |
| Adversarial Variational Bayes | `VAE/adversarial_vb/avb_tensorflow.py`; `VAE/adversarial_vb/avb_pytorch.py` | TensorFlow + PyTorch | AVB/T-network variational objective. |

## RBM family

| Model family | Relative source artifact label(s) | Framework coverage | When to choose |
| --- | --- | --- | --- |
| Binary RBM with Contrastive Divergence | `RBM/rbm_binary_cd.py` | NumPy + TensorFlow MNIST loader | Default binary RBM baseline. |
| Binary RBM with Persistent Contrastive Divergence | `RBM/rbm_binary_pcd.py` | NumPy + TensorFlow MNIST loader | Persistent negative chains / PCD. |

## Helmholtz Machine family

| Model family | Relative source artifact label(s) | Framework coverage | When to choose |
| --- | --- | --- | --- |
| Binary Helmholtz Machine with Wake-Sleep | `HelmholtzMachine/vanilla_HM/helmholtz.py` | NumPy + TensorFlow MNIST loader | One-layer binary wake-sleep example. |

## Programmatic lookup

Use the bundled catalog helper for repeatable lookup:

```bash
python scripts/model_catalog.py --list-families
python scripts/model_catalog.py --family vae
python scripts/model_catalog.py --model adversarial-variational-bayes
```

The helper reads `references/model-catalog.json` from this skill directory, so it works without reopening the source checkout.
