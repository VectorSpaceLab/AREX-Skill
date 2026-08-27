# Dependencies and explicit weights

## Runtime dependency boundary

The inference path has two model families in one process:

1. **MobileSAMv2/SAM components**: the model registry and `SamPredictor` build
   the prompt-guided decoder and selected image encoder.
2. **Object-aware detector**: `ObjectAwareModel` subclasses the bundled
   Ultralytics YOLO runtime and uses `PromptModelPredictor` to return box
   results.

The detector is not an optional feature once this route is selected: without
its import and checkpoint, there are no object-aware boxes to decode. Its
checkpoint must be a local file accepted by that runtime. Do not replace it
with a generic detector without verifying the result schema (`results[0].boxes.xyxy`).

The valid package-qualified inspection/import route for the MobileSAMv2 package
is:

```python
from models.MobileSAMv2.mobilesamv2 import SamPredictor, sam_model_registry
```

The top-level spelling `from mobilesamv2 ...` is invalid in the verified
package layout because the package uses relative imports for `ImageEncoder`,
EfficientViT, and modeling modules. A separately maintained runner must make
the `models` package available in its chosen environment without pointing the
runtime skill at a particular checkout. The prompt-guided detector module also
needs its compatible Ultralytics dependency/import layout; it was not executed
in the bounded inspection and is an explicit runtime risk.

Do not import model code during preflight. The bundled helper deliberately does
not import torch, OpenCV, Matplotlib, Ultralytics, or MobileSAMv2. Do not use a
package constructor that receives a model name or missing filename: the
vendored detector runtime may interpret such values as downloadable assets.
Every model path must be an existing local file before model construction.

## Required local artifact set

Provide three explicit files:

- **ObjectAwareModel checkpoint**: the file passed to
  `--ObjectAwareModel_path`.
- **Prompt-guided mask decoder checkpoint**: the file passed to
  `--Prompt_guided_Mask_Decoder_path`. The builder expects a state dictionary
  with `PromtEncoder` and `MaskDecoder` entries (the misspelled
  `PromtEncoder` key is source behavior).
- **Selected image-encoder checkpoint**: the file passed to
  `--encoder_path`, compatible with the chosen operational encoder.

The source has two overlapping relative-path conventions that must not be
silently merged. The parser declares the following defaults:

```text
PromptGuidedDecoder/
  ObjectAwareModel.pt       # declared --ObjectAwareModel_path default
  Prompt_guided_Mask_Decoder.pt
```

But `create_model()` hard-codes `./weight/ObjectAwareModel.pt` for the
ObjectAwareModel constructor and `./PromptGuidedDecoder/Prompt_guided_Mask_Decoder.pt`
for the decoder, while the global encoder mapping is:

```text
weight/
  mobile_sam.pt             # tiny_vit mapping
  sam_vit_h.pt               # sam_vit_h mapping
  l2.pt                      # efficientvit_l2 mapping
```

Treat these as source evidence of path inconsistency, not a required
installation layout.
The adapted helper requires absolute-or-user-resolved explicit local paths and
checks `.pt`/`.pth` extensions. It does not copy, discover, or download these
files. A checkpoint with the right suffix but the wrong architecture remains a
model-load error; preflight cannot prove tensor compatibility.

## CUDA and backend rule

Actual inference requires a CUDA-enabled PyTorch installation and a visible
NVIDIA device. The source initially chooses `"cuda"` when available and
`"cpu"` otherwise, but later executes `torch.from_numpy(...).cuda()` for the
transformed boxes. Consequently CPU is not a supported fallback. A successful
CPU parser/import or preflight is diagnostic only, not an inference result.

Use a user-selected CUDA environment and explicit device policy. Do not copy
private activation commands or device identifiers into this skill. Confirm
CUDA availability and a small CUDA allocation before a real runner; if that
check fails, stop rather than letting the misleading CPU model placement
continue to a later `.cuda()` exception.

## No-network rule

All inputs are local paths. Reject URL schemes and missing files before model
imports. Never allow a missing detector source or checkpoint to fall through to
the detector's default source behavior: its implementation can select a demo
URL when `source=None`. This skill does not provide download commands or
network credentials. Obtain artifacts separately, then rerun the preflight.
