# Model/config troubleshooting

## Dependency and backend failures

- **`ModuleNotFoundError: timm`, `addict`, or `einops`:** install the pinned
  inspection/runtime dependencies from the project environment plan before
  importing model/config modules. The repository has no packaging metadata;
  being in the checkout does not install `geoseg`.
- **`ModuleNotFoundError: mamba_ssm` or CUDA extension errors:** this is an
  optional PyramidMamba prerequisite. The source imports `mamba_ssm.Mamba` at
  module import, so even inspecting that module's constructors can fail. Keep
  PyramidMamba out of a claimed supported path until `mamba_ssm` and its
  compatible `causal-conv1d`/PyTorch/CUDA toolchain are installed and a forward
  smoke passes. Do not “fix” this by pretending the model is a standard
  DCSwin.
- **CPU probe passes but GPU run fails:** the verified CUDA smoke used an A100
  (compute capability 8.0). A CPU import does not prove CUDA kernels,
  checkpoint loading, memory capacity, or attention-window behavior. Repeat a
  small CUDA constructor/forward probe on the target backend.
- **timm pretrained download/cache error:** set `pretrained=False` for a
  random-init import/shape test, or provide a valid cache/network policy. That
  test must not be reported as pretrained validation.

## Data and config import failures

- **`FileNotFoundError` during `py2cfg` from LoveDA:** expected when the data
  layout is absent. Importing `loveda_dataset` constructs `loveda_val_dataset`
  and lists both Urban and Rural image/mask directories immediately. Prepare
  `data/LoveDA/Val/{Urban,Rural}/images_png` and
  `masks_png_convert` (and the configured training root) before live import;
  use `inspect_config.py` when you only need field/path discovery.
- **Image/mask count assertion:** Potsdam, Vaihingen, and UAVID enumerate
  paired directories and assert equal counts. Check extensions, stems, and
  split output directories rather than deleting the assertion.
- **Relative path appears wrong:** paths such as `data/potsdam/train` and
  `pretrain_weights/stseg_small.pth` are interpreted relative to the process
  working directory. Run from the intended project root or make paths
  deliberate in a private adapted config; do not rely on the directory of the
  config file.
- **Missing `pretrain_weights/*.pth`:** DCSwin, FTUNetFormer, and BANet call
  `torch.load` when `pretrained=True` and a non-null `weight_path` is supplied.
  For an uninitialized smoke test use `pretrained=False` or `weight_path=None`.
  For real transfer initialization, verify the file and its state-dict shape.
- **Missing output/checkpoint path:** `weights_path` is a save directory, not a
  backbone file. Ensure it is writable before training; `test_weights_name`
  must match the actual `.ckpt` stem when a test script loads a checkpoint.

## Label, loss, and model mismatches

- **`AssertionError`/CUDA CE error about target range:** print unique mask
  values and compare them with `0..num_classes-1` plus the config's
  `ignore_index`. For LoveDA/Potsdam/Vaihingen the checked configs use 7/6/6;
  UAVID uses 255. A class-count mismatch commonly occurs when reusing a model
  factory default of 4 or 6.
- **`one_hot` or Dice failure on ignored pixels:** ensure the chosen Dice/CE
  instances receive the same ignore value and that transforms pad with that
  value. Never pass 255 into a loss configured with ignore 6, or vice versa.
- **Tuple/tensor loss error:** UNetFormer returns `(main, aux)` only in
  training mode. Set `use_aux_loss=True` and use `UnetFormerLoss` for the
  checked UNetFormer configs. Single-output models use `use_aux_loss=False`
  and a loss that accepts one logits tensor. If adapting ABCNet's three-output
  training result, design and test a dedicated loss/metric branch.
- **Unexpected metric class count:** `Evaluator(num_class)` must equal the
  prediction head's channel count. Its aggregate values can exclude the last
  class for Potsdam/Vaihingen in the training workflow, but its confusion
  matrix still needs all six classes.

## Optimizer, checkpoint, and monitor failures

- **Backbone learning-rate rule has no effect:** `process_model_params` uses
  regex matching against parameter names. Confirm names begin with
  `backbone.` and inspect group learning rates after construction. A renamed
  module can silently lose the lower backbone rate.
- **Checkpoint callback says monitored key is unavailable:** choose exactly a
  metric logged by the training module (`val_mIoU`, `val_F1`, or `val_OA`) and
  use `monitor_mode='max'` for the checked configs. Validate with one synthetic
  validation step before a long run.
- **Resume/pretrained confusion:** `pretrained_ckpt_path` loads a Lightning
  model before fitting; `resume_ckpt_path` is passed to `trainer.fit`; a
  `pretrain_weights/*.pth` file is only a backbone/model initialization asset.
  Do not put a backbone path in a Lightning checkpoint field.
- **Lookahead or scheduler state mismatch:** preserve the configured wrapper
  and scheduler together when loading/resuming. Changing `max_epoch` or
  scheduler type mid-run invalidates assumptions about annealing/restarts.

## Safe recovery checklist

1. Run `python scripts/inspect_config.py path/to/config.py` and review imports,
   model/loss calls, dataset roots, weight paths, and output paths.
2. Prepare only the required data layout and optional dependencies.
3. Run a `pretrained=False` tiny shape probe, then separately test explicit
   pretrained loading if the asset exists.
4. Assert `num_classes`, ignore value, target dtype/range, output shape, and
   auxiliary output contract.
5. Validate one optimizer step/metric update and one checkpoint monitor key;
   only then hand off to [training](../../training/SKILL.md) or
   [evaluation-inference](../../evaluation-inference/SKILL.md).
