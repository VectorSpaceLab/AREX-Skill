# Inference and Evaluation Troubleshooting

## Missing checkpoint

**Symptom:** command planning or runtime fails because `models/...pt` does not exist.

**Cause:** pretrained MUNIT checkpoints are external assets and are not bundled with this skill.

**Fix:** ask the user for a local checkpoint path or explicit permission to acquire one. Verify the checkpoint matches the config architecture and trainer type.

## Wrong direction or swapped domains

**Symptom:** the translated image semantics are reversed or the style image seems ignored/mismatched.

**Cause:** `--a2b 1` encodes domain A and decodes domain B; `--a2b 0` reverses it. The script does not infer domain names from filenames.

**Fix:** inspect the dataset/config domain arrangement in `../data-and-configuration/` and choose the flag deliberately. For example-guided translation, the style image must belong to the target domain.

## `--style` produces only one output

This is expected. `test.py` sets `num_style = 1` whenever a style image path is provided.

## Unexpected batch output folders

MUNIT batch inference writes one folder per style index using the prefix pattern `<output_folder>_00`, `<output_folder>_01`, and so on. UNIT writes directly under `<output_folder>`.

## Old checkpoint loading fallback

If direct state-dict loading fails, the script calls the PyTorch 0.3-to-0.4 conversion helper to remove selected InstanceNorm running-stat keys. This can rescue old official-format checkpoints, but it cannot fix architecture changes such as a different `style_dim`, channel count, generator depth, or discriminator shape.

## CUDA/runtime errors

Unmodified inference moves the model, input image, style image, and random style tensors to CUDA. If CUDA is unavailable, route to `../environment-and-setup/`. Do not claim CPU inference support unless the code has been ported and verified.

## IS/CIS metric failures

**Symptoms:** missing Inception checkpoint, classifier state-dict shape mismatch, SciPy import error, or GPU memory failure during 299x299 upsampling.

**Fix:** skip metrics unless the user specifically needs them and can provide domain-specific Inception model paths. Use core translation first, then enable one metric flag at a time.

## Output folder collisions

The scripts create output folders but do not protect against overwriting filenames. For repeated experiments, include a run-specific output folder. The command builders can help standardize output paths, but they do not create or delete directories.
