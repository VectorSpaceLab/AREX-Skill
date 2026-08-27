---
name: model-zoo-and-apis
description: "Select pytorch-semseg model architectures, instantiate safe
  segmentation models, and inspect API registries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# model-zoo-and-apis

Use this sub-skill when the user needs to choose a pytorch-semseg architecture id, instantiate a segmentation model through the package API, inspect registries for losses/optimizers/schedulers/augmentations, or debug model/API import failures.

## Route here

- Choose among model ids: `fcn32s`, `fcn16s`, `fcn8s`, `unet`, `segnet`, `pspnet`, `icnet`, `icnetBN`, `linknet`, `frrnA`, `frrnB`.
- Build a `ptsemseg.models.get_model(model_dict, n_classes, version=None)` payload.
- Instantiate a no-download architecture for import/API smoke testing.
- Inspect `loss`, `optimizer`, `scheduler`, `augmentation`, `runningScore`, `averageMeter`, or `convert_state_dict` APIs.
- Explain FCN/SegNet VGG weight-download side effects, FRRN A/B ambiguity, protobuf/caffe import errors, model shape errors, and DataParallel state-dict prefixes.

## Route elsewhere

- Dataset layouts, dataset keys, filesystem paths, and YAML schema validation: use `data-and-configs`.
- `train.py` or `validate.py` command execution, checkpoint training/evaluation, and metric interpretation from full runs: use `training-and-evaluation`.
- `test.py` single-image CLI, checkpoint filename parsing for inference, palette decoding, and DenseCRF: use `single-image-inference`.

## Safe workflow

1. Read `references/api-reference.md` for model ids, verified constructor signatures, registry keys, and safe examples.
2. Run the bundled registry helper from an environment where `ptsemseg` is importable:

   ```bash
   python scripts/smoke_model_registry.py --list-only
   ```

3. For a no-download CPU model smoke, prefer explicit FRRN payloads:

   ```bash
   python scripts/smoke_model_registry.py --smoke --model-id frrnA --n-classes 2 --height 64 --width 64
   ```

4. If the user requests `frrnA` or `frrnB`, always include `model_type: "A"` or `model_type: "B"` in the `model_dict`; the registry maps both ids to the same constructor.
5. Do not call `get_model` for `fcn32s`, `fcn16s`, `fcn8s`, or `segnet` merely to test imports unless the user accepts the `torchvision.models.vgg16(pretrained=True)` weight-cache/network side effect.
6. Use `references/troubleshooting.md` when imports fail, unknown keys are reported, small tensors fail in deep models, or checkpoints contain `module.` prefixes.

## Bundled files

- `references/api-reference.md` — verified signatures, registry tables, examples, and API caveats.
- `references/troubleshooting.md` — failure-mode matrix and fixes.
- `scripts/smoke_model_registry.py` — safe argparse helper for registry listing and optional FRRN CPU smoke.
