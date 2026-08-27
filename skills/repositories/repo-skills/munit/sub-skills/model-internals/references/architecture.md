# MUNIT architecture and dataflow

## Conceptual model

MUNIT assumes that an image representation can be separated into:

- a content code shared across the two domains; and
- a style code specific to a target domain.

For an A-to-B translation, the source-domain generator encodes content from an A image, then the target-domain decoder combines that content with a B-domain style code. Different sampled B styles produce different valid B outputs for the same A content.

## Domain modules

The implementation builds symmetric domain modules:

```text
MUNIT_Trainer
  gen_a: AdaINGen for domain A
  gen_b: AdaINGen for domain B
  dis_a: MsImageDis for domain A realism
  dis_b: MsImageDis for domain B realism
```

A `UNIT_Trainer` keeps the same discriminator layout but replaces AdaIN generators with `VAEGen` modules:

```text
UNIT_Trainer
  gen_a: VAEGen for domain A
  gen_b: VAEGen for domain B
  dis_a: MsImageDis for domain A realism
  dis_b: MsImageDis for domain B realism
```

## AdaIN generator flow

`AdaINGen` contains three conceptual parts:

```text
image
  ├─ StyleEncoder -> style code [N, style_dim, 1, 1]
  └─ ContentEncoder -> content feature map
style code -> MLP -> flat AdaIN parameters
content + assigned AdaIN parameters -> Decoder -> image
```

Important details:

- The style encoder always uses four downsampling stages in this implementation, ending in global average pooling and a 1x1 projection to `style_dim`.
- The content encoder uses `gen.n_downsample` and `gen.n_res` from config.
- The decoder starts with residual blocks. For MUNIT, those residual blocks use `AdaptiveInstanceNorm2d`.
- The MLP output size is exactly the number of decoder AdaIN parameters, computed as `2 * num_features` for every AdaIN layer.
- `decode(content, style)` must run the MLP and assign AdaIN parameters before calling the decoder.

Shape implications:

- Random or example style codes must have the configured `style_dim` and singleton spatial dimensions.
- Changing `gen.dim`, `gen.n_downsample`, or `gen.n_res` changes channel counts and therefore checkpoint compatibility.
- Changing `gen.style_dim` changes MLP input shape, fixed sampling tensors, inference style tensor shape, and checkpoint compatibility.

## UNIT VAE generator flow

`VAEGen` is a reduced VAE-style generator:

```text
image -> ContentEncoder -> hiddens
hiddens + sampled noise -> Decoder -> image reconstruction/translation
```

The training code calls `encode` and `decode` directly. `encode(images)` returns `(hiddens, noise)`, and the trainer adds the sampled noise before decoding during reconstruction and cross-domain translation.

Porting note: the standalone `VAEGen.forward` path should be tested before use because it treats the tuple returned by `encode` as if it were a tensor. The standard trainer/inference flows do not rely on that path.

## Multi-scale discriminator flow

`MsImageDis` builds one discriminator CNN per scale:

```text
input image -> scale 0 CNN -> prediction map
       |
       v average pool stride 2
    scale 1 CNN -> prediction map
       |
       v average pool stride 2
    scale 2 CNN -> prediction map
```

The number of scales is configurable. Every scale has the same architecture template but sees a progressively downsampled image. Losses are summed across scales.

Supported adversarial variants:

- `lsgan`: squared error to 0/1 targets.
- `nsgan`: binary cross entropy applied to sigmoid outputs with generated 0/1 target tensors.

## MUNIT update sequence

Generator update:

1. Sample random style tensors for A and B with shape `[batch, style_dim, 1, 1]`.
2. Encode A and B images into content/style pairs.
3. Decode within-domain reconstructions: A content + A style, B content + B style.
4. Decode cross-domain translations: B content + sampled A style, A content + sampled B style.
5. Re-encode translated images to reconstruct style and content.
6. Optionally decode cycle image reconstructions when `recon_x_cyc_w > 0`.
7. Compute image/style/content reconstruction losses, optional cycle losses, adversarial generator losses, and optional VGG perceptual losses.
8. Sum weighted losses and step the generator optimizer.

Discriminator update:

1. Sample random style tensors for both target domains.
2. Encode source content and decode cross-domain fake images.
3. Detach fake images.
4. Compute discriminator losses against fake and real images for both domains.
5. Sum weighted losses and step the discriminator optimizer.

## UNIT update sequence

Generator update:

1. Encode A and B into hidden tensors plus noise tensors.
2. Decode within-domain reconstructions from hidden + noise.
3. Decode cross-domain translations from the other domain's hidden + noise.
4. Re-encode translated images and optionally decode cycle reconstructions.
5. Compute image reconstruction, KL regularization, cycle image reconstruction, cycle KL, adversarial, and optional VGG losses.
6. Sum weighted losses and step the generator optimizer.

Discriminator update mirrors MUNIT but uses VAE hidden/noise paths instead of style sampling.

## Checkpoint architecture compatibility

A saved generator checkpoint stores two state dicts:

```text
{
  "a": domain A generator state,
  "b": domain B generator state
}
```

A saved discriminator checkpoint uses the same `a`/`b` shape. Optimizers are saved as:

```text
{
  "gen": generator optimizer state,
  "dis": discriminator optimizer state
}
```

Architecture-changing edits must be coordinated with checkpoint expectations:

- `input_dim_a`/`input_dim_b` changes first/last convolution channel counts.
- `gen.dim`, `gen.n_downsample`, and `gen.n_res` change encoder/decoder channels and module numbering.
- `gen.style_dim` changes style encoder output, MLP input, sampled style tensors, and checkpoint tensors.
- `dis.dim`, `dis.n_layer`, and `dis.num_scales` change discriminator state dict shapes.
- InstanceNorm running-stat keys from old checkpoints may need conversion before loading.
