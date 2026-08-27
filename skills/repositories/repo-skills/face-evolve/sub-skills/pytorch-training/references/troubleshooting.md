# PyTorch Training Troubleshooting

Use this reference when face.evoLVe PyTorch training, validation, checkpoint loading, or component inspection fails.

## `train.py` syntax error around `LOSS_DICT`

Symptom:

```text
SyntaxError: invalid syntax
```

Likely location: the loss dictionary block that mixes stable `Focal`/`Softmax` loss entries with experimental margin-head names.

Cause:

- Missing comma after the `Softmax` cross-entropy entry.
- Experimental entries refer to classes that are not imported or are misspelled (`AdaM_Softmax` vs `AM_Softmax`, `Circleloss` vs `CircleLoss`).
- One entry resembles `MV_Softmax.py()`, which is not valid Python.
- `SST_Prototype` is missing a colon in the checked block.
- Conceptual mismatch: margin-head classes are placed in `LOSS_DICT`, but the stable loop expects heads to produce logits and losses to consume logits.

Minimal stable repair:

```python
LOSS_DICT = {
    'Focal': FocalLoss(),
    'Softmax': nn.CrossEntropyLoss(),
}
```

Keep experimental heads out of `LOSS_DICT` unless you deliberately redesign the head/loss interface and write tests for forward signatures, return types, and device behavior.

## `head.metrics` import fails: `Module` is not defined

Symptom:

```text
NameError: name 'Module' is not defined
```

Cause: later experimental classes inherit from `Module`, but the head module imports `torch.nn as nn` and not `Module` itself.

Stable repair options:

- Add `from torch.nn import Module` near the other imports.
- Or change experimental class bases from `Module` to `nn.Module`.

The bundled inspector applies an in-memory `Module = torch.nn.Module` patch only for signature inspection. It does not modify source files and should not be treated as a training repair.

## bcolz / numpy compatibility problems

Symptoms include bcolz import/build failures, validation load errors, or ABI-related numpy errors.

Cause: the validation utilities use `bcolz.carray(...)`. bcolz is old and often requires a compatible Python/numpy combination.

Remedies:

- If validation is required, use a Python/numpy combination known to import bcolz successfully.
- If validation is not required, guard or remove `get_val_data` and `perform_val` calls instead of installing bcolz just for training-loss debugging.
- Do not claim LFW/CFP/AgeDB/CALFW/CPLFW/VGGFace2-FP validation unless the matching bcolz roots and `*_list.npy` files were actually loaded.

## Missing validation data

Symptom:

```text
FileNotFoundError
```

or bcolz errors mentioning a missing root such as `lfw`, `cfp_ff`, `cfp_fp`, `agedb_30`, `calfw`, `cplfw`, or `vgg2_fp`.

Cause: `get_val_data(DATA_ROOT)` expects all seven validation datasets under `DATA_ROOT`.

Remedies:

- Ask the user which validation datasets are available.
- Repair the validation block to evaluate only supplied datasets.
- If no validation data is available, skip validation and checkpoint after training epochs, while documenting that no validation metric was produced.
- Route validation-pair preparation and post-training verification metrics to `feature-extraction-verification` and data layout acquisition to `data-preparation`.

## `MULTI_GPU`, `GPU_ID`, and device mismatch

Common symptoms:

- CUDA device ordinal errors.
- Tensors on different devices.
- CPU-only host attempts to call `.cuda(...)` in a head.
- Training hangs or fails immediately after wrapping the backbone.

Causes:

- `MULTI_GPU=True` while no CUDA runtime is available.
- `GPU_ID` lists devices that are not visible to PyTorch.
- `DEVICE` points to one GPU while the head's model-parallel `device_id` list points elsewhere.
- A head was constructed with a non-`None` `device_id` during CPU inspection.

Remedies:

- For CPU inspection: `MULTI_GPU=False`, `DEVICE=cpu`, and construct heads with `device_id=None`.
- For one visible GPU: set `MULTI_GPU=False` or use `GPU_ID=[0]` consistently.
- For multiple GPUs: ensure IDs are relative to CUDA visibility, the first ID can hold concatenated logits, and the class count is large enough to justify model-parallel head splitting.
- Do not use a CPU smoke check as proof that multi-GPU training is verified.

## Checkpoint path or state mismatch

Symptoms:

- `No Checkpoint Found...` message despite expecting resume.
- `Missing key(s)` or `Unexpected key(s)` in `load_state_dict`.
- Size mismatch for final head weights.

Causes:

- Resume paths point to directories or placeholders, not files.
- Backbone checkpoint was created by a different backbone or input size.
- Head checkpoint class count differs from the current `ImageFolder` class count.
- `EMBEDDING_SIZE` changed.
- State dict keys include or omit a `module.` prefix unexpectedly.

Remedies:

- Verify both resume paths are actual `.pth` files.
- Compare `BACKBONE_NAME`, `INPUT_SIZE`, `HEAD_NAME`, class count, and `EMBEDDING_SIZE` with checkpoint provenance.
- Load backbone checkpoints before `DataParallel` wrapping when using the stable flow.
- If fine-tuning on new identities, load only the compatible backbone and initialize a new head.
- Route feature extraction from a trained checkpoint to `feature-extraction-verification`.

## BatchNorm and tiny-batch failures

Symptoms:

```text
Expected more than 1 value per channel when training
```

or unstable/lower-quality tiny runs.

Causes:

- Backbones end with `BatchNorm1d(512)` and many modules contain BatchNorm layers.
- Training mode with batch size 1 cannot compute useful BatchNorm statistics.
- `DROP_LAST=True` can drop all samples in very small fixtures.

Remedies:

- For component inspection, call `model.eval()` before synthetic forwards.
- For any training smoke, use batch size at least 2 and enough samples per class.
- Set `DROP_LAST=False` only for tiny debugging, not for full large-scale training unless intentionally changed.
- Treat tiny CPU training as a control-flow test, not an accuracy signal.

## Tiny fixture top-k and display frequency failures

Symptoms:

- `selected index k out of range` from top-k accuracy.
- Modulo-by-zero error or no progress printing.

Causes:

- The stable training loop asks for `topk=(1, 5)` even when `NUM_CLASS < 5`.
- `DISP_FREQ = len(train_loader) // 100` becomes zero for fewer than 100 batches.

Remedies:

- Use `max_k = min(5, NUM_CLASS)` before requesting top-k metrics.
- Set `DISP_FREQ = max(1, len(train_loader) // 100)`.
- Keep these as source repairs for tiny/debug runs; they are not needed for normal large class counts.

## TensorBoardX or log path errors

Symptoms:

- Import error for `tensorboardX`.
- Permission or file errors creating event logs.
- Empty log view despite training.

Remedies:

- Install `tensorboardX` in the runtime environment or replace logging with native `torch.utils.tensorboard` after testing.
- Ensure `LOG_ROOT` exists and is writable.
- Use a distinct log directory per experiment to avoid confusing overlapping curves.

## Head API confusion

Symptoms:

- `TypeError` because `Softmax.forward()` received labels.
- `TypeError` because a margin head was called without labels.
- Loss receives a tuple instead of logits.
- Modern PyTorch raises an attribute error for `nn.init.zero_` while constructing the `Softmax` head.

Causes:

- `Softmax` head forward signature is `head(x)`.
- Stable margin heads require `head(features, labels)`.
- `MagFace` returns `(logits, regularizer)`, unlike stable heads.
- `SST_Prototype` uses a prototype/queue signature rather than `(features, labels)`.
- The `Softmax` head uses the legacy initializer name `nn.init.zero_` for bias initialization.

Remedies:

- Dispatch by head type.
- If using the `Softmax` head on modern PyTorch, replace `nn.init.zero_(self.bias)` with `nn.init.zeros_(self.bias)` or `self.bias.data.zero_()`.
- Keep experimental heads out of stable training until their forward returns and objectives are integrated.
- Run the bundled inspector with `--inspect-heads` to view signatures before editing training code.

## EfficientNet-like source import fails

Symptom:

```text
SyntaxError: invalid character ...
```

Cause: the EfficientNet-like backbone source contains stray non-Python text. Additional constructor/classmethod mismatches are likely even after removing that text.

Remedies:

- Treat EfficientNet-like support as repair-required.
- Prefer stable ResNet/IR/IR-SE backbones for training tasks unless the user specifically asks to repair EfficientNet-like code.
- If repairing, first make the file importable, then fix constructor/classmethod argument order, then run a CPU shape check before training.

## Full training is too expensive or unsafe

Skip or postpone full training when:

- The user asked only to inspect config or model support.
- Large training data is absent.
- Validation arrays are absent and validation was not explicitly disabled.
- The source still has syntax/import issues.
- GPU use has not been approved.
- The requested check can be satisfied by the bundled component inspector.

A safe substitute is a synthetic component smoke; it validates construction and shapes but not convergence, accuracy, checkpoint quality, or multi-GPU behavior.
