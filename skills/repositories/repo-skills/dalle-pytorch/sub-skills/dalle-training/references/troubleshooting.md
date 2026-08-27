# DALL-E training troubleshooting

## `dataset is empty`

Run:

```bash
python scripts/validate_image_text_folder.py /path/to/data --strict
```

Fix unmatched stems, empty caption files, unsupported image extensions, or duplicate stems. The source maps by stem rather than relative path, so two `cat.txt` files in different folders can collide.

## `Input ... is too long for context length`

Use `--truncate_captions`, reduce caption length, or create the model with a larger `text_seq_len`. Do not change `text_seq_len` when resuming a checkpoint unless the checkpoint was built with the new value.

## `VAE model file does not exist` or VAE checkpoint shape errors

A `--vae_path` checkpoint must be a standard file with `hparams` and `weights`, not a DeepSpeed partition directory. If the user has a DeepSpeed VAE checkpoint directory, explain that the helper does not support merging it directly into DALL-E training.

## OpenAI VAE default path fails

If no `--vae_path` is provided and `--taming` is not set, training uses `OpenAIDiscreteVAE`. Modern torch can trigger the torch `<=1.10` assertion. Prefer a trained VAE checkpoint or VQGAN unless the user accepts a legacy environment.

## W&B or checkpoint side effects

Training initializes W&B and writes DALL-E checkpoints before/throughout training. Ask before running in automated environments, and set W&B offline/disabled behavior according to user policy.

## CUDA or memory errors

The helper calls `.cuda()` for non-DeepSpeed training. Reduce `batch_size`, `depth`, `dim`, `heads`, `text_seq_len`, or image token length, or route to `distributed-and-backends` for reversible layers, DeepSpeed, AMP, or Horovod.

## WebDataset yields no samples

Check:

- `--wds` has exactly two comma-separated keys;
- keys match actual sample fields;
- the folder contains tar files when passing a directory;
- remote URL/GCS commands are available and authorized;
- captions are decodable UTF-8.
