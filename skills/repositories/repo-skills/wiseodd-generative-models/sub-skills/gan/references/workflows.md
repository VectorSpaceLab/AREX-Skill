# GAN workflows

## How to choose

1. If the user names a behavior instead of a script, map it to the closest family.
2. If both frameworks exist, choose TensorFlow when you want the original session-based code and can supply a TF1-style MNIST loader.
3. Choose PyTorch when you already have a legacy torch environment or want the PyTorch code path, but remember that most PyTorch GAN files still import the TensorFlow MNIST loader.
4. Run the script from the family directory so `../../MNIST_data` and `out/` resolve correctly.

## Family map

| Family | Script(s) | Framework choice | Selection hint |
| --- | --- | --- | --- |
| Vanilla GAN | `GAN/vanilla_gan/gan_tensorflow.py`, `GAN/vanilla_gan/gan_pytorch.py` | dual | Default baseline if the user only says “GAN”. |
| Conditional GAN (cGAN) | `GAN/conditional_gan/cgan_tensorflow.py`, `GAN/conditional_gan/cgan_pytorch.py` | dual | Class-conditional digit generation. |
| InfoGAN | `GAN/infogan/infogan_tensorflow.py`, `GAN/infogan/infogan_pytorch.py` | dual | Latent-code control and disentanglement. |
| Wasserstein GAN (WGAN) | `GAN/wasserstein_gan/wgan_tensorflow.py`, `GAN/wasserstein_gan/wgan_pytorch.py` | dual | Critic-based Wasserstein baseline. |
| WGAN-GP / improved WGAN | `GAN/improved_wasserstein_gan/wgan_gp_tensorflow.py` | TensorFlow only | Gradient-penalty variant; there is no PyTorch file. |
| LSGAN | `GAN/least_squares_gan/lsgan_tensorflow.py`, `GAN/least_squares_gan/lsgan_pytorch.py` | dual | Least-squares discriminator objective. |
| ACGAN | `GAN/auxiliary_classifier_gan/ac_gan_tensorflow.py`, `GAN/auxiliary_classifier_gan/ac_gan_pytorch.py` | dual | Auxiliary classifier for class conditioning. |
| BEGAN | `GAN/boundary_equilibrium_gan/began_tensorflow.py`, `GAN/boundary_equilibrium_gan/began_pytorch.py` | dual | Autoencoder discriminator with equilibrium control. |
| BGAN | `GAN/boundary_seeking_gan/bgan_tensorflow.py`, `GAN/boundary_seeking_gan/bgan_pytorch.py` | dual | Boundary-seeking loss. |
| EBGAN | `GAN/ebgan/ebgan_tensorflow.py`, `GAN/ebgan/ebgan_pytorch.py` | dual | Energy-based discriminator. |
| f-GAN | `GAN/f_gan/f_gan_tensorflow.py`, `GAN/f_gan/f_gan_pytorch.py` | dual | f-divergence formulation. |
| GAP | `GAN/generative_adversarial_parallelization/gap_pytorch.py` | PyTorch only | Parallelized GAN training; no TensorFlow counterpart exists. |
| DiscoGAN | `GAN/disco_gan/discogan_tensorflow.py`, `GAN/disco_gan/discogan_pytorch.py` | dual | Unpaired image-to-image translation. |
| DualGAN | `GAN/dual_gan/dualgan_tensorflow.py`, `GAN/dual_gan/dualgan_pytorch.py` | dual | Two-domain translation with reconstruction. |
| COGAN | `GAN/coupled_gan/cogan_tensorflow.py`, `GAN/coupled_gan/cogan_pytorch.py` | dual | Coupled generation from shared latent codes. |
| ALI/BiGAN | `GAN/ali_bigan/ali_bigan_tensorflow.py`, `GAN/ali_bigan/ali_bigan_pytorch.py` | dual | Bidirectional inference / joint encoder-generator. |
| MAGAN | `GAN/magan/magan_tensorflow.py`, `GAN/magan/magan_pytorch.py` | dual | Margin adaptation against mode collapse. |
| Softmax GAN | `GAN/softmax_gan/softmax_gan_tensorflow.py`, `GAN/softmax_gan/softmax_gan_pytorch.py` | dual | Softmax discriminator objective. |
| GibbsNet | `GAN/gibbsnet/gibbsnet_pytorch.py` | PyTorch only | Iterative adversarial inference; no TensorFlow counterpart exists. |
| Mode-regularized GAN | `GAN/mode_regularized_gan/mode_reg_gan_tensorflow.py`, `GAN/mode_regularized_gan/mode_reg_gan_pytorch.py` | dual | Mode coverage regularization; the PyTorch file still uses `np.int`. |

## Practical notes

- All scripts use MNIST and save sample grids to `out/` under the working family directory.
- The PyTorch variants are not self-contained modern code: they still rely on the TensorFlow MNIST loader.
- `gan_pytorch.py` and `mode_reg_gan_pytorch.py` already print losses with `.data.numpy()`, but most of the other PyTorch GAN files still use `loss.data[0]`.
- For shared catalog lookup, use `../../../references/model-catalog.md`.
