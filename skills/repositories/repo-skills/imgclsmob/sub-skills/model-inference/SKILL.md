---
name: model-inference
description: "Select, prepare, and run verified Gluon or PyTorch/pytorchcv
  image-classification models with safe CPU defaults, strict local checkpoints,
  ImageNet preprocessing, and output checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model inference

Use this skill for one-batch image-classification inference, model selection,
local checkpoint loading, input preprocessing, or lightweight model statistics
through the Gluon or PyTorch/pytorchcv providers.

## Safe default

Start from the sub-skill directory with a non-pretrained `resnet18` CPU smoke:

```bash
python scripts/infer_gluon.py --model resnet18
python scripts/infer_pytorch.py --model resnet18
```

Both scripts construct random weights by passing `pretrained=False`, use one
normalized `(1, 3, 224, 224)` input, and print the output shape, parameter count,
and zero-based top-k class indices/probabilities. If `--image` is omitted, the
input is a zero-valued RGB image before normalization, so the result is only a
shape/device smoke and has no accuracy meaning.

The scripts never request or download pretrained weights. A checkpoint is
accepted only as an existing local file; use `--checkpoint FILE` with the same
provider, model, class count, and input-channel count used to create it. The
PyTorch script also accepts `--remove-module` for a checkpoint saved under
`torch.nn.DataParallel`.

## Route by intent

1. Select a provider-supported model name. The providers lowercase the name
   and raise `ValueError` for an unsupported model; they do not infer aliases.
2. Keep `pretrained=False` for smoke tests. If using `--checkpoint`, keep the
   model and `--classes` aligned with the checkpoint and let strict loading
   expose missing, extra, or shape-incompatible parameters.
3. Apply the ImageNet RGB preprocessing in
   [checkpoints-and-inputs.md](references/checkpoints-and-inputs.md).
4. Assert that the input is NCHW and the output is rank-2 with batch size one
   before interpreting top-k results.
5. Use [api-reference.md](references/api-reference.md) for provider and local
   loading contracts. Use [troubleshooting.md](references/troubleshooting.md)
   for recovery.

Do not turn this route into training, resume, or dataset evaluation. Send
those requests to [training-evaluation](../training-evaluation/SKILL.md). Send
cross-framework parameter conversion to [conversion](../conversion/SKILL.md).
Send TensorFlow, Keras, and Chainer requests to
[framework-compatibility](../framework-compatibility/SKILL.md).
