# Configuration Reference

## Core Paths

Common config fields:

```yaml
data: dataset/data/train.pkl
valdata: dataset/data/val.pkl
tokenizer: dataset/tokenizer.json
model_path: checkpoints
output_path: outputs
load_chkpt: null
name: pix2tex
```

Keep paths relative to the working directory you use for training or make them
absolute. If you build a custom tokenizer, update both `tokenizer` and
`num_tokens`.

## Training Parameters

Important fields include:

- `epochs`, `batchsize`, `micro_batchsize`: effective batch and gradient memory.
- `optimizer`, `lr`, `betas`, `scheduler`, `gamma`, `lr_step`: optimizer and
  scheduler selection.
- `sample_freq`, `save_freq`, `testbatchsize`, `valbatches`: validation and
  checkpoint cadence.
- `wandb`, `id`, `debug`: W&B logging/resume behavior and debug mode.

## Image and Sequence Bounds

- `max_width`, `max_height`, `min_width`, `min_height`: image filters and model
  positional capacity.
- `channels`: normally 1.
- `patch_size`: must be compatible with the encoder/backbone.
- `max_seq_len`: formula token length cap.

## Architecture Fields

- `encoder_structure`: `hybrid` or `vit`.
- `backbone_layers`: ResNetV2 backbone layers for hybrid encoder.
- `dim`, `encoder_depth`, `num_layers`, `heads`, `decoder_args`: transformer
  model size and attention options.
- `num_tokens`, `bos_token`, `eos_token`, `pad_token`: tokenizer/vocabulary
  contract.

## Safe Config Inspection

Run:

```bash
python scripts/summarize_pix2tex_config.py path/to/config.yaml
```

The helper validates required keys, reports model/data dimensions, and warns
about missing referenced files without importing torch or starting training.
