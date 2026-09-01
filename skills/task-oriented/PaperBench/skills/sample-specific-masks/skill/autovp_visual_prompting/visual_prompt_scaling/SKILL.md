---
name: visual_prompt_scaling
description: Build AutoVP frame-shaped visual prompt masks and apply bounded universal prompts to resized images.
---
# Visual Prompt Scaling
Use this skill when implementing AutoVP-style input scaling and frame prompts. Do not use it for patch-token prompt tuning or model-internal prompts.

## Inputs
Source image size, target image size, channel count, image array, and prompt parameters.

## Outputs
Prompt width `p`, binary frame mask, centered image canvas, and prompted image.

## Workflow
Compute `p=(source_size-target_size)//2`; build a frame mask; center the image; apply a sigmoid-bounded prompt only where mask is one. Reject target sizes larger than the source input. Record odd padding decisions.

## Validation
Run `python tests/test_visual_prompt_scaling.py` or the Distiller skill-tree validator with tests.
