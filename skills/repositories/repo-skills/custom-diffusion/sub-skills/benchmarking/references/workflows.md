# Benchmark workflows

## Validate the sample folder

1. Confirm that `samples/` contains exactly the expected number of PNG files.
2. Confirm that `prompts.json` has one entry for every PNG stem.
3. Validate the `target_paths` string before launching an expensive metric job.

## Run evaluation

1. Use the validated sample root and the external target-image paths.
2. Keep the `+`-separated target order stable because it controls the metric suffix names.
3. Expect a pandas pickle to be updated at the `outpkl` path.

## Interpret the outputs

- `CLIP Text alignment` uses the prompt strings recorded in `prompts.json`.
- `CLIP Image alignment` and `DINO Image alignment` refer to the first target path.
- Later target paths add numeric suffixes such as `1`, `2`, and so on.

## Handoff from inference

The inference route should generate a prompt montage plus per-sample images under the delta directory. Once that layout is correct, the benchmarking route can validate the folder and move to the metric run.
