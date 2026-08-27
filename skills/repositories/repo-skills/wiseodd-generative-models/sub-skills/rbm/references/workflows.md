# RBM Workflows

This sub-skill covers the binary RBM examples only. The repo contains two NumPy training loops:

- contrastive divergence (CD)
- persistent contrastive divergence (PCD)

Both are legacy MNIST scripts with no CLI. Hyperparameters such as minibatch size, hidden size, learning rate, and Gibbs steps are embedded in the source.

## Which one should I use?

| Need | Use |
| --- | --- |
| Canonical binary RBM baseline | CD |
| Classic per-example negative phase that restarts from data | CD |
| Persistent model-sample chains across minibatches | PCD |
| Slightly more model-anchored negative phase / persistent sampling | PCD |

## CD in one sentence

CD starts from a minibatch example, runs `K` Gibbs steps, and uses the final reconstructed sample as the negative phase.

## PCD in one sentence

PCD keeps a persistent Markov chain alive across updates, advances that chain with `K` Gibbs steps, and uses the persistent samples for the negative phase.

## Shared assumptions

- Visible and hidden units are Bernoulli.
- MNIST is binarized with a `> 0.5` threshold before training or plotting.
- The scripts use TensorFlow 1.x-style MNIST loading, but the actual learning loop is NumPy-based.
- Labels are loaded but not used for the RBM update.
- Output images are written under `out/`.
- The default visualizations expect square latent/output grids; `h_dim` should stay a perfect square unless the plotting helper is changed.

## Execution notes

- In a source checkout, `RBM/` is the expected working directory so the relative path `../MNIST_data` resolves to the expected dataset location.
- The scripts create `out/` on demand and save preview grids there.
- The output preview shows a 4x4 grid of sampled hidden states as `H.png` and a 4x4 grid of visible reconstructions as `V.png`, not a training metric dashboard.
- There is no command-line interface; choose the variant by running the corresponding script and, if needed, editing constants in source.

## Family-specific interpretation

- Choose CD when you want the simplest explanation or the textbook baseline.
- Choose PCD when the user explicitly wants persistent chains, a more model-driven negative phase, or the PCD variant named in the paper or README.
- If the user only says “binary RBM on MNIST,” default to CD unless they mention persistent sampling, PCD, or a desire to reuse the negative phase across minibatches.
