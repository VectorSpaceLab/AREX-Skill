# Model architecture and losses

## Main components

The model is a conditional GAN built from these pieces:

- **Encoder**: progressively downsamples the source glyph image to a compact
  representation.
- **Embedding lookup**: turns the style label into a learned conditioning vector
  that is concatenated with the encoder bottleneck.
- **Decoder**: upsamples through transpose convolutions and skip connections to
  reconstruct the target glyph.
- **Discriminator**: judges real/fake and predicts the style category.

## Loss terms

| Loss | Role |
| --- | --- |
| Adversarial cheat loss | Push generator outputs toward realistic target glyphs |
| L1 loss | Keep generated glyphs close to the paired target image |
| Category loss | Encourage the discriminator to predict the style label |
| Constant / encoding loss | Keep source and generated encodings aligned |
| TV loss | Optional smoothing regularizer for generated output |

When `flip_labels=1`, an additional no-target branch reuses source images with
shuffled labels so the model can keep learning when the discriminator becomes
overconfident.

## Important shapes and identifiers

- Input placeholders expect batches of paired images with channels split into
  source and target halves.
- `embedding_num` must be greater than the maximum style label ID.
- `embedding_dim` controls the width of the style code concatenated with the
  bottleneck.
- `batch_size` must remain fixed throughout graph construction and training.
- `inst_norm=1` activates conditional instance normalization in decoder layers
  except the final output layer.

## Data provider behavior

`model/dataset.py` pads batches to a multiple of the batch size so the graph can
use fixed transpose-convolution shapes. Validation is an infinite iterator that
keeps cycling through the validation set. Fine-tuning filters training and
validation records to selected labels.

## Output and checkpoint conventions

- `get_model_id_and_dir()` combines `experiment_id` and `batch_size`.
- `checkpoint()` writes TensorFlow checkpoints into the model directory.
- `validate_model()` writes paired real/fake sample images.
- `export_generator()` saves only generator variables, including the style
  embedding and `g_` variables.

## Practical implications

- If you change the batch size, embedding count, or normalization mode, old
  checkpoints may no longer restore cleanly.
- CPU graph construction can validate the architecture and names, but it does
  not prove that long training or GPU performance will be acceptable.
- The architecture uses TensorFlow 1 APIs that expect explicit sessions and
  graph initialization.
