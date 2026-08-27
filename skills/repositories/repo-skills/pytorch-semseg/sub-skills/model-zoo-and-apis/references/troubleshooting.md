# model/API troubleshooting

Use this matrix for pytorch-semseg model registry, constructor, import, utility, and checkpoint-loading problems. Route dataset, training, validation, or single-image CLI issues to the neighboring sub-skill named in the scope row.

## Scope routing

| User problem | Owner |
| --- | --- |
| Unknown `model.arch`, constructor kwargs, loss/optimizer/scheduler/augmentation keys, metric utilities, state-dict prefixes | `model-zoo-and-apis` |
| Dataset root paths, split files, YAML schema, loader options | `data-and-configs` |
| `train.py`/`validate.py`, checkpoints from training, full metric reports | `training-and-evaluation` |
| `test.py`, image path/output path, DenseCRF, palette decoding | `single-image-inference` |

## Common failures

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| `TypeError: Descriptors cannot be created directly` while importing `ptsemseg.models`, `pspnet`, or `icnet` | Generated `ptsemseg/caffe_pb2.py` is incompatible with modern protobuf runtimes. PSPNet/ICNet import this generated module for Caffe model loading support. | Prefer installing `protobuf<3.21`. Temporary workaround: run with `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`. The bundled helper sets this workaround for inspection, but production environments should pin protobuf when possible. |
| `get_model({"arch": "fcn8s"}, ...)` or SegNet/FCN construction tries to download weights | `get_model` initializes FCN and SegNet variants with `torchvision.models.vgg16(pretrained=True)`, which may read or populate the torchvision weights cache and can trigger network access. | Do not use FCN/SegNet `get_model` for routine smoke checks. Use `scripts/smoke_model_registry.py --list-only` or FRRN smoke. Only instantiate FCN/SegNet through `get_model` when the user accepts cache/network behavior or has weights already available. |
| User asks for `frrnA`, but output behaves like FRRN-B | Registry ids `frrnA` and `frrnB` both map to the shared `frrn` constructor, whose default is `model_type='B'`. The dispatcher does not inject `model_type`. | Require explicit payloads: `{"arch": "frrnA", "model_type": "A"}` or `{"arch": "frrnB", "model_type": "B"}`. Treat missing `model_type` as ambiguous. |
| `arch` spelling seems valid but error is confusing, e.g. `TypeError: exceptions must derive from BaseException` | The source registry tries to raise a string for unknown model ids. Modern Python converts that into a confusing type error. | Validate against the exact registry ids: `fcn32s`, `fcn16s`, `fcn8s`, `unet`, `segnet`, `pspnet`, `icnet`, `icnetBN`, `linknet`, `frrnA`, `frrnB`. Check case sensitivity. |
| Unknown loss key | `cfg["training"]["loss"]["name"]` is not in the loss registry. | Use one of `cross_entropy`, `bootstrapped_cross_entropy`, `multi_scale_cross_entropy`. `bootstrapped_cross_entropy` also needs `K`. |
| Unknown optimizer key | `cfg["training"]["optimizer"]["name"]` is not in the optimizer registry. | Use one of `sgd`, `adam`, `adamax`, `asgd`, `adadelta`, `adagrad`, `rmsprop`. |
| Unknown scheduler key | `scheduler_dict["name"]` is not in the scheduler registry. | Use one of `constant_lr`, `poly_lr`, `multi_step`, `cosine_annealing`, `exp_lr`. Pass a copy into `get_scheduler` if the original dict must keep its `name`, because the function mutates the dict. |
| Unknown augmentation key | `get_composed_augmentations` indexes `key2aug` directly and raises `KeyError` for unknown keys. | Use one of `gamma`, `hue`, `brightness`, `saturation`, `contrast`, `rcrop`, `hflip`, `vflip`, `scale`, `rsize`, `rsizecrop`, `rotate`, `translate`, `ccrop`. Note that source `scale` expects an integer long-side size. |
| Forward pass fails with pooling, convolution, crop, or tensor-size errors on tiny inputs | Deep segmentation models downsample repeatedly and some FCN/PSP/ICNet paths use large classifier kernels or pyramid pooling. Small inputs may collapse spatial dimensions or mismatch skip crops. | Use the helper's FRRN default `64x64` only for registry smoke. For FCN/PSP/ICNet/SegNet behavior, use architecture-appropriate segmentation sizes or the documented constructor `input_size`; do not infer production safety from tiny tensors. |
| Warnings about `nn.functional.upsample`, `pretrained=True`, `size_average`, or `reduce` | The repo targets older PyTorch/torchvision APIs. Modern runtimes keep compatibility but warn about renamed arguments/functions. | Treat these as compatibility warnings unless the call fails. Modern replacements are `F.interpolate`, torchvision `weights=...`, and reduction arguments, but do not edit runtime behavior unless maintaining a fork. |
| Checkpoint load has many missing/unexpected keys beginning with `module.` | Checkpoint was saved from `torch.nn.DataParallel`, while current model is not wrapped the same way. | Run `ptsemseg.utils.convert_state_dict(state_dict)` before loading into a non-DataParallel model. If the current model is wrapped in DataParallel, keep prefixes consistent instead. |
| `ModuleNotFoundError: ptsemseg` | The checkout is not an installable packaging project in the usual `setup.py`/`pyproject.toml` sense, so the source root must be importable. | Run scripts from the repository root, or put the source root on `PYTHONPATH`, or use an environment that registers the source root. Do not expect `pip install -e .` to work unless packaging files are added. |
| `No module named pydensecrf` | Optional DenseCRF is relevant to single-image inference, not model registry inspection. | Route to `single-image-inference`. Normal model registry and FRRN smoke checks do not require DenseCRF. |
| Metrics produce `nan` for some classes | `runningScore` computes per-class IoU/accuracy from the confusion matrix; absent classes have zero denominators. | This is expected for classes absent from a small validation slice. Use representative labels or interpret `nan` as absent-class evidence rather than a model API failure. |

## Safe debugging order

1. Run the no-download registry listing:

   ```bash
   python scripts/smoke_model_registry.py --list-only
   ```

2. If import succeeds, run an explicit FRRN CPU smoke:

   ```bash
   python scripts/smoke_model_registry.py --smoke --model-id frrnA --n-classes 2 --height 64 --width 64
   ```

3. If model selection is the issue, compare the payload against `references/api-reference.md`.
4. If the failure involves datasets, command-line training/evaluation, or single-image inference, stop and route to the appropriate sub-skill rather than expanding this scope.
