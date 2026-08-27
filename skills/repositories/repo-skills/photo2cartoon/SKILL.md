---
name: photo2cartoon
description: "Guide Photo2Cartoon portrait cartoonization workflows: assets,
  preprocessing, PyTorch or ONNX inference, dataset preparation, GAN training,
  model internals, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Photo2Cartoon

Use this repo skill when a task names **photo2cartoon**, Photo2Cartoon, portrait cartoonization, face-to-cartoon translation, U-GAT-IT + Soft-AdaLIN hourglass models, the `photo2cartoon_weights` assets, or the repo's preprocessing/training scripts.

Photo2Cartoon is a source-script repository, not a packaged Python distribution. Treat the generated skill as the operating manual and use a target checkout or ported module set only when the user explicitly needs to execute the code.

## First Checks

1. Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout.
2. Read `references/setup-and-assets.md` before installing dependencies or looking for weights.
3. Run the shared source/asset checker when a user supplies a checkout:

```bash
python scripts/check_repository_assets.py --root /path/to/photo2cartoon-checkout
```

4. If the task requires full visual inference, confirm that external model files exist; this checkout did not contain the published `.pt`, `.onnx`, `.pb`, or MobileFaceNet assets when the skill was generated.

## Route by Task

| User task | Read |
|---|---|
| Run or debug PyTorch `.pt` portrait inference, ONNX inference, output validation, or Cog-style prediction | `sub-skills/portrait-inference/SKILL.md` |
| Explain or port face detection, largest-face selection, rotation alignment, crop expansion, segmentation mask, alpha composition, or background whitening | `sub-skills/preprocessing/SKILL.md` |
| Prepare `trainA/trainB/testA/testB` folders, validate image data, understand `data_process.py`, or launch/resume GAN training | `sub-skills/data-and-training/SKILL.md` |
| Inspect `ResnetGenerator`, `Discriminator`, Soft-AdaLIN/LIN, checkpoint keys, Face ID loss, CAM heatmaps, or safe synthetic model checks | `sub-skills/model-internals/SKILL.md` |
| Diagnose cross-cutting install/import, asset, backend, or legacy dependency problems | `references/troubleshooting.md` |

## Core Operating Facts

- Inference first preprocesses a face into an aligned/cropped RGBA image, composites the RGB crop on white, resizes to `256x256`, normalizes to `[-1,1]`, runs the generator, and reuses the alpha mask over a white final background.
- The PyTorch inference path constructs `ResnetGenerator(ngf=32, img_size=256, light=True)` and loads checkpoint key `genA2B` from `models/photo2cartoon_weights.pt`.
- The ONNX path feeds input name `input` and requests output name `output` from `models/photo2cartoon_weights.onnx`.
- Training expects `dataset/<dataset>/{trainA,trainB,testA,testB}` with real photos in domain A and cartoon portraits in domain B.
- The training object saves checkpoints with keys `genA2B`, `genB2A`, `disGA`, `disGB`, `disLA`, and `disLB`.
- Full preprocessing and inference require external assets and legacy ML dependencies; safe generated helpers default to validation, recipe generation, or synthetic smoke checks rather than downloads or long training.

## Bundled References and Scripts

- `references/setup-and-assets.md`: dependency snapshots, external assets, and safe environment strategy.
- `references/troubleshooting.md`: cross-cutting failures before routing to a sub-skill.
- `references/repo-routing-metadata.json`: structured router metadata used by DisCo's repo-skill importer.
- `scripts/check_repository_assets.py`: safe source-tree and asset validator.

## Non-goals

This skill does not bundle the model weights, segmentation graph, cartoon dataset, or sample images. It also does not verify visual quality, run the original long training loop, download data from cloud drives, or mutate a user's shared Python environment.
