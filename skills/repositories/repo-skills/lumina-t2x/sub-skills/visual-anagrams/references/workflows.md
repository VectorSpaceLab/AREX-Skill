# Visual Anagrams Workflows

## Purpose

Read this when you need to generate an illusion, save its metadata, or animate an existing result.

## Generation

### Template route

- Edit `run.sh` to point `model_dir` at your checkpoint and then run it.

### Direct route

- `python generate.py --name <illusion_name> --prompts <prompt_1> <prompt_2> ... --views <view_1> <view_2> ... --ckpt <model_dir> --resolution <cat:WxH> --num_samples <n> --num_inference_steps <steps>`

### Important flags

- `--name` controls the result folder under `results/`.
- `--prompts` and `--views` must have the same length.
- `--style` prepends an optional style phrase to every prompt.
- `--view_args` supplies per-view parameters for views that need one.
- `--generate_1024` requests an upsampled output path.
- `--save_metadata` stores a pickle file that can later drive animation.

### Common outputs

- `sample_<size>.png`
- `sample_<size>.views.png`
- `metadata.pkl` when metadata saving is enabled

## Animation

### Template route

- `python animate.py --im_path <illusion.png> [--metadata_path <metadata.pkl> | --view <view_name> --prompt_1 ... --prompt_2 ...]`

### Notes

- When `--metadata_path` is provided, the script reuses the saved prompts and views.
- Without metadata, you must provide the view name and the two prompt strings manually.
- Motion-blur views use a slightly different animation path.
- The animation path imports `imageio` / `imageio-ffmpeg`, so install those extras before trying to write MP4 output.

## Resolution and view logic

- Resolution strings use the `category:WxH` style from the README examples.
- The selected view list must match the prompt count exactly.
- The illusion generator works by repeatedly sampling on the chosen views and combining the inverted noises.
