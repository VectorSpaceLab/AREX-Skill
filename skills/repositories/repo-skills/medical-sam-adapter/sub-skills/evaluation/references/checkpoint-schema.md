# Checkpoint schema and compatibility

## Evaluation wrapper required by `val.py`

The independent evaluator loads `-weights` with a CUDA map location and then
indexes these keys directly:

| Key | Required by `val.py` | Meaning in the training saver |
|---|---|---|
| `epoch` | Yes | Epoch number saved as `epoch + 1`. |
| `best_tol` | Yes | Best-tolerance field written by the training path. |
| `state_dict` | Yes | Model parameters used for `net.load_state_dict`. |
| `model` | No | Model name metadata, written by training; normally a string such as `sam`. |
| `optimizer` | No | Optimizer state mapping, written by training but not restored by `val.py`. |
| `path_helper` | No | Mapping containing training output paths; written by training, but independent evaluation ignores it. |

A missing `epoch`, `best_tol`, or `state_dict` is a wrapper error even if the
file contains a usable-looking raw model state dict. The training saver writes
all six named fields (`epoch`, `model`, `state_dict`, `optimizer`, `best_tol`,
and `path_helper`) into `best_dice_checkpoint.pth` under the run's `Model/`
directory. Note that the saver stores `best_dice` under the key `best_tol`; the
independent evaluator reads the field but does not use it to select a model.
Do not infer compatibility from the filename; inspect the contents.

`state_dict` must be a non-empty mapping of string parameter names to tensor
values that matches the freshly constructed network. The bundled helper marks
missing required fields and malformed state-dict entries nonzero. The three
training metadata fields (`model`, `optimizer`, and `path_helper`) are not
indexed by `val.py`; their absence is a warning, while a present value with the
wrong broad type is a schema error. `val.py` calls
`net.load_state_dict(...)` with the default strict behavior, so missing or
unexpected keys and shape differences stop loading. Unlike the resume branch
in `train.py`, independent evaluation does not use `strict=False`.

## Distributed prefix behavior

The source has an asymmetric but intentional convention:

- During training, when `-distributed` is not `none`, the saver uses
  `net.module.state_dict()`. These saved keys are the underlying, unprefixed
  names.
- During independent validation, when `-distributed` is not `none`, the loader
  creates a new mapping with `'module.' + key` for every key before loading.
  The network was wrapped with `torch.nn.DataParallel`, whose names require
  that prefix.
- With `-distributed none`, validation uses the checkpoint mapping unchanged
  and the network is not wrapped.

Therefore a distributed evaluation expects an **unprefixed** `state_dict` from
the training saver and adds exactly one `module.` prefix. A checkpoint already
containing `module.` keys will become `module.module.*` and fail. Conversely,
using an unwrapped single-GPU evaluation for a DataParallel-prefixed mapping
will report missing/unexpected keys. `inspect_checkpoint.py` reports the
observed prefix so this decision is made before loading the model.

`-distributed` is a comma-separated string of GPU ids consumed by
`DataParallel`; it is not a boolean. Select the same device visibility and
model configuration that the checkpoint was trained with. Distributed versus
single-GPU loading does not change the metric formulas, but it changes the
required key namespace and available memory.

## Base checkpoint versus adapter wrapper

`-sam_ckpt` is passed to `get_network` while constructing the base model;
`-weights` is loaded afterward as the adapter/training wrapper. They are
separate inputs:

- Original SAM model construction selects an encoder from `default`, `vit_b`,
  `vit_l`, or `vit_h`. Its builder reads the supplied base file, keeps only
  keys that exist in the constructed model with equal shapes, and loads them
  non-strictly. A canonical missing base filename can trigger an interactive
  download prompt in the source; do not rely on that behavior in a controlled
  evaluation.
- EfficientSAM construction has its own registry (`default`, `vit_s`,
  `vit_t`) and expects its checkpoint's `model` mapping when a checkpoint is
  supplied. Do not pass an original SAM file as an EfficientSAM file.
- MobileSAM construction has its own registry and checkpoint conventions. The
  standalone MobileSAMv2 object-aware route is separate; route it to
  [mobile inference](../../mobile-inference/).

An adapter checkpoint is architecture-specific. Match at least `-net`,
`-encoder`, `-image_size`, `-multimask_output`, and the adaptation/model
variant used to create it. A changed number of mask tokens, encoder, image
embedding size, adapter/LoRA structure, or output channels commonly produces
strict loading errors or invalid results. Route choices about how to create a
compatible model to [training](../../training/); this reference owns only
loading/evaluation compatibility.

## Safe inspection

Use the bundled read-only helper:

```bash
python scripts/inspect_checkpoint.py --checkpoint /path/to/file.pth
```

It loads only when the user explicitly supplies a path, maps to CPU, prefers
PyTorch's `weights_only=True`, prints metadata and bounded key summaries, and
never instantiates a model or writes output. A valid evaluation wrapper should
show `epoch`, `best_tol`, and a non-empty tensor-valued `state_dict`; the helper
also reports whether keys are unprefixed, `module.`-prefixed, or mixed. A raw
base-model state dict can still be inspected, but the helper reports that it is
not the `val.py` wrapper schema and exits nonzero so it is not mistaken for
`-weights`. If the installed PyTorch has no `weights_only` parameter, it refuses
legacy arbitrary-pickle loading and exits with a clear diagnostic rather than
silently weakening the safety policy.
