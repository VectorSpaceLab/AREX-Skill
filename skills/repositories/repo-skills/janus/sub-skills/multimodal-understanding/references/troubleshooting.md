# Multimodal Understanding Troubleshooting

## Purpose

Use this when the understanding workflow fails after the package imports.

## `load_pil_images` returns the wrong number of images

**Symptoms**

- `prepare_inputs` has more or fewer image tokens than expected.
- The processor asserts or the decoded answer looks unrelated.

**Likely causes**

- The prompt contains the wrong number of `<image_placeholder>` strings.
- The conversation has images in the wrong message.
- The image list contains non-RGB or unreadable files.

**Recovery**

1. Count placeholders first.
2. Load images with the bundled helper.
3. Confirm each image is RGB and openable.
4. Re-run the dry-run helper before any model download.

## `prompt and conversations cannot be used at the same time`

**Likely cause**: both inputs were passed to `VLChatProcessor.process_one` or the wrapper script.

**Recovery**: choose one input style and keep the wrapper call narrow.

## The decoded answer echoes the prompt

**Likely causes**

- Wrong role tokens for the model family.
- Incorrect `sft_format` or template.
- A checkpoint/template mismatch.

**Recovery**

1. Print the formatted prompt.
2. Verify the family-specific role tokens.
3. Check that the assistant turn is empty when generation starts.

## `torch.cuda.is_available() == False`

**Likely cause**: the model snippets assume CUDA.

**Recovery**

1. Use the dry-run path if you only need prompt validation.
2. If you need a real answer, switch to a CUDA-capable environment.
3. Do not treat a CPU import as proof that the README's `.cuda()` workflow will work.

## `ModuleNotFoundError: No module named 'torchvision'`

**Likely cause**: the source image processor uses torchvision resize utilities, but the package metadata does not declare torchvision.

**Recovery**

1. Install a torchvision build that matches the selected torch wheel.
2. Re-run the environment check script.
3. Retry the understanding workflow.

## Model download or `trust_remote_code` problems

**Symptoms**

- Download stalls.
- Hugging Face access errors.
- Remote-code import warnings.

**Recovery**

1. Confirm the model id is the right family.
2. Ensure the machine can reach the model host and cache location.
3. If using a restricted environment, stick to dry-run validation until access is available.

## Bad output after a successful run

If the model runs but the answer is still wrong:

1. Inspect the image size and resize behavior.
2. Confirm the prompt has only one image placeholder per image.
3. Check whether the model family expects `User` or `<|User|>` role tokens.
4. Compare the raw decoded answer before changing generation settings.
