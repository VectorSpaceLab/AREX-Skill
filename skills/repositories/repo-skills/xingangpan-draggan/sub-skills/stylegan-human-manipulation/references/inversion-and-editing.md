# Inversion and Editing Workflows

## PTI configuration

The PTI entry point is configuration-driven rather than a full command-line interface. Review the path/global config before execution:

- Input images: an aligned-image directory, typically resized/normalized to the StyleGAN-Human 1024x512 convention.
- `e4e`: e4e-w+ encoder weights when using the encoder initialization path.
- `stylegan2_ada_shhq`: the StyleGAN-Human generator checkpoint.
- Checkpoint, embedding, and experiment output directories.
- CUDA device selection and run name.

The source workflow creates embeddings and fine-tuned generator checkpoints under the PTI output tree. PTI is long-running and mutates output directories; preflight assets and make a new run name before launching.

## Attribute editing

The supported documented attributes are `upper_length` and `bottom_length`. The edit configuration stores different directions/strengths for InterfaceGAN, StyleSpace, and SeFa. Editing generated images uses random seeds; editing a real image uses a PTI latent path and an aligned source image.

Before editing, verify:

- The checkpoint is a compatible StyleGAN-Human model.
- Latent-direction files and StyleSpace statistics are present under the expected asset directories.
- The requested attribute is one of the supported names.
- CUDA is available and the custom CUDA ops can compile/load if the source environment requires them.
- `gen_video` and FFmpeg settings match available disk space.

The output combines raw/generated and edited variants and may write video frames. Keep each attribute/seed/run in a separate output directory.

## InsetGAN

InsetGAN jointly optimizes a face generator and a full-body generator. It needs:

- A body StyleGAN-Human checkpoint.
- An FFHQ face checkpoint.
- dlib 68-landmark and CNN face-detector model files.
- LPIPS and CUDA.
- Enough VRAM/time for multiple optimization stages.

The operation converts pickles to the expected generator state format when needed and writes intermediate frames when video output is enabled. Treat it as an optional, expensive demonstration rather than a smoke test.

## Output handoff

For a real-image editing result, preserve the chain of artifacts: aligned input, PTI embedding, fine-tuned checkpoint, attribute name/strength, and final output. Do not report an edit as reproducible if any of those inputs are missing.
