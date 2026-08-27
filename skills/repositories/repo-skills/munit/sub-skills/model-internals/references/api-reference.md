# MUNIT model API reference

This reference is for code modification and porting. It records the model/trainer contracts without requiring a future agent to reopen the source files.

## Trainer classes

### `MUNIT_Trainer(hyperparameters)`

Purpose: two-domain multimodal image translation with separate content and style spaces.

Constructor effects and required config surfaces:

- Reads `input_dim_a`, `input_dim_b`, `gen`, `dis`, `lr`, `beta1`, `beta2`, `weight_decay`, `init`, and `display_size`.
- Creates `gen_a = AdaINGen(input_dim_a, gen)` and `gen_b = AdaINGen(input_dim_b, gen)`.
- Creates `dis_a = MsImageDis(input_dim_a, dis)` and `dis_b = MsImageDis(input_dim_b, dis)`.
- Stores `style_dim = gen.style_dim`.
- Creates fixed sampling style tensors `s_a` and `s_b` with shape `[display_size, style_dim, 1, 1]` on CUDA.
- Creates Adam optimizers over both generators and both discriminators, plus optional schedulers.
- Applies the configured initializer to all modules, then Gaussian initialization to discriminators.
- If `vgg_w > 0`, loads VGG through the selected utility path and freezes it.

Methods:

| Method | Inputs | Returns/effects | Notes |
|---|---|---|---|
| `recon_criterion(input, target)` | two tensors | mean absolute error | Used for image, style, and content reconstruction losses. |
| `forward(x_a, x_b)` | one batch from each domain | `(x_ab, x_ba)` | Encodes content/style, decodes cross-domain with fixed style tensors, toggles eval/train mode. |
| `gen_update(x_a, x_b, hyperparameters)` | two CUDA batches plus config | backpropagates and steps generator optimizer | Computes image recon, style recon, content recon, optional cycle image recon, adversarial losses, optional VGG losses, and `loss_gen_total`. |
| `dis_update(x_a, x_b, hyperparameters)` | two CUDA batches plus config | backpropagates and steps discriminator optimizer | Samples random target-domain styles, decodes fakes, detaches fakes, then computes discriminator losses. |
| `sample(x_a, x_b)` | display batches | eight image groups | Returns A, A recon, A-to-B with fixed/random style, B, B recon, B-to-A with fixed/random style. |
| `compute_vgg_loss(vgg, img, target)` | VGG module and two images | perceptual MSE after InstanceNorm | Calls the RGB-to-BGR VGG preprocessing utility. |
| `update_learning_rate()` | none | steps non-null schedulers | `constant` policy means no scheduler. |
| `resume(checkpoint_dir, hyperparameters)` | checkpoint directory and config | iteration integer | Loads latest generator/discriminator checkpoints plus optimizer state. |
| `save(snapshot_dir, iterations)` | directory and iteration index | writes `gen_%08d.pt`, `dis_%08d.pt`, `optimizer.pt` | Generator/discriminator checkpoints store dictionaries with `a` and `b` keys. |

MUNIT-specific loss/config keys: `gan_w`, `recon_x_w`, `recon_s_w`, `recon_c_w`, `recon_x_cyc_w`, `vgg_w`, and `gen.style_dim`.

### `UNIT_Trainer(hyperparameters)`

Purpose: the older UNIT-style variational shared-latent baseline using VAE-style generators.

Constructor differences from `MUNIT_Trainer`:

- Uses `VAEGen(input_dim_a, gen)` and `VAEGen(input_dim_b, gen)` instead of AdaIN generators.
- Does not create fixed style tensors and does not require `gen.style_dim` for diversity.
- Still creates `MsImageDis` for both domains, optimizers, schedulers, initializers, and optional VGG.

Methods mirror `MUNIT_Trainer` but loss names differ:

| Method | Important behavior |
|---|---|
| `forward(x_a, x_b)` | Encodes each domain, decodes the other domain's hidden representation, returns `(x_ab, x_ba)`. |
| `gen_update(x_a, x_b, hyperparameters)` | Computes image reconstruction, KL regularization, optional cycle image reconstruction, cycle KL regularization, adversarial losses, optional VGG losses, and `loss_gen_total`. |
| `dis_update(x_a, x_b, hyperparameters)` | Encodes/decode fakes and updates discriminators like MUNIT, without style sampling. |
| `sample(x_a, x_b)` | Returns six image groups: A, A recon, A-to-B, B, B recon, B-to-A. |

UNIT-specific required loss keys: `recon_kl_w` and `recon_kl_cyc_w`. The bundled MUNIT demo configs do not include these, so `--trainer UNIT` needs a UNIT-specific config, not just a CLI flag change.

## Generator classes

### `AdaINGen(input_dim, params)`

Required `params` keys: `dim`, `style_dim`, `n_downsample`, `n_res`, `activ`, `pad_type`, `mlp_dim`.

Internal graph:

- `enc_style = StyleEncoder(4, input_dim, dim, style_dim, norm='none', activ=activ, pad_type=pad_type)`. Style encoder downsampling is fixed at four stages for this implementation.
- `enc_content = ContentEncoder(n_downsample, n_res, input_dim, dim, norm='in', activ=activ, pad_type=pad_type)`.
- `dec = Decoder(n_downsample, n_res, enc_content.output_dim, input_dim, res_norm='adain', activ=activ, pad_type=pad_type)`.
- `mlp = MLP(style_dim, get_num_adain_params(dec), mlp_dim, 3, norm='none', activ=activ)`.

Methods and tensor contracts:

| Method | Contract |
|---|---|
| `forward(images)` | Encodes images into content/style and decodes reconstruction. |
| `encode(images)` | Returns `(content, style_fake)`. `style_fake` is `[N, style_dim, 1, 1]` because the style encoder ends with adaptive average pooling and a 1x1 conv. |
| `decode(content, style)` | Passes style through the MLP, assigns dynamic AdaIN parameters into the decoder, then decodes content. |
| `assign_adain_params(adain_params, model)` | Iterates over `AdaptiveInstanceNorm2d` modules; assigns flattened bias/weight slices per layer and consumes slices in order. |
| `get_num_adain_params(model)` | Sums `2 * num_features` for every AdaIN layer in the model. |

Do not call `dec(content)` directly for an AdaIN decoder unless the target AdaIN layers already have valid dynamic `weight` and `bias` tensors for the current batch.

### `VAEGen(input_dim, params)`

Required `params` keys: `dim`, `n_downsample`, `n_res`, `activ`, `pad_type`.

Internal graph:

- `enc = ContentEncoder(n_downsample, n_res, input_dim, dim, norm='in', activ=activ, pad_type=pad_type)`.
- `dec = Decoder(n_downsample, n_res, enc.output_dim, input_dim, res_norm='in', activ=activ, pad_type=pad_type)`.

Methods:

| Method | Contract |
|---|---|
| `encode(images)` | Returns `(hiddens, noise)`, where noise is sampled with the same size and CUDA device as `hiddens`. |
| `decode(hiddens)` | Returns decoded images from hidden content. |
| `forward(images)` | Intended to return `(images_recon, hiddens)`, but porters should inspect and test this path because the source assigns the tuple returned by `encode` to a single variable before calling `.size()`. Training/inference flows use `encode` and `decode` directly. |

## Discriminator class

### `MsImageDis(input_dim, params)`

Required `params` keys: `n_layer`, `gan_type`, `dim`, `norm`, `activ`, `num_scales`, `pad_type`.

Internal graph:

- Builds `num_scales` separate CNNs in a `ModuleList`.
- Each scale starts with a `Conv2dBlock(input_dim, dim, 4, 2, 1, norm='none')`.
- Then repeats `n_layer - 1` stride-2 blocks while doubling channels.
- Ends each scale with a 1x1 convolution to one output channel.
- Between scales, applies average pooling with kernel 3, stride 2, padding 1, and `count_include_pad=False`.

Methods:

| Method | Contract |
|---|---|
| `forward(x)` | Returns a list of discriminator outputs, one per scale. |
| `calc_dis_loss(input_fake, input_real)` | For every scale, computes discriminator loss with `lsgan` or `nsgan` semantics. |
| `calc_gen_loss(input_fake)` | For every scale, computes generator adversarial loss with `lsgan` or `nsgan` semantics. |

Supported `gan_type` values are `lsgan` and `nsgan`. Any other value raises an assertion.

## Encoder/decoder/block signatures

Verified constructor signatures:

| Class | Signature | Core behavior |
|---|---|---|
| `StyleEncoder` | `StyleEncoder(n_downsample, input_dim, dim, style_dim, norm, activ, pad_type)` | Conv stem, two mandatory downsamplings, optional extra downsamplings, adaptive average pooling, 1x1 style projection. |
| `ContentEncoder` | `ContentEncoder(n_downsample, n_res, input_dim, dim, norm, activ, pad_type)` | Conv stem, `n_downsample` stride-2 blocks, then `n_res` residual blocks. Exposes `output_dim`. |
| `Decoder` | `Decoder(n_upsample, n_res, dim, output_dim, res_norm='adain', activ='relu', pad_type='zero')` | Residual blocks first, then nearest upsample + layer-normalized conv blocks, then tanh output conv. |
| `Conv2dBlock` | `Conv2dBlock(input_dim, output_dim, kernel_size, stride, padding=0, norm='none', activation='relu', pad_type='zero')` | Pad, convolution or spectral-normalized convolution, optional normalization, optional activation. |
| `LinearBlock` | `LinearBlock(input_dim, output_dim, norm='none', activation='relu')` | Linear or spectral-normalized linear, optional normalization, optional activation. |
| `AdaptiveInstanceNorm2d` | `AdaptiveInstanceNorm2d(num_features, eps=1e-5, momentum=0.1)` | Holds dummy running stats; `weight` and `bias` are assigned dynamically before forward. |
| `LayerNorm` | `LayerNorm(num_features, eps=1e-5, affine=True)` | Normalizes per sample over all non-batch dimensions; optional learned `gamma`/`beta`. |

Supported options:

| Surface | Supported values | Notes |
|---|---|---|
| Padding | `reflect`, `replicate`, `zero` | Config comments mention `zero` and `reflect`; the block also supports `replicate`. |
| Normalization | `bn`, `in`, `ln`, `adain`, `none`, `sn` | `adain` is for decoder residual blocks; `sn` wraps the layer with spectral normalization and sets no separate norm. |
| Activation | `relu`, `lrelu`, `prelu`, `selu`, `tanh`, `none` | Unsupported strings raise assertions at construction. |
| Initialization | `gaussian`, `xavier`, `kaiming`, `orthogonal`, `default` | Set through the selected utility initializer. |
| Scheduler | `constant`, `step` | Other policies return `NotImplementedError` from the scheduler helper. |

## Selected utility helpers relevant to internals

| Helper | Why model modifiers care |
|---|---|
| `get_scheduler(optimizer, hyperparameters, iterations=-1)` | Only `constant` and `step` are implemented; changing config policies needs a helper change. |
| `weights_init(init_type='gaussian')` | Applies initialization to Conv/Linear modules by class-name prefix; custom layers may be skipped unless adapted. |
| `get_model_list(dirname, key)` | Resume picks the lexicographically last `.pt` file containing `gen` or `dis`; naming conventions affect resume. |
| `pytorch03_to_pytorch04(state_dict_base, trainer_name)` | Removes selected old InstanceNorm running-stat keys from generator state dicts for MUNIT/UNIT loading. |
| `load_vgg16(model_dir)` | Can create directories, run a network download command, convert a Torch7 file with `load_lua`, and save converted weights. Avoid in static inspection. |
| `vgg_preprocess(batch)` | Converts normalized RGB tensors to BGR `[0, 255]`, subtracts fixed VGG means, and creates a CUDA mean tensor. |
| `get_slerp_interp(nb_latents, nb_interp, z_dim)` | Produces style interpolation latents shaped `[N, z_dim, 1, 1]`, matching MUNIT style-code shape. |

## Data/API touchpoints that affect model shapes

Data layout details belong to `../data-and-configuration/`, but model edits must preserve these interfaces:

- `input_dim_a` and `input_dim_b` determine generator/discriminator input channels for domains A and B.
- Training loaders normalize image tensors to `[-1, 1]` using mean/std of `0.5` per RGB channel.
- Inference loaders convert inputs to RGB, so default inference expects three-channel images unless code and configs are intentionally changed.
- `new_size` or `new_size_a`/`new_size_b` controls preprocessing size before crop or inference transform; changing resolution affects memory more than class signatures.
