# Environment and Input Troubleshooting

## Alpha validator says there is no alpha channel

Make-It-3D expects a transparent-background object. Convert the input to RGBA with a segmentation/background-removal tool and save as PNG. Do not proceed with ordinary RGB unless the user agrees to patch source code that assumes BGRA/RGBA.

## Foreground coverage is near zero or near one

Likely causes:

- Fully transparent or fully opaque alpha channel.
- Mask exported with wrong object/background polarity.
- Large background retained as foreground.

Recovery: inspect the alpha mask, crop/center the object, and regenerate a transparent background. Re-run the validator and confirm foreground coverage is plausible.

## DPT weights missing

Symptoms: file-not-found errors around `dpt_hybrid-midas-501f0c75.pt` or depth model load. Place the DPT hybrid weights under `dpt_weights/` relative to the runtime working directory used for `python main.py`.

## Help command fails before showing flags

This can happen because `main.py` imports heavy modules before `argparse` runs. Install import-time dependencies such as PyTorch3D, OpenAI CLIP, contextual loss, Open3D, PyMCubes, and DPT/timm before expecting `main.py --help` to work.

## No `nvcc` but GPUs are visible

A CUDA driver can run prebuilt CUDA wheels, but source extensions such as `raymarching` often need the CUDA toolkit compiler. Install a matching toolkit or use an environment image that already includes it. Do not treat visible A100/RTX GPUs alone as proof the extension can build.

## Hugging Face authentication or cache errors

Stable Diffusion and BLIP2 can require model access. Use `huggingface-cli login` or a token in the user's environment. Never echo tokens in a command transcript. Provide `--text` to skip BLIP2 if the user can write the prompt manually.
