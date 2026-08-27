# Helmholtz Machine Workflows

## Shared references

- Root catalog: `../../../references/model-catalog.md`
- Root compatibility: `../../../references/compatibility.md`
- Root troubleshooting: `../../../references/troubleshooting.md`

## What the example is

This repo's Helmholtz Machine entry point is a single legacy script that trains a one-layer binary Helmholtz Machine with wake-sleep. There is no CLI, no config file, and no package API.

Core state:

- `R`: recognition / inference weights
- `W`: generative weights
- `B`: hidden bias for the generative prior
- `alpha = 0.1`
- `mb_size = 16`
- `h_dim = 36`

The script loads MNIST with one-hot labels, but the labels are unused. The actual learning loop is unsupervised.

## Wake-sleep loop

1. Load a minibatch from MNIST.
2. Binarize the images with `> 0.5` before training.
3. Infer hidden units with `infer(X) = sigmoid(X @ R)`.
4. Generate visibles with `generate(H) = sigmoid(H @ W)`.
5. Run the wake phase:
   - sample `H ~ Bernoulli(infer(X_mb))`
   - compute `V = generate(H)`
   - compare the sample against the current hidden prior `H' = sigmoid(B)`
   - update `B` and `W` from the wake mismatch
6. Run the sleep phase:
   - sample `H_mb ~ Bernoulli(sigmoid(B))`
   - sample `V ~ Bernoulli(generate(H_mb))`
   - re-infer `H = infer(V)`
   - update `R` from the sleep mismatch
7. Repeat for 1000 iterations with a decayed step size `alpha / t`.

In plain language:

- Wake phase improves the generative model from real MNIST minibatches.
- Sleep phase improves the recognition model from synthetic samples.
- The script uses binary visibles and binary hidden samples throughout.

## Binarized MNIST assumptions

- The input data is thresholded at 0.5.
- The one-hot labels are loaded only because the old TensorFlow MNIST helper returns them together with images.
- The example assumes the MNIST dataset already exists at the expected relative path.

## Output image generation

- The script creates `out/` if it is missing.
- It saves hidden-unit samples to `out/H.png`.
- It saves reconstructed visibles to `out/V.png`.
- `H.png` uses `sqrt(h_dim)` for its grid shape.
- `V.png` uses `sqrt(X_dim)` for its grid shape, which is 28 for MNIST.

Because `out/` is relative, the images land under the current working directory, not automatically beside the example unless you run it from the example's own working directory.

## NumPy-only execution notes

- After MNIST loading, the training logic is pure NumPy plus `np.random.binomial`.
- Matplotlib is only used to save the PNG grids.
- TensorFlow is only needed for the legacy MNIST loader, not for the wake-sleep math.
- That makes the algorithm easy to explain without a GPU framework, but the legacy loader and alias usage still matter on modern systems.
