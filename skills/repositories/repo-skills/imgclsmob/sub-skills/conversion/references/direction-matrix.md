# Conversion direction matrix

This matrix is derived from the `if`/`elif` dispatch in this repository's
`convert_models.py` snapshot. Framework labels are exact lower-case strings.
A framework package being importable, or appearing in the parser help, does not
make it a valid source or destination for the CLI.

## Dispatched edges

| Source `--src-fwk` | Destination `--dst-fwk` | Function | Source contract | Destination contract |
|---|---|---|---|---|
| `gluon` | `gluon` | `convert_gl2gl` | Local Gluon parameter file consumed by `gluon.utils.prepare_model` | Gluon parameters written to `--dst-params` |
| `gluon` | `pytorch` | `convert_gl2pt` | Local Gluon parameter file | PyTorch state dictionary written with `torch.save`; convention `.pth` |
| `gluon` | `chainer` | `convert_gl2ch` | Local Gluon parameter file | Chainer NPZ written with `chainer.serializers.save_npz`; convention `.npz` |
| `gluon` | `keras` | `convert_gl2ke` | Local Gluon parameter file | Keras/MXNet `save_weights` artifact; convention `.h5` |
| `gluon` | `tensorflow` | `convert_gl2tf` | Local Gluon parameter file; the destination is constructed as a TF1 graph | TF1 variables saved through `tensorflow_.utils.save_model_params`, normally an `.npz` path |
| `gluon` | `tf2` | `convert_gl2tf2` | Local Gluon parameter file | TF2 Keras weights written with `save_weights`; convention `.tf2.h5` |
| `pytorch` | `pytorch` | `convert_pt2pt` | File accepted by `torch.load`; a dict containing `state_dict` is unwrapped | PyTorch state dictionary written with `torch.save` |
| `pytorch` | `gluon` | `convert_pt2gl` | File accepted by `torch.load`; `--remove-module` handles a DataParallel wrapper when used | Gluon parameters written to `--dst-params` |
| `mxnet` | `gluon` | `convert_mx2gl` | MXNet checkpoint prefix passed to `mx.model.load_checkpoint(prefix=..., epoch=0)`; use the prefix, not a made-up extension | Gluon parameters written to `--dst-params` |
| `tensorflow` | `tensorflow` | `convert_tf2tf` | NumPy archive readable by `np.load`, normally a TF1 archive | TF1 parameter archive written through `save_model_params` |
| `tensorflow` | `gluon` | `convert_tf2gl` | NumPy archive readable by `np.load` | Gluon parameters written to `--dst-params` |
| `tf2` | `tfl` | `convert_tf22tfl` | **CLI branch ignores `--src-params`** and calls TF2 `prepare_model` with `use_pretrained=True` and an empty path; this may obtain pretrained weights | Raw TFLite bytes written directly to `--dst-params`; `--dst-model` is required by the parser but is not used in this branch; convention `.tflite` |

The source labels accepted by the real parser are not enumerated there; the
above table is the dispatch truth. There is no dispatched `tf2 -> tensorflow`,
`tf2 -> gluon`, `keras -> *`, `chainer -> *`, `mxnet -> mxnet`, or any other
edge. There is no dispatched destination `mxnet`. Do not infer directions from
package names.

The bundled inspector's `--list` prints these exact edges and function names.
It deliberately has no repository or ML-package imports.

## Exact `convert_models.py` flags

The real parser requires these four identity flags:

```text
--src-fwk STR                source framework label
--dst-fwk STR                destination framework label
--src-model STR              source model name
--dst-model STR              destination model name
```

Checkpoint and behavior flags:

```text
--src-params PATH            source parameter file or MXNet prefix (default "")
--dst-params PATH            destination parameter path (default "")
--load-ignore-extra          ignore extra source keys in Gluon/PyTorch loading
--remove-module              handle a stored PyTorch DataParallel module wrapper
--src-num-classes INT        source class count (default 1000)
--src-in-channels INT        source input channel count (default 3)
--dst-num-classes INT        destination class count (default 1000)
--dst-in-channels INT        destination input channel count (default 3)
--model-type STR             documented values image/audio; parser does not enforce
--save-dir PATH              logging/output directory (default "")
--logging-file-name NAME     log file name (default train.log)
```

The parser gives empty defaults to both parameter paths, but a real conversion
will generally fail or write to an unintended location without explicit local
paths. The inspector therefore requires both paths for a plan. It rejects a
source/destination path collision and only performs an opt-in presence check
when `--check-files` is supplied.

### Flag scope and shape implications

- `--load-ignore-extra` and `--remove-module` are parsed for every edge.
  `load-ignore-extra` is used while preparing Gluon or PyTorch sources;
  `remove-module` is used only while preparing a PyTorch source. If both are
  supplied for PyTorch, `load-ignore-extra` takes that loader branch and
  `remove-module` is not used. Extra-key filtering is not a shape conversion.
- The CLI carries separate class and input-channel values for source and
  destination construction. The Gluon and PyTorch preparation branches use the
  values they receive; TF1/TFL source handling and the current TF2 destination
  construction do not universally consume them. `gluon -> gluon` explicitly
  permits a fine-tune mismatch and skips mismatched parameters. Other edges
  normally require equal counts, names/order, and shapes; changing
  class/channel values is not a general conversion recipe. The source's special
  grouped-convolution, Chainer, and model-specific ordering cases remain
  implementation details, not a guarantee for arbitrary model pairs.
- `--model-type` is passed only when constructing a TF2 destination. The source
  code tests `model_type == "image"`; any other value selects its audio branch.
  The inspector requires `image` or `audio` so an accidental typo is blocked.
  The flag is otherwise ignored by conversion code.
- `--save-dir` and `--logging-file-name` configure `cvutil` logging. They are
  not a dry-run or output-format selector. The conversion destination is
  `--dst-params`.

## Artifact and TensorFlow rules

Use these conventions as review hints, not proof; the CLI does not enforce file
extensions:

- Gluon: `.params`
- PyTorch: `.pth`
- Chainer: `.npz`
- Keras/MXNet: commonly `.h5`
- TF1 archive: commonly `.npz`
- TF2 weights: `.tf2.h5`
- TFLite bytes: `.tflite`

`tensorflow` is the TF1 graph/session implementation: TF1 variables are
assigned and saved as a compressed NumPy archive. `tf2` is the TF2/Keras
implementation: models are built/called once, and weights are transposed where
needed before `save_weights`. `tfl` is not a training framework and is only the
TF2-to-TFLite destination.

A separately prepared local-input wrapper should receive these arguments;
this runtime skill only validates the direction and does not bundle or execute
a TensorFlow exporter:

```text
--model MODEL --input ./model.tf2.h5 --output-dir ./tflite-out
```

The source example's `--input-shape` default is `(1, 640, 480, 3)`. It is
declared as a single `int` with a tuple default, while the implementation
slices it as a sequence. Consequently, `--input-shape 224` fails later and
`--input-shape 1 224 224 3` is rejected by argparse in this snapshot. Do not
present custom multi-value shape commands as verified. The wrapper should
require an existing output directory, convert, allocate an interpreter, invoke
random input using the interpreter's actual input shape, and compare the
result to the Keras model.

## Evidence and backend boundary

The repository requirements include NumPy, MXNet, PyTorch/torchvision, Chainer,
Keras with an MXNet backend, TensorFlow, TensorFlow Addons, tensorpack, and
`cvutil`. Backend installation and compatibility diagnosis belong to the
framework-compatibility route.

The focused native conversion tests are evidence of particular setups, not a
blanket support claim:

- `tests/convert_gl2pt_batchnorm.py`, `convert_gl2pt_conv2d.py`, and
  `convert_gl2pt_dense.py` create `mx.gpu(0)`, move the PyTorch model/input with
  `.cuda()`, and compare outputs against an absolute-sum threshold of `1e-5`.
- The `tests/convert_gl2tf_*.py` cases use `mx.gpu(0)`, TF1 placeholders and
  `tf.Session`; the `convert_gl2tf2_*.py` cases use `mx.gpu(0)` and TF2 Keras,
  often transposing channels-last outputs back to NCHW before a `1e-5` check.

Therefore CPU-only versions of those examples are unverified and optional,
not passed. Do not claim that the CLI's `use_cuda=False` initialization is a
native CPU verification result.
