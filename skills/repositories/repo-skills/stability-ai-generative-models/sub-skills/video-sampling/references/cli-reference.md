# Video Sampling CLI Reference

The standalone samplers use Python Fire, so arguments are passed as `--name value` or `--name=value`. For list values, quote the whole list so the shell does not split it: `--azimuths_deg '[0,18,...,360]'`. Boolean values are safest as `--remove_bg True` or `--verbose True`.

## Safe Help and Inspection

```bash
python scripts/sampling/simple_video_sample.py -- --help
python scripts/sampling/simple_video_sample_4d.py -- --help
python scripts/sampling/simple_video_sample_4d2.py -- --help
python <generative-models-skill>/sub-skills/video-sampling/scripts/inspect_video_sampling_cli.py --script all --json
```

`Fire --help` and the bundled static helper are safe because they do not perform sampling. Full commands below load models and require checkpoints plus a suitable runtime.

## `simple_video_sample.py`

Used for SVD, SVD-XT, SVD image-decoder variants, SV3D_u, and SV3D_p.

| Parameter | Default | Applies to | Meaning |
| --- | --- | --- | --- |
| `input_path` | `assets/test_image.png` | all | Single `.jpg/.jpeg/.png` image or a folder of image files. No glob support in this script. |
| `num_frames` | version-specific | SVD/SVD-XT | Defaults to 14 for `svd`/`svd_image_decoder`, 25 for `svd_xt`/`svd_xt_image_decoder`, and forced to 21 for SV3D. |
| `num_steps` | version-specific | all | Defaults to 25 for SVD, 30 for SVD-XT, and 50 for SV3D. |
| `version` | `svd` | all | One of `svd`, `svd_xt`, `svd_image_decoder`, `svd_xt_image_decoder`, `sv3d_u`, `sv3d_p`. |
| `fps_id` | `6` | all | Conditioning fps id; values below 5 or above 30 trigger quality warnings. |
| `motion_bucket_id` | `127` | all | Motion conditioning bucket; values above 255 trigger a quality warning. |
| `cond_aug` | `0.02` | SVD/SVD-XT | Conditioning noise augmentation; SV3D variants override it to `1e-5`. |
| `seed` | `23` | all | Torch random seed. |
| `decoding_t` | `14` | all | Frames decoded at a time; reduce for low VRAM. |
| `device` | `cuda` | all | Device for model execution; real sampling expects CUDA in practice. |
| `output_folder` | version-specific | all | Destination folder for paired input `.jpg` and generated `.mp4` files. |
| `elevations_deg` | `10.0` | SV3D_p | Scalar or 21 elevations in degrees. |
| `azimuths_deg` | `None` | SV3D_p | Optional 21 azimuths in degrees; omitted value produces an even orbit. |
| `image_frame_ratio` | `None` | SV3D | Object-size ratio during alpha crop/pad before resizing to `576x576`. |
| `verbose` | `False` | all | Passes verbosity to sampler/model loading. |

Version-derived defaults:

| `version` | Frames | Steps | Config | Checkpoint | Default output folder |
| --- | ---: | ---: | --- | --- | --- |
| `svd` | 14 | 25 | `svd.yaml` | `checkpoints/svd.safetensors` | `outputs/simple_video_sample/svd/` |
| `svd_xt` | 25 | 30 | `svd_xt.yaml` | `checkpoints/svd_xt.safetensors` | `outputs/simple_video_sample/svd_xt/` |
| `svd_image_decoder` | 14 | 25 | `svd_image_decoder.yaml` | `checkpoints/svd_image_decoder.safetensors` | `outputs/simple_video_sample/svd_image_decoder/` |
| `svd_xt_image_decoder` | 25 | 30 | `svd_xt_image_decoder.yaml` | `checkpoints/svd_xt_image_decoder.safetensors` | `outputs/simple_video_sample/svd_xt_image_decoder/` |
| `sv3d_u` | 21 | 50 | `sv3d_u.yaml` | `checkpoints/sv3d_u.safetensors` | `outputs/simple_video_sample/sv3d_u/` |
| `sv3d_p` | 21 | 50 | `sv3d_p.yaml` | `checkpoints/sv3d_p.safetensors` | `outputs/simple_video_sample/sv3d_p/` |

Safe command templates:

```bash
python scripts/sampling/simple_video_sample.py --input_path inputs/object.png --version svd --decoding_t 8
python scripts/sampling/simple_video_sample.py --input_path inputs/object.png --version svd_xt --num_steps 20 --decoding_t 4
python scripts/sampling/simple_video_sample.py --input_path inputs/object.png --version sv3d_u --decoding_t 4
python scripts/sampling/simple_video_sample.py --input_path inputs/object.png --version sv3d_p --elevations_deg 15.0 --decoding_t 4
```

## `simple_video_sample_4d.py`

Used for original SV4D video-to-4D sampling with SV3D-generated first-frame reference views.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `input_path` | `assets/sv4d_videos/test_video1.mp4` | `.gif`, `.mp4`, folder of `.jpg/.jpeg/.png`, or image glob pattern. |
| `output_folder` | `outputs/sv4d` | Folder for processed input, first-time reference video, per-view videos, and diagonal video. |
| `num_steps` | `20` | SV4D denoising steps; README suggests up to 50 for quality. |
| `sv3d_version` | `sv3d_u` | `sv3d_u` or `sv3d_p` for first-frame reference views. |
| `img_size` | `576` | Square preprocessing/output resolution. Lower for low VRAM. |
| `fps_id` | `6` | Passed to SV3D reference generation. |
| `motion_bucket_id` | `127` | Passed to SV3D reference generation. |
| `cond_aug` | `1e-5` | Passed to SV3D reference generation. |
| `seed` | `23` | Torch random seed. |
| `encoding_t` | `8` | Frames encoded at a time; reduce for low VRAM. |
| `decoding_t` | `4` | Frames decoded at a time; reduce for low VRAM. |
| `device` | `cuda` | Device for model execution. |
| `elevations_deg` | `10.0` | Scalar or 21 elevations for the SV3D reference orbit. |
| `azimuths_deg` | `None` | Optional 21 azimuths for the SV3D reference orbit. |
| `image_frame_ratio` | `0.917` | Object-size ratio used while preprocessing frames. |
| `verbose` | `False` | Sampler/model verbosity. |
| `remove_bg` | `False` | Use `rembg` to produce alpha masks before cropping/compositing. |

Safe command templates:

```bash
python scripts/sampling/simple_video_sample_4d.py --input_path inputs/object.mp4 --output_folder outputs/sv4d
python scripts/sampling/simple_video_sample_4d.py --input_path 'frames/*.png' --remove_bg True --encoding_t 1 --decoding_t 1 --img_size 512
python scripts/sampling/simple_video_sample_4d.py --input_path inputs/object.mp4 --sv3d_version sv3d_p --elevations_deg 30.0
```

## `simple_video_sample_4d2.py`

Used for SV4D 2.0 and SV4D2 8-view video-to-4D sampling.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `input_path` | `assets/sv4d_videos/camel.gif` | `.gif`, `.mp4`, folder of `.jpg/.jpeg/.png`, or image glob pattern. |
| `model_path` | `checkpoints/sv4d2.safetensors` | Must have basename `sv4d2.safetensors` or `sv4d2_8views.safetensors`. |
| `output_folder` | `outputs` | Parent output folder; script appends `sv4d2` or `sv4d2_8views`. |
| `num_steps` | `50` | Denoising steps. Reduce to shorten runtime. |
| `img_size` | `576` | Square preprocessing/output resolution. Lower for low VRAM. |
| `n_frames` | `21` | Number of input/output video frames read by the script. |
| `seed` | `23` | Torch random seed. |
| `encoding_t` | `8` | Frames encoded at a time; reduce for low VRAM. |
| `decoding_t` | `4` | Frames decoded at a time; reduce for low VRAM. |
| `device` | `cuda` | Device for model execution. |
| `elevations_deg` | `0.0` | Scalar or one value per total view: 5 for 4-view mode, 9 for 8-view mode. |
| `azimuths_deg` | `None` | Optional list of 5 or 9 total-view azimuths, depending on model basename. |
| `image_frame_ratio` | `0.9` | Object-size ratio used while preprocessing frames. |
| `verbose` | `False` | Sampler/model verbosity. |
| `remove_bg` | `False` | Use `rembg` to produce alpha masks before cropping/compositing. |

Model-path-derived behavior:

| Basename | Config | Chunk shape | Generated views | Default azimuths | Output subfolder |
| --- | --- | --- | ---: | --- | --- |
| `sv4d2.safetensors` | `sv4d2.yaml` | 12 frames x 4 views | 4 | `[0, 60, 120, 180, 240]` | `sv4d2/` |
| `sv4d2_8views.safetensors` | `sv4d2_8views.yaml` | 5 frames x 8 views | 8 | `[0, 30, 75, 120, 165, 210, 255, 300, 330]` | `sv4d2_8views/` |

Safe command templates:

```bash
python scripts/sampling/simple_video_sample_4d2.py --input_path inputs/object.gif --model_path checkpoints/sv4d2.safetensors --output_folder outputs
python scripts/sampling/simple_video_sample_4d2.py --input_path inputs/object.gif --model_path checkpoints/sv4d2_8views.safetensors --output_folder outputs --encoding_t 1 --decoding_t 1
python scripts/sampling/simple_video_sample_4d2.py --input_path 'frames/*.png' --remove_bg True --img_size 512 --n_frames 21
```

## Output Conventions

- `simple_video_sample.py` writes one copied/processed input image as `000000.jpg` and one generated video as `000000.mp4`, incrementing by existing `.mp4` count.
- `simple_video_sample_4d.py` writes a processed input video, a first-frame reference video, `v001` through `v008` novel-view videos, and a diagonal video.
- `simple_video_sample_4d2.py` writes outputs under `<output_folder>/sv4d2/` or `<output_folder>/sv4d2_8views/` and emits one `.mp4` per generated view.
