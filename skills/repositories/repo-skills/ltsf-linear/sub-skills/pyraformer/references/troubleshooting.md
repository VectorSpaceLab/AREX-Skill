# Troubleshooting

## Missing file or wrong path

**Symptom:** `FileNotFoundError` for a CSV or `.npy` file.

**Likely cause:** The `root_path`, `data_path`, or `-data_path` directory does not match the file tree.

**What to check:**

- Long-range runs need the benchmark CSV under the directory passed in `-root_path`.
- Single-step runs need the matching preprocessed files under `-data_path`.
- Synthetic runs need `data/synthetic.npy` when you are not regenerating it.

## Mask or shape mismatch

**Symptom:** Attention mask errors, tensor shape errors, or unexpected view/gather failures.

**Likely cause:** The model settings do not match the dataset assumptions.

**What to check:**

- `input_size` and `predict_step` must match the dataset preset you are using.
- `window_size` must be a Python list string, not a bare list object.
- `decoder=FC` and `decoder=attention` follow different shape paths.
- The single-step dataset presets fix the expected `input_size` in the source loader.

## TVM or CUDA-only failure

**Symptom:** TVM compile/load errors, CUDA index issues, or runtime assertion failures after enabling `use_tvm`.

**Likely cause:** The optional TVM path is being used without the required constant window pattern or without a compatible CUDA/TVM stack.

**What to check:**

- Keep `use_tvm=False` unless the user explicitly wants the advanced path.
- Use a constant `window_size` list when TVM is on.
- Treat `graph_attention.py` as a debug helper, not a default route.

## Single-step flag confusion

**Symptom:** Pretraining or hard-sample-mining seems to turn on or off in the opposite way you expected.

**Likely cause:** The single-step parser uses `store_false` for `-pretrain` and `-hard_sample_mining`.

**What to check:**

- In the long-range script, those flags enable the features.
- In the single-step script, passing the flags disables the features.

## Preprocessing surprises

**Symptom:** Some series disappear from the generated data or the output count is smaller than expected.

**Likely cause:** The preprocessing code intentionally filters sparse or too-short sequences.

**What to check:**

- Electricity preprocessing drops sequences that start too late.
- Flow preprocessing drops sparse or short app/zone groups.
- Wind preprocessing drops windows with no positive history.

## Checkpoint lookup failure

**Symptom:** `-eval` cannot find a model file.

**Likely cause:** The checkpoint path does not match the dataset key or forecast horizon.

**What to check:**

- Long-range eval uses `models/LongRange/<data>/<predict_step>/best_iter<i>.pth`.
- Single-step eval uses `models/SingleStep/<dataset>/best_model.pth`.

## Smoke expectations

The bundled smoke script checks CLI help and a preprocessing dry-run when the source environment is compatible.
It does not promise a dummy forward pass.

## Environment mismatch

**Symptom:** The source CLI fails immediately with an import error around `torch.functional.align_tensors` or a similar old-API symbol.

**Likely cause:** The current Python / PyTorch stack does not match the older Pyraformer runtime used by the upstream code.

**What to check:**

- Prefer the verified PyTorch 1.9.0 + CUDA 11.1 style environment for source entry-point checks.
- Re-run the smoke in the intended repo environment before changing the route or the model flags.
