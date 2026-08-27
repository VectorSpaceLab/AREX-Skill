# Inference Troubleshooting

## Parser accepts a value but generation fails later

`parse_args()` does not validate every runtime constraint. For example, `--video-length 128` can parse, but `HunyuanVideoSampler.predict` and the pipeline reject it for the default VAE because `(128 - 1) % 4 != 0`. Use 65, 129, or another `4n+1` frame count.

## Prompt errors

`predict()` requires `prompt` to be a string. If the user passes `None`, a list, or another object directly to the API, fix the call before loading models.

## Seed-list errors

If passing a list of seeds, its length must equal `batch_size` or `batch_size * num_videos_per_prompt`. For most one-prompt workflows, prefer one integer `--seed` and let the code expand it.

## Latent-channel mismatch

The default VAE name `884-16c-hy` implies 16 latent channels. Do not override `--latent-channels` unless the VAE changes too; otherwise the parser sanity check raises a mismatch error.

## Missing weights

If the error mentions an invalid model path, missing `model_path`, or no recognized `.pt` file, return to `../checkpoint-and-setup/SKILL.md` and validate `--model-base` and `--dit-weight`.

## OOM or slow generation

HunyuanVideo is large. Use lower resolution, `--use-cpu-offload`, FP8, or multi-GPU xDiT as appropriate. Do not claim CPU mode can generate equivalent videos; CPU checks only validate non-generation logic.
