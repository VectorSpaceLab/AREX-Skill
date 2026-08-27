# Inference CLI Reference

## `test.py` Single-Image Translation

| Argument | Default | Meaning | Operational notes |
| --- | --- | --- | --- |
| `--config` | required by practical use | Network/config YAML | Must match the checkpoint architecture and direction. |
| `--input` | required | Input image path | Loaded as RGB, resized, converted to tensor, normalized to `[-1, 1]`. |
| `--output_folder` | required | Folder for outputs | Created if missing. |
| `--checkpoint` | required | Generator checkpoint | Expected to contain `a` and `b` generator state dicts; old PyTorch 0.3 checkpoints are converted by fallback helper. |
| `--style` | empty | Optional style image | When non-empty, `num_style` is forced to 1. |
| `--a2b` | `1` | Direction flag | `1` encodes domain A and decodes domain B; `0` encodes B and decodes A. |
| `--seed` | `10` | Random seed | Applied to CPU and CUDA RNGs. |
| `--num_style` | `10` | Number of random styles | Ignored down to 1 when `--style` is set. |
| `--synchronized` | off | Parser flag | Present in `test.py` but not used by the single-image body. |
| `--output_only` | off | Save only translated outputs | If off, also saves `input.jpg`. |
| `--output_path` | `.` | Path for VGG/log/checkpoint support | Used to set `config['vgg_model_path']`. |
| `--trainer` | `MUNIT` | `MUNIT` or `UNIT` | UNIT writes one `output.jpg`; MUNIT writes `output000.jpg`, `output001.jpg`, ... |

Safe builder example:

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

The builder prints a `python test.py ...` command but does not execute it.

## `test_batch.py` Folder Translation and Metrics

| Argument | Default | Meaning | Operational notes |
| --- | --- | --- | --- |
| `--config` | `configs/edges2handbags_folder` in parser | Network/config YAML | Provide the actual `.yaml` path; parser default lacks extension. |
| `--input_folder` | required | Folder of images to translate | Enumerated through the same `ImageFolder` helper. |
| `--output_folder` | required | Output prefix/folder | MUNIT writes to `output_folder_00`, `output_folder_01`, ... for each style; UNIT writes under `output_folder`. |
| `--checkpoint` | required | Generator checkpoint | Same `a`/`b` state dict expectation as single-image inference. |
| `--a2b` | `1` | Direction flag | `1`: A to B; `0`: B to A. |
| `--seed` | `1` | Random seed | Applied to CPU and CUDA RNGs. |
| `--num_style` | `10` | Number of styles per input for MUNIT | Creates one output folder suffix per style. |
| `--synchronized` | off | Reuse one fixed style set for all inputs | If off, samples new random style tensors per input. |
| `--output_only` | off | Avoid saving input copies | If off, saves input previews. |
| `--output_path` | `.` | VGG/log/checkpoint support path | Passed into config as `vgg_model_path`. |
| `--trainer` | `MUNIT` | `MUNIT` or `UNIT` | Controls sampling/output behavior. |
| `--compute_IS` | off | Compute Inception Score | Requires a pretrained Inception classifier path. |
| `--compute_CIS` | off | Compute Conditional Inception Score | Requires per-domain Inception classifier path. |
| `--inception_a`, `--inception_b` | `.` | Inception state dict paths | Direction chooses B for A-to-B metrics and A for B-to-A metrics. |

Safe builder example:

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

## Output Naming

- MUNIT single-image: `output000.jpg` through `outputNNN.jpg`, plus `input.jpg` unless `--output_only` is used.
- UNIT single-image: `output.jpg`, plus `input.jpg` unless `--output_only` is used.
- MUNIT batch: each style index writes into a suffixed folder like `<output_folder>_00/<basename>`, `<output_folder>_01/<basename>`.
- UNIT batch: writes `<output_folder>/<basename>`.

## Direction Decisions

Use `--a2b 1` for source domain A to target domain B and `--a2b 0` for B to A. The config alone does not infer the semantic domain names, so check how the dataset was arranged in `data-and-configuration` before selecting the flag.
