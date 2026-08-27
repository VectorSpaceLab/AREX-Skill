# API reference

## Purpose

Read this when you need the exact MimicMotion call signatures, input shapes, or output behavior without reopening the source checkout.

## Main runtime surfaces

| API | Verified signature | Notes |
| --- | --- | --- |
| `inference.preprocess` | `(video_path, image_path, resolution=576, sample_stride=2)` | Loads the reference image and motion video, computes DWPose overlays, prepends the reference image pose, and returns normalized pose/image tensors in `[-1, 1]`. |
| `inference.run_pipeline` | `(pipeline, image_pixels, pose_pixels, device, task_config)` | Converts the preprocessed image tensor back to PIL images, seeds a `torch.Generator`, calls the pipeline, and returns the generated frames tensor with the reference frame removed. |
| `inference.main` | `(args)` | Reads `args.inference_config`, builds the pipeline, iterates `infer_config.test_case`, and writes one MP4 per case. |
| `mimicmotion.utils.loader.create_pipeline` | `(infer_config, device)` | Builds the Stable Video Diffusion components, loads the MimicMotion checkpoint with `torch.load(..., weights_only=True)`, and returns a `MimicMotionPipeline`. |
| `mimicmotion.utils.utils.save_to_mp4` | `(frames, save_path, fps=7)` | Permutes frame layout to `(frames, height, width, channels)` and writes video output with `torchvision.io.write_video`. |
| `mimicmotion.dwpose.preprocess.get_video_pose` | `(video_path: str, ref_image: numpy.ndarray, sample_stride: int = 1)` | Uses DWPose to detect body/hand/face keypoints, rescales poses to the reference image, and returns a stack of pose images. |
| `mimicmotion.dwpose.preprocess.get_image_pose` | `(ref_image)` | Produces the reference-image pose rendering used as the first pose frame. |
| `mimicmotion.dwpose.dwpose_detector.DWposeDetector.__call__` | `(self, oriImg)` | Returns a pose dictionary with `bodies`, `hands`, and `faces` entries. |
| `mimicmotion.pipelines.pipeline_mimicmotion.MimicMotionPipeline.__call__` | `(self, image, image_pose, height=576, width=1024, num_frames=None, tile_size=16, tile_overlap=4, num_inference_steps=25, min_guidance_scale=1.0, max_guidance_scale=3.0, fps=7, motion_bucket_id=127, noise_aug_strength=0.02, image_only_indicator=False, decode_chunk_size=None, num_videos_per_prompt=1, generator=None, latents=None, output_type='pil', callback_on_step_end=None, callback_on_step_end_tensor_inputs=['latents'], return_dict=True, device=None)` | The core generation path. It expects CUDA-capable execution and uses the pose network, 3D U-Net, and VAE decoder. |
| `mimicmotion.modules.pose_net.PoseNet.forward` | `(self, x)` | Accepts a 4D or 5D pose tensor and returns latent pose features. |
| `mimicmotion.modules.unet.UNetSpatioTemporalConditionModel.forward` | `(self, sample, timestep, encoder_hidden_states, added_time_ids, pose_latents=None, image_only_indicator=False, return_dict=True)` | The conditioned spatio-temporal denoiser used by the pipeline. |
| `predict.Predictor.predict` | `(self, motion_video, appearance_image, resolution=576, chunk_size=16, frames_overlap=6, denoising_steps=25, noise_strength=0.0, guidance_scale=2.0, sample_stride=2, output_frames_per_second=15, seed=None, checkpoint_version='v1-1')` | Cog-facing prediction surface with validation and checkpoint switching. Returns a temporary MP4 path. |

## Notes worth remembering

- `Predictor.setup` downloads weights into `models/` and switches the checkpoint path between `models/MimicMotion.pth` and `models/MimicMotion_1-1.pth`.
- `predict.py` validates several user-facing bounds before generation:
  - `resolution` must be between 64 and 1024 and divisible by 8.
  - `chunk_size` must be at least 2 and greater than `frames_overlap`.
  - `denoising_steps` must be between 1 and 100.
  - `noise_strength` must be between 0.0 and 1.0.
  - `guidance_scale` must be between 0.1 and 10.0.
  - `sample_stride` must be at least 1.
  - `output_frames_per_second` must be between 1 and 60.
- The local inference path operates on a config file. The sample config uses one test case and the `v1-1` checkpoint by default.
- `MimicMotionPipeline` and `Predictor.run_pipeline` both rely on CUDA; the CPU fallback branch in the source CLI is not treated as a supported runtime path in this skill.
- `DWposeDetector` can use either `CPUExecutionProvider` or `CUDAExecutionProvider`, but the overall generation workflow still requires CUDA for the torch pipeline.
