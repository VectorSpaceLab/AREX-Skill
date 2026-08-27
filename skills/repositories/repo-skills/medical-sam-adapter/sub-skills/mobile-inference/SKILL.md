---
name: mobile-inference
description: "Operate the documented MobileSAMv2 object-aware image inference
  route with explicit local weights, encoder selection, CUDA checks, and
  rendered output paths."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# MobileSAMv2 object-aware inference

Use this route only for the separately documented MobileSAMv2 inference path:
a local image directory is read, an object-aware detector supplies box prompts,
and a prompt-guided SAM decoder renders masks. This is not the adapter-training
CLI. Route training variants to [training](../training/SKILL.md), and route
image/dataset layout questions to [data preparation](../data-preparation/SKILL.md).

## Safe entry point

Run the bundled, preflight-only wrapper with explicit local paths:

```bash
python scripts/run_mobile_samv2.py \
  --ObjectAwareModel_path /abs/path/ObjectAwareModel.pt \
  --Prompt_guided_Mask_Decoder_path /abs/path/Prompt_guided_Mask_Decoder.pt \
  --encoder_path /abs/path/mobile_sam.pt \
  --encoder_type tiny_vit \
  --img_path /abs/path/images \
  --output_dir /abs/path/rendered \
  --preflight
```

`--dry-run` is an alias. Omitting both flags is also safe: this helper always
performs preflight and never imports PyTorch, the detector, or MobileSAMv2
model code. It never downloads, creates output files, or performs inference.
A passing result proves only the local path and static CLI contract; it is not a
model or CUDA smoke test.

## Operating sequence

1. Read [the exact CLI](references/cli-reference.md). Select one of the three
   operational encoder mappings and supply every checkpoint path explicitly.
2. Run the wrapper and fix every reported path, extension, image, output, or
   encoder error before attempting any model import.
3. For a separately maintained real runner, use the repository-qualified
   package layout `models.MobileSAMv2.mobilesamv2` and provide the detector
   dependency/import layout described in [dependencies and weights](references/dependencies-and-weights.md).
   The optional prompt-guided detector module was not executed in verification.
4. On CUDA only, follow [the source-equivalent workflow](references/workflows.md):
   convert OpenCV BGR images to RGB, detect boxes, transform boxes to the SAM
   input frame, decode in batches of 320, and render into the explicit output
   directory.
5. Keep input and output directories separate. Checkpoint files must be local,
   readable, and compatible with the selected builder; no implicit download is
   allowed.

## Non-negotiable caveats

- CUDA is required for actual inference. The source initially places the model
  on CPU when CUDA is unavailable, but later creates the transformed box tensor
  with `.cuda()` unconditionally. CPU execution is therefore not supported;
  CPU parsing/import is diagnostic only.
- The original parser advertises six encoder strings, but the standalone source
  mapping actually contains only `tiny_vit`, `sam_vit_h`, and
  `efficientvit_l2`. The helper reports the other three as parser-accepted but
  operationally unsupported instead of allowing a later `KeyError`.
- The source parser's path defaults and `create_model()` disagree: the parsed
  paths are not consistently used, and some weights are hard-coded relative to
  the process directory. The wrapper intentionally removes that ambiguity by
  requiring explicit paths.
- Never let a missing detector input become `source=None`; the detector can
  choose a demo URL in that case. The wrapper accepts only local paths and has
  no network client.
- Do not copy the vendored Ultralytics or EfficientViT trees into this skill.

## Verification boundary

The verified checks for this route are `--help`, deterministic parser behavior,
local path/extension/weight/image/output validation, and no-network behavior.
Full training, evaluation, detector/model imports, real checkpoints, rendered
inference, notebook execution, and external downloads are not final checks and
remain unrun because they have artifact, optional-dependency, CUDA, and output
side effects. For shared failures, use [the root troubleshooting guide](../../references/troubleshooting.md).

See [CLI reference](references/cli-reference.md), [dependencies and weights](references/dependencies-and-weights.md), [workflows](references/workflows.md), and [troubleshooting](references/troubleshooting.md).
