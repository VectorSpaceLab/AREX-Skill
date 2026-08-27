# Video Sampling Workflows

Full sampling loads diffusion checkpoints and is normally CUDA/GPU-bound. Use the command templates here only after the environment is installed, licenses are accepted, and required `.safetensors` files are present under `checkpoints/`. For safe planning without imports, run the bundled static helper.

## Safe Static Inspection

```bash
python <generative-models-skill>/sub-skills/video-sampling/scripts/inspect_video_sampling_cli.py --script all
python <generative-models-skill>/sub-skills/video-sampling/scripts/inspect_video_sampling_cli.py --script sv4d2 --json
```

The helper is metadata-only: it does not import `torch`, `sgm`, `rembg`, `cv2`, or source repo modules, and it never opens checkpoints.

## SVD and SVD-XT Image-to-Video

Use `simple_video_sample.py` when the input is a single `.jpg`, `.jpeg`, or `.png` image, or a folder of images to process independently.

```bash
python scripts/sampling/simple_video_sample.py \
  --input_path inputs/object.png \
  --version svd \
  --output_folder outputs/simple_video_sample/svd
```

```bash
python scripts/sampling/simple_video_sample.py \
  --input_path inputs/object.png \
  --version svd_xt \
  --num_steps 30 \
  --decoding_t 8 \
  --output_folder outputs/simple_video_sample/svd_xt
```

- `svd` defaults to 14 frames, 25 denoising steps, checkpoint `checkpoints/svd.safetensors`, config `svd.yaml`, and output folder `outputs/simple_video_sample/svd/`.
- `svd_xt` defaults to 25 frames, 30 denoising steps, checkpoint `checkpoints/svd_xt.safetensors`, config `svd_xt.yaml`, and output folder `outputs/simple_video_sample/svd_xt/`.
- `svd_image_decoder` and `svd_xt_image_decoder` use the same CLI with image-decoder checkpoints/configs.
- Keep conditioning frames near `576x1024` for best SVD/SVD-XT quality. Non-multiple-of-64 dimensions trigger resizing; non-`576x1024` dimensions trigger a quality warning.
- Reduce `--decoding_t` first when the VAE decode step runs out of memory.

## SV3D_u and SV3D_p Image-to-Multi-View Video

Use `simple_video_sample.py --version sv3d_u` for a default object orbit from one image. Use `sv3d_p` when the camera path must be controlled.

```bash
python scripts/sampling/simple_video_sample.py \
  --input_path inputs/object.png \
  --version sv3d_u \
  --output_folder outputs/simple_video_sample/sv3d_u
```

```bash
python scripts/sampling/simple_video_sample.py \
  --input_path inputs/object.png \
  --version sv3d_p \
  --elevations_deg 10.0 \
  --output_folder outputs/simple_video_sample/sv3d_p
```

```bash
python scripts/sampling/simple_video_sample.py \
  --input_path inputs/object.png \
  --version sv3d_p \
  --elevations_deg '[0,2,4,6,8,10,8,6,4,2,0,-2,-4,-6,-8,-10,-8,-6,-4,-2,0]' \
  --azimuths_deg '[0,18,36,54,72,90,108,126,144,162,180,198,216,234,252,270,288,306,324,342,360]'
```

- Both SV3D variants force `num_frames=21`, default `num_steps=50`, default `cond_aug=1e-5`, and expect `576x576` object images.
- SV3D_u uses checkpoint `checkpoints/sv3d_u.safetensors` and config `sv3d_u.yaml`.
- SV3D_p uses checkpoint `checkpoints/sv3d_p.safetensors` and config `sv3d_p.yaml`.
- `elevations_deg` may be one scalar or exactly 21 values. `azimuths_deg` is auto-generated when omitted, otherwise it must contain exactly 21 values sorted around the orbit.
- For non-RGBA inputs, the script applies `rembg.remove(..., alpha_matting=True)`, crops to the alpha bounding box, composites onto white, and resizes to `576x576`. Use `image_frame_ratio` to control object scale inside the square frame.
- Reduce `--decoding_t` if SV3D VAE decoding exceeds VRAM.

## SV4D Video-to-4D

Use `simple_video_sample_4d.py` for the original SV4D workflow. It preprocesses a 21-frame video, runs SV3D on the first frame to create reference views, then samples 8 novel-view videos over 21 frames.

```bash
python scripts/sampling/simple_video_sample_4d.py \
  --input_path inputs/object.mp4 \
  --output_folder outputs/sv4d \
  --num_steps 20 \
  --encoding_t 8 \
  --decoding_t 4
```

```bash
python scripts/sampling/simple_video_sample_4d.py \
  --input_path 'frames/*.png' \
  --sv3d_version sv3d_p \
  --elevations_deg 30.0 \
  --remove_bg True \
  --encoding_t 1 \
  --decoding_t 1 \
  --img_size 512
```

- Required checkpoints: `checkpoints/sv4d.safetensors` plus SV3D checkpoint(s), usually `checkpoints/sv3d_u.safetensors`; use `sv3d_p.safetensors` when `--sv3d_version sv3d_p`.
- Inputs may be `.gif`, `.mp4`, a folder of `.jpg/.jpeg/.png`, or a glob pattern. SV4D preprocessing requires exactly 21 frames after reading/slicing.
- Output includes `000000_t000.mp4`, `000000_v001.mp4` through `000000_v008.mp4`, and `000000_diag.mp4` in the output folder.
- Lower `encoding_t` reduces memory used by video encoders; lower `decoding_t` reduces memory used by VAE decode. Lower `img_size` reduces memory and compute but changes resolution from the trained `576x576` target.
- SV4D depends on SV3D reference generation; failures before SV4D model loading are often SV3D checkpoint, camera, preprocessing, or first-frame background issues.

## SV4D2 Video-to-4D

Use `simple_video_sample_4d2.py` for SV4D 2.0. It selects 4-view or 8-view behavior from the `model_path` basename.

```bash
python scripts/sampling/simple_video_sample_4d2.py \
  --input_path inputs/object.gif \
  --model_path checkpoints/sv4d2.safetensors \
  --output_folder outputs \
  --num_steps 50
```

```bash
python scripts/sampling/simple_video_sample_4d2.py \
  --input_path 'frames/*.png' \
  --model_path checkpoints/sv4d2.safetensors \
  --remove_bg True \
  --encoding_t 1 \
  --decoding_t 1 \
  --img_size 512
```

- `sv4d2.safetensors` selects config `sv4d2.yaml`, chunks of 12 frames x 4 novel views, and output folder `outputs/sv4d2/` when `--output_folder outputs` is used.
- Default script input length is `n_frames=21`, even though the model was trained on 12-frame chunks. The script autoregressively generates longer sequences.
- Default azimuths are `[0, 60, 120, 180, 240]` for the input view plus 4 generated views; `elevations_deg` may be scalar or 5 values.
- Unlike SV4D, SV4D2 does not run SV3D reference-view generation.

## SV4D2 8-View Mode

Use SV4D2 8-view mode when the requested output is 8 generated views per temporal chunk.

```bash
python scripts/sampling/simple_video_sample_4d2.py \
  --input_path inputs/object.gif \
  --model_path checkpoints/sv4d2_8views.safetensors \
  --output_folder outputs \
  --encoding_t 1 \
  --decoding_t 1
```

- `sv4d2_8views.safetensors` selects config `sv4d2_8views.yaml`, chunks of 5 frames x 8 novel views, and output folder `outputs/sv4d2_8views/` when `--output_folder outputs` is used.
- The script still defaults to `n_frames=21` and autoregressively applies the 5-frame chunk model.
- Default azimuths are `[0, 30, 75, 120, 165, 210, 255, 300, 330]` for the input view plus 8 generated views; `elevations_deg` may be scalar or 9 values.
- The `model_path` basename must be exactly `sv4d2.safetensors` or `sv4d2_8views.safetensors`; renamed files fail the assertion even if the contents are correct.

## Low-VRAM Playbook

- First reduce `--decoding_t`: SVD/SV3D default is 14; SV4D/SV4D2 default is 4.
- For SV4D/SV4D2, also reduce `--encoding_t` from 8 to 1.
- Reduce `--img_size` from 576 to 512 only for SV4D/SV4D2 if memory is still insufficient.
- Reduce `--num_steps` to shorten runtime; this usually affects quality more than memory.
- Keep `device=cuda` for real sampling unless a CPU-only debug run is explicitly acceptable; CPU full sampling is impractically slow and may still fail on missing GPU-specific assumptions.
