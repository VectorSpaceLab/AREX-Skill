# dcgan_theano model API reference

This reference summarizes the iGAN inference model facts needed to construct
safe commands and reason about sample generation. It is intentionally static: do
not import Theano merely to read these facts.

## Model class construction

The relevant API is a class named `Model` under the `dcgan_theano` model type.
The sample script dynamically locates it from the model type and constructs it
with:

```python
model = Model(model_name=args.model_name, model_file=args.model_file)
```

Constructor contract:

| Parameter | Required | Meaning |
| --- | --- | --- |
| `model_name` | yes | Must match a config function such as `outdoor_64` or `shoes_64`. |
| `model_file` | yes | Path to a pickled model artifact containing generator/discriminator weights and batchnorm state. |
| `use_predict` | optional | Present in the signature but not used by sample generation; projection workflows own predictor-specific behavior. |

Important constructor side effects during native execution:

- Reads model metadata from the config function named by `model_name`.
- Initializes generator, discriminator, and predictor parameter containers.
- Loads the artifact through the repo's pickle loader.
- Copies loaded parameter arrays into Theano shared variables.
- Compiles a Theano generator function `_gen`.

Because construction compiles Theano code, use the bundled dry-run scripts for
planning unless native execution is explicitly intended.

## Supported config functions

The model config module exposes the following functions. All models use
`n_layers=3`, `n_f=128`, and `npx=64`.

| Config function | npx | n_layers | n_f | nc | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `outdoor_64()` | 64 | 3 | 128 | 3 | RGB landscape model. |
| `shoes_64()` | 64 | 3 | 128 | 3 | RGB shoe-photo model. |
| `handbag_64()` | 64 | 3 | 128 | 3 | RGB handbag model. |
| `church_64()` | 64 | 3 | 128 | 3 | RGB church model. |
| `hed_shoes_64()` | 64 | 3 | 128 | 1 | One-channel HED shoe-sketch model. |

If `model_name` does not match a config function, native construction will fail
before generation. A custom model needs both a config function and a compatible
artifact.

## Model file convention and expected contents

The default convention used by the sample script is:

```text
./models/<model_name>.<model_type>
```

For the standard model type this becomes:

```text
./models/outdoor_64.dcgan_theano
```

The loaded artifact is expected to behave like a pickled dictionary with keys:

| Key | Used for |
| --- | --- |
| `disc_params` | Discriminator parameter values. |
| `gen_params` | Generator parameter values; required for sample generation. |
| `disc_batchnorm` | Discriminator batchnorm state. |
| `gen_batchnorm` | Generator batchnorm state; required for sample generation. |
| `predict_params` | Optional predictor values for projection workflows. |
| `predict_batchnorm` | Optional predictor batchnorm state. |

The inference sample workflow needs generator parameters and generator
batchnorm. Projection workflows may care about the optional predictor keys and
are routed to the image-projection sub-skill.

## Generation methods

### `model_G(z)`

Symbolic generator mapping `z -> x`. It calls the generator graph with clipped
and optionally tanh-normalized latent values. This is an internal Theano graph
entry point, not a direct NumPy image-generation helper.

### `model_D(x)`

Symbolic discriminator mapping `x -> probability`. It is present in the model
class but is not used by random sample generation.

### `model_P(x)`

Symbolic predictor mapping `x -> z`. It is relevant to projection/inversion and
should be handled by the image-projection sub-skill.

### `gen_samples(z0=None, n=32, batch_size=32, use_transform=True)`

Public helper used by the standalone sample script.

Behavior:

- Requires `n % batch_size == 0` for the default random path.
- If `z0` is omitted, samples latent vectors uniformly from `[-1, 1]` with shape
  `(n, 100)`.
- If `z0` is provided, sets `n = len(z0)` and uses a batch size of at least `64`.
- Runs the compiled generator in batches.
- Concatenates batches along axis `0`.
- If `use_transform=True`, converts generated tensors to image-space arrays and
  casts to `uint8` after scaling by `255`.

The sample script calls:

```python
samples = model.gen_samples(z0=None, n=196, batch_size=49, use_transform=True)
```

Expected post-transform shape for RGB models is `(196, 64, 64, 3)`. For the HED
shoe model, expect a one-channel generation path that may be tiled later for
visualization.

## Transform behavior

### `transform(x, nc=3)`

- For `nc == 3`, expects image arrays shaped `(N, H, W, 3)`, transposes to
  `(N, 3, H, W)`, converts to float, and scales from `[0, 255]` to `[-1, 1]`.
- For non-RGB, transposes to `(N, 1, H, W)` and scales by `1 / 255.0`.

### `transform_mask(x)`

- Transposes mask arrays to channel-first order and scales by `1 / 255.0`.
- Constraint-map workflows own the mask semantics.

### `inverse_transform(x, npx=64, nc=3)`

- For `nc == 3`, reshapes generated tensors to `(N, 3, npx, npx)`, transposes to
  `(N, npx, npx, 3)`, and maps from `[-1, 1]` back to `[0, 1]`.
- For `nc == 1`, reshapes to `(N, 1, npx, npx)`, transposes to
  `(N, npx, npx, 1)`, and returns `1.0 - x`.

After inverse transform, `gen_samples(..., use_transform=True)` multiplies by
`255` and casts to `uint8`.

## Grid visualization facts

The sample script creates a `14 x 14` grid from `196` generated samples. The
grid helper tiles one-channel samples into three channels for visualization.
For a 64x64 RGB model, the final grid array is expected to be roughly
`896 x 896 x 3` before OpenCV writes it.

The script converts color order immediately before writing:

```python
im_vis = cv2.cvtColor(im_vis, cv2.COLOR_BGR2RGB)
cv2.imwrite(args.output_image, im_vis)
```

If colors appear swapped in a downstream reproduction, verify whether the array
is RGB or BGR at each save/display boundary before modifying the model.

## Backend and dependency implications

The model definition imports Theano CUDA/cuDNN APIs, custom Theano ops,
activation/init utilities, NumPy, and repo-local helper modules. Sample writing
also imports OpenCV. A modern Python environment that can run the dry-run helper
scripts is not proof that native `dcgan_theano.Model` construction will work.

Use this sub-skill to build commands and report prerequisites; only claim native
model operation after a real run writes the sample image and reports
`samples_shape`.
