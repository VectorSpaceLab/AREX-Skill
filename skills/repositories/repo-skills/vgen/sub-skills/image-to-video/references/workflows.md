# I2VGen-XL workflows

This sub-skill covers the VGen I2VGen-XL path only: single-image-plus-caption video generation, the person-specialized config variant, and the local predictor/demo wrappers that mirror the same model family.

## Evidence-backed workflow shape

The observed inference entry point is `tools/inferences/inference_i2vgen_entrance.py`, which is selected by `TASK_TYPE: inference_i2vgen_entrance` in the I2VGen configs. The entry point:

- merges the update config into the base config and then loads `vldm_cfg`
- sets up `MASTER_ADDR`, `MASTER_PORT`, rank, world size, and NCCL distributed inference when more than one GPU is present
- builds the diffusion, CLIP embedder, autoencoder, and UNet modules
- loads `checkpoint['state_dict']` from `test_model` with a strict state-dict load
- reads `test_list_path`, strips each line, skips comment lines beginning with `#`, repeats active samples according to `round`, and splits each active line on exactly one `|||`
- opens each image, converts non-RGB images to RGB, encodes the image and caption, samples a video, and saves an `.mp4` into the experiment log directory

## Default config variant

`configs/i2vgen_xl_infer.yaml` is the main reusable inference configuration.

Observed defaults:

- `TASK_TYPE: inference_i2vgen_entrance`
- `guide_scale: 9.0`
- `chunk_size: 2`
- `decoder_bs: 2`
- `max_frames: 16`
- `target_fps: 16`
- `scale: 8`
- `seed: 8888`
- `round: 4`
- `batch_size: 1`
- `use_zero_infer: True`
- `vldm_cfg: configs/i2vgen_xl_train.yaml`
- `test_list_path: data/test_list_for_i2vgen.txt`
- `test_model: models/i2vgen_xl_00854500.pth`

The README also documents a direct override form for swapping in a different list or checkpoint.

## Person variant

`configs/i2vgen_xl_infer_person.yaml` is a person-specialized variant.

Observed overrides:

- `seed: 0`
- `data_root: workspace/test_imgs/test_img_01`
- `test_list_path: workspace/test_imgs/test_img_02.txt`
- `cap_dict_path: workspace/test_imgs/cap_dict_01.json`
- `test_model: models/i2vgen_xl_person_00854500.pth`

Treat `data_root` and `cap_dict_path` as person-workflow context fields. The shared entrance loop still consumes `test_list_path` lines in the same `image|||caption` format, so the person list should be validated with the same checker as the default list.

## Input list format

`data/test_list_for_i2vgen.txt` documents the expected format for one sample per line.

Rules that follow from the observed inference code:

- Use exactly one `|||` delimiter per active line.
- Keep comment lines commented with `#`; the loader skips them after stripping whitespace.
- Do not rely on blank lines; the source loader does not treat them as ignorable comments.
- Provide both an image path and a caption.
- Leave no empty caption if you want the sample to generate, because the inference loop skips empty captions.
- Prefer paths that resolve from the current working directory of the VGen checkout unless the user has explicitly organized another root.
- The caption should be a plain text description suitable for image-conditioned generation.

Example:

```text
data/test_images/img_0001.jpg|||A green frog floats on the surface of the water on green lotus leaves, with several pink lotus flowers, in a Chinese painting style.
```

## Recommended local flow

1. Validate the input list with the bundled checker.
2. Confirm the checkpoint file exists and matches the selected config.
3. Run the bundled local launcher and point `--repo-root` at the VGen checkout, which forwards to the repository's standard config-driven inference path.
4. Inspect the generated MP4 files in the experiment directory named after the input list stem.

The README states that the result lands under `workspace/experiments/test_list_for_i2vgen` for the default list; the code names the output directory from the list file stem.

Example launch:

```bash
python sub-skills/image-to-video/scripts/run_i2vgen_inference.py --repo-root /path/to/VGen --dry-run --cfg configs/i2vgen_xl_infer.yaml -- \
  test_list_path data/test_list_for_i2vgen.txt \
  test_model models/i2vgen_xl_00854500.pth
```
## Checkpoint expectations

The local inference code expects a checkpoint path that contains a `state_dict` key and a `step` key.

Observed checkpoint choices:

- Standard I2VGen-XL: `models/i2vgen_xl_00854500.pth`
- Person-specialized I2VGen-XL: `models/i2vgen_xl_person_00854500.pth`

The README also documents two ways to fetch the base model family before placing or pointing `test_model` at the local `.pth` file:

- ModelScope snapshot download for `damo/I2VGen-XL` with revision `v1.0.0`
- Hugging Face clone of `damo-vilab/i2vgen-xl` with git-lfs enabled

Use the default checkpoint for standard I2VGen-XL runs and the person checkpoint for the person-specific variant. A mismatch between checkpoint family and config usually shows up as a strict load failure or a visibly degraded sample.

## Optional demo wrappers

### `predict.py`

This is a Cog predictor wrapper.

Observed behavior:

- loads `configs/i2vgen_xl_infer.yaml`
- initializes distributed CUDA inference on `nccl`
- accepts `image`, `prompt`, `max_frames`, `num_inference_steps`, `guidance_scale`, and `seed`
- writes a single output video to `/tmp/out.mp4`

Treat this file as a reference for predictor argument shape and output handling. It is not the preferred core offline path because it depends on Cog-style deployment tooling and a demo-oriented runtime.

### `gradio_app.py`

This is a ModelScope/Gradio demo surface.

Observed behavior:

- installs `modelscope` and `gradio` at runtime
- uses `pipeline(task="image-to-video", model='damo/i2vgen-xl', model_revision='v1.1.3', device='cuda:0')`
- exposes a browser UI that recommends English captions and a 1280x720 image input

Treat it as reference-only unless the user explicitly wants the network-backed demo path.

## Useful tuning notes

- `round` controls repetition of the same input line. Use `round: 1` for smoke testing.
- `max_frames`, `decoder_bs`, and `chunk_size` can be lowered first when memory is tight.
- `use_zero_infer: True` is part of the observed default inference path.
- Keep the caption short and specific if you are testing a single image.
