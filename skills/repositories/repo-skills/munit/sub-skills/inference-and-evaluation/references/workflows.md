# Inference and Evaluation Workflows

## Preflight Before Any Translation

1. Confirm a legacy-compatible runtime in `../environment-and-setup/`. Parser checks can run on CPU, but real translation calls CUDA unconditionally.
2. Confirm the config matches the checkpoint architecture: trainer type, `gen.style_dim`, channel counts, resize keys, and generator/discriminator dimensions.
3. Provide local paths for input image or folder, output folder, and checkpoint. This skill does not download checkpoints.
4. Build the command with a bundled dry-run helper and review warnings before executing from the user's MUNIT checkout.

## Multimodal Single-Image Translation

Use MUNIT when the goal is multiple random target styles for one source image:

```bash
python scripts/munit_inference_command.py \
  --repo-root /path/to/user/munit-checkout \
  --config configs/edges2shoes_folder.yaml \
  --input inputs/edges2shoes_edge.jpg \
  --checkpoint models/edges2shoes.pt \
  --output-folder outputs/edges2shoes \
  --a2b 1 \
  --num-style 10
```

After explicit user approval in a compatible CUDA runtime, the printed command has the shape:

```bash
python test.py --config configs/edges2shoes_folder.yaml --input inputs/edges2shoes_edge.jpg --output_folder outputs/edges2shoes --checkpoint models/edges2shoes.pt --a2b 1 --num_style 10 --trainer MUNIT
```

Expected output is a numbered set of target images. The default `num_style` is 10.

## Example-Guided Translation

Use `--style` to encode a style image from the target domain. In the original script, any non-empty style path forces `num_style = 1` even if the CLI says a larger number:

```bash
python scripts/munit_inference_command.py \
  --repo-root /path/to/user/munit-checkout \
  --config configs/edges2shoes_folder.yaml \
  --input inputs/edges2shoes_edge.jpg \
  --style inputs/edges2shoes_shoe.jpg \
  --checkpoint models/edges2shoes.pt \
  --output-folder outputs/example_guided \
  --a2b 1
```

Check that the style image belongs to the target domain for the selected direction.

## B-to-A Translation

For the reverse direction, set `--a2b 0`. The source input should now be from domain B, and the optional style image should be from domain A.

## Batch Translation

Use `test_batch.py` for folder inputs:

```bash
python scripts/munit_batch_command.py \
  --repo-root /path/to/user/munit-checkout \
  --config configs/edges2shoes_folder.yaml \
  --input-folder datasets/edges2shoes/testA \
  --output-folder outputs/batch_edges2shoes \
  --checkpoint models/edges2shoes.pt \
  --a2b 1 \
  --num-style 5 \
  --synchronized
```

MUNIT writes each style index to a separate suffixed output folder. Use `--synchronized` when the user wants the same style samples applied across all input images; omit it when each input should receive independently sampled styles.

## Optional Metrics

`test_batch.py` can compute Inception Score (`--compute_IS`) and Conditional Inception Score (`--compute_CIS`). These metrics require an Inception model checkpoint path for the target domain. See `evaluation-metrics.md`; do not enable metrics unless the user provides the model paths and accepts the extra assumptions.

## Checkpoint Compatibility

The inference scripts first try to load checkpoint dictionaries directly into `gen_a`/`gen_b`. If that fails, they call the bundled conversion helper for PyTorch 0.3 to 0.4 InstanceNorm running-stat keys. This helps old official checkpoints but is not a general architecture converter. Route style-dimension or architecture shape mismatches to `../model-internals/`.
