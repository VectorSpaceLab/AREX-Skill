---
name: inference-and-evaluation
description: "Build and debug MUNIT single-image, example-guided, batch
  translation, and IS/CIS evaluation commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Inference and Evaluation

Use this sub-skill when the user wants to translate images with a trained MUNIT or UNIT checkpoint, produce diverse samples, use an example style image, process an input folder, or reason about optional Inception Score / Conditional Inception Score metrics.

## Responsibilities

- Construct safe commands for `test.py` single-image inference and `test_batch.py` folder inference without loading checkpoints or starting CUDA by default.
- Explain A-to-B versus B-to-A direction, random style sampling, synchronized style codes, example-guided style, `num_style`, and output naming.
- Diagnose missing checkpoint/config/input paths, style/config mismatches, output folder surprises, and old checkpoint conversion behavior.
- Distinguish core translation from optional IS/CIS metric computation and its additional Inception-model prerequisites.

## Start Here

1. Confirm runtime and checkpoint prerequisites in `../environment-and-setup/`; unmodified inference calls `.cuda()` and needs a compatible legacy runtime.
2. Validate the YAML and any input folders in `../data-and-configuration/` when the command uses a config or batch folder.
3. Read `references/workflows.md` for single-image, example-guided, and batch recipes.
4. Use a bundled command builder to print the command without executing it:

   ```bash
   python scripts/munit_inference_command.py --help
   python scripts/munit_inference_command.py \
     --repo-root /path/to/user/munit-checkout \
     --config configs/edges2shoes_folder.yaml \
     --input inputs/edges2shoes_edge.jpg \
     --checkpoint models/edges2shoes.pt \
     --output-folder outputs/edges2shoes \
     --a2b 1 \
     --num-style 10
   ```

5. For folder inference or metrics, use:

   ```bash
   python scripts/munit_batch_command.py --help
   ```

## Route Elsewhere

- Installing the legacy PyTorch/CUDA stack or triaging import failures: `../environment-and-setup/`.
- Editing configs, dataset folders, or list files: `../data-and-configuration/`.
- Training checkpoints or resume behavior: `../training/`.
- Changing model architecture, checkpoint key conversion, or modernizing source code: `../model-internals/`.

## Safety Gates

- Do not auto-download pretrained checkpoints, Inception models, datasets, or VGG assets.
- Do not run actual inference unless the user provides local asset paths, accepts CUDA/runtime requirements, and authorizes execution.
- Do not treat `--help` success as proof that a checkpoint can run; help checks validate parser coverage only.
- Do not claim CPU inference support for the unmodified scripts. They move models, inputs, styles, and tensors to CUDA.

## Reference Map

- `references/workflows.md` - practical single-image, example-guided, batch, direction, and output recipes.
- `references/cli-reference.md` - exact `test.py` and `test_batch.py` flags and defaults.
- `references/evaluation-metrics.md` - IS/CIS metric prerequisites and interpretation boundaries.
- `references/troubleshooting.md` - symptom-driven fixes for checkpoint, style, direction, output, metric, and legacy-runtime failures.
- `scripts/munit_inference_command.py` - safe single-image/example-guided command builder.
- `scripts/munit_batch_command.py` - safe batch/metric command builder.
