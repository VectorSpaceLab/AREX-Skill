# Generation Workflows

## Top-level StyleGAN generation

Use `gen-images` in the bundled builder:

```bash
python sub-skills/stylegan-generation/scripts/build_generation_command.py \
  --repo-root /path/to/DragGAN gen-images \
  --network checkpoints/stylegan2-ffhq-512x512.pkl \
  --seeds 0,1,4-6 --trunc 0.7 --noise-mode const \
  --outdir outputs/ffhq
```

The underlying workflow accepts `--network`, `--seeds`, `--trunc`, `--class`, `--noise-mode {const,random,none}`, `--translate a,b`, `--rotate angle`, and `--outdir`. Seeds are written as `seed####.png`. Conditional networks require `--class`; unconditional networks warn if it is supplied.

The implementation selects CUDA, MPS, or CPU. MPS uses float32; the CUDA/CPU path may use float64 in the repo’s generator code. CPU is useful for small smoke cases but can be very slow for high-resolution models.

## StyleGAN-Human generation

```bash
python sub-skills/stylegan-generation/scripts/build_generation_command.py \
  --repo-root /path/to/DragGAN stylegan-human-generate \
  --network pretrained_models/stylegan_human_v2_1024.pkl \
  --seeds 0-10 --trunc 0.8 --outdir outputs/generate --version 2
```

Version 2/3 use PyTorch network pickles. Version 1 uses a TensorFlow 1.x code path and is an optional compatibility route, not a default environment target.

## Interpolation

```bash
python sub-skills/stylegan-generation/scripts/build_generation_command.py \
  --repo-root /path/to/DragGAN interpolation \
  --network pretrained_models/stylegan_human_v2_1024.pkl \
  --seeds 85,100 --outdir outputs/inter_gifs \
  --num-interps 100 --fps 15
```

The workflow saves endpoint images and a latent-space traversal GIF. Use two seeds; the source script truncates extra seeds and generates a random partner when given only one.

## Style-mixing image grid

```bash
python sub-skills/stylegan-generation/scripts/build_generation_command.py \
  --repo-root /path/to/DragGAN style-mixing \
  --network pretrained_models/stylegan_human_v2_1024.pkl \
  --rows 85,100,75 --cols 55,821 --styles 0-3 \
  --outdir outputs/stylemixing
```

`--styles` selects the destination style layers copied into each row latent. The output is a grid image; keep the style range within the model’s `num_ws` range.

## Style-mixing video

Use the `stylemixing-video` builder only after checking TensorFlow/import compatibility:

```bash
python sub-skills/stylegan-generation/scripts/build_generation_command.py \
  --repo-root /path/to/DragGAN stylemixing-video \
  --network pretrained_models/stylegan_human_v2_1024.pkl \
  --row-seed 3859 --col-seeds 3098,31759,3791 \
  --col-styles 8-12 --duration-sec 10 --fps 10 \
  --outdir outputs/stylemixing_video
```

The source script imports `dnnlib.tflib` before parsing options even though the main video path uses PyTorch. Missing TensorFlow therefore blocks help/import on an unmodified checkout. Video generation also needs `ffmpeg` and substantial compute/disk.
