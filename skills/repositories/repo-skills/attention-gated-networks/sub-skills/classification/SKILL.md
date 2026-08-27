---
name: classification
description: "Guides Attention-Gated Networks ultrasound classification
  workflows, including Sononet training, evaluation, HDF5 data layout, and
  attention overlays."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classification

Use this sub-skill for ultrasound scan-plane classification tasks in
Attention-Gated Networks. It covers Sononet, Sononet2, Sononet Grid Attention,
`FeedForwardClassifier`, `AggregatedClassifier`, the HDF5 ultrasound loader,
classification training/testing scripts, and attention overlay export.

## Read first

- Read [api-reference.md](references/api-reference.md) when you need exact
  model names, wrapper behavior, config fields, aggregation modes, or class and
  function signatures.
- Read [data-layout.md](references/data-layout.md) before preparing the
  ultrasound HDF5 file or debugging loader/sampler failures.
- Read [workflows.md](references/workflows.md) for training, testing,
  checkpoint evaluation, model inspection, and safe attention-overlay export.
- Read [troubleshooting.md](references/troubleshooting.md) when CUDA,
  torchsample, Visdom, sampler, HDF5, or overlay failures appear.
- Run [run_classifier.py](scripts/run_classifier.py) for skill-owned training
  and testing commands that replace the source repo's root entry points.
- Run [export_attention_overlay.py](scripts/export_attention_overlay.py) to
  replace the source repo's hard-coded attention visualization script with a
  parameterized, skill-owned helper.
- For fast environment validation, run the root helper
  `../../scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode classification`.

## When to use this sub-skill

Use this route when the user asks to:

- train or test ultrasound scan-plane classification models;
- choose between `sononet`, `sononet2`, and `sononet_grid_attention`;
- configure `aggregated_classifier`, deep supervision, or attention aggregation;
- inspect classifier outputs, class counts, losses, or scikit-learn metrics;
- prepare or validate the `us` HDF5 dataset layout;
- export compatibility-score attention maps or overlay PNGs;
- debug classification-specific CUDA, Visdom, sampler, HDF5, or checkpoint
  issues.

Route 3D segmentation, NIfTI validation, and multi-attention U-Net feature-map
exports to `../segmentation/SKILL.md` instead.

## Quick workflow

1. Install the repository with CUDA-enabled PyTorch and the legacy
   `torchsample` dependency. Then run:

   ```bash
   python ../../scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode classification
   ```

2. Prepare an ultrasound HDF5 file with `x_train`, `p_train`, `x_val`, `p_val`,
   `x_test`, `p_test`, and `label_names`. See [data-layout.md](references/data-layout.md).
3. Copy a Sononet config and replace its dataset path. The source configs use
   `model.output_nc=14`, `input_nc=1`, `tensor_dim='2D'`, and `gpu_ids=[0]`.
4. Train with the bundled replacement when real data is available:

Relative config paths are resolved from the explicit `--repo-root`; relative
`data_path` values are resolved from the config file's parent. The HDF5 data
file and any checkpoint/weights must already exist outside this skill. Bundled
runners and `check_env.py --config ...` reject missing or private `/vol/...`
paths before constructing a dataset.

   ```bash
   python scripts/run_classifier.py --repo-root /path/to/Attention-Gated-Networks --config path/to/config.json --mode train
   ```

5. Evaluate a checkpoint with the bundled replacement:

   ```bash
   python scripts/run_classifier.py --repo-root /path/to/Attention-Gated-Networks --config path/to/config.json --mode test
   ```

6. For attention models, use `model_type='sononet_grid_attention'` and read
   [workflows.md](references/workflows.md) before choosing `aggregation_mode` and
   `aggregation`.
7. Export a safe synthetic overlay, or adapt the command for a real 2D input:

   ```bash
   python scripts/export_attention_overlay.py \
     --repo-root /path/to/Attention-Gated-Networks \
     --config configs/config_sononet_grid_att_8.json \
     --output-dir /tmp/ag-net-attention
   ```

## Key decisions

- CUDA is required for the unmodified wrappers because the model and tensor
  paths call `.cuda()`.
- The stock ultrasound configs assume 14 classes. Do not reuse them unchanged
  for a different HDF5 label set.
- `AggregatedClassifier` is for multiple-output attention models. Plain
  Sononet classifiers use `FeedForwardClassifier`.
- Synthetic smoke checks prove wiring only; they do not replace training on the
  real ultrasound HDF5 file or evaluating a real checkpoint.
- The original attention visualization script hard-codes private paths. Use the
  bundled helper or parameterize your own script rather than running it as-is.

The source `train_classifaction.py` contains a 10-hour sleep after the final
epoch's updates. It is retained in the source checkout for provenance; use the
bundled runner when a bounded run without that hold is required.

## Expected outputs

Training writes checkpoints and logs below the configured checkpoint directory
and experiment name. Testing writes accumulated metrics and a `test_result.pkl`
inside the model save directory. The bundled attention helper writes overlay
PNGs and `.npy` arrays to the requested output directory.
