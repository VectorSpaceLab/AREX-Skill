---
name: inference-and-sampling
description: "Routes pretrained super-resolution inference and unconditional
  sampling workflows for this SR3/DDPM iterative-refinement repo skill."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Sampling

Use this sub-skill when the task is to assemble or review commands for:

- pretrained super-resolution inference with `infer.py` on prepared low/high-resolution validation images;
- unconditional image generation or unconditional training/evaluation with `sample.py`;
- W&B flag selection for those two scripts.

Do not use this sub-skill for `sr.py` super-resolution training, standalone PSNR/SSIM evaluation, dataset conversion, or checkpoint download instructions beyond prerequisite notes.

## Read first

- [references/workflows.md](references/workflows.md) for workflow prerequisites, config fields, outputs, and safe command construction.
- [references/troubleshooting.md](references/troubleshooting.md) for checkpoint, data, CUDA, JSON-comment, W&B, and output-location failures.
- [scripts/build_inference_command.py](scripts/build_inference_command.py) to parse a comment-bearing SR config and print an `infer.py` command without running inference.
- [scripts/build_sample_command.py](scripts/build_sample_command.py) to parse a comment-bearing sample config and print a `sample.py` command without running training or generation.

## Routing checklist

1. Classify the user request:
   - `infer.py`: conditional super-resolution from a validation dataset using a pretrained checkpoint stem in `path.resume_state`.
   - `sample.py -p val`: unconditional generation from a pretrained checkpoint; `datasets.val.data_len` controls how many samples are produced.
   - `sample.py -p train`: unconditional training or resume training; this is not SR training and still needs the repo's training data layout.
2. Confirm the config matches the workflow before suggesting a run:
   - super-resolution inference should use a conditional config such as `config/sr_sr3_64_512.json`;
   - unconditional sampling should use a non-conditional config such as `config/sample_sr3_128.json` or `config/sample_ddpm_128.json`;
   - pretrained inference/generation should have `path.resume_state` set to the checkpoint prefix, not the `_gen.pth` file name.
3. Prefer the bundled builders for command assembly. They validate JSON-with-`//` comments and can enforce checkpoint-file checks when `--require-resume-state` is passed.
4. Surface external prerequisites explicitly before a future Researcher runs anything: CUDA-capable runtime expected by the stock configs, matching data layout for `infer.py`, pretrained checkpoint files, and the long reverse-diffusion cost of 2000-step configs.
