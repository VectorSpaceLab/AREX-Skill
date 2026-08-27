# Video task lifecycle

## Purpose

Read this when you need the end-to-end video workflow from the initial task object to the final output file.

## Verified APIs

- `VideoUpscaleTask(video_path, selected_output_path, selected_AI_model, selected_AI_multithreading, selected_gpu, tiles_resolution, input_resize_factor, output_resize_factor, selected_blending_factor, selected_video_extension, selected_video_codec)`
- `upscale_video(process_status_q, video_frames_and_info_q, event_stop_upscale_process, video_path, file_number, selected_output_path, selected_AI_model, selected_blending_factor, selected_AI_multithreading, selected_gpu, input_resize_factor, output_resize_factor, tiles_resolution, selected_video_extension, selected_video_codec, selected_keep_frames)`
- `upscale_video_frames_async(video_frames_and_info_q, event_stop_upscale_process, video_upscale_task, frame_chunk)`

## Lifecycle

1. Build a `VideoUpscaleTask` from the selected file and settings.
2. Decide the target directory and output filename.
3. Check whether the target directory already contains upscaled frames.
4. Either resume from existing frames or extract frames with `ffmpeg.exe`.
5. Complete the task initialization with frame counts and resolutions.
6. Fan out frame upscaling across a multiprocessing pool.
7. Save upscaled frames through a coordination queue and a saver thread.
8. Encode the output video and copy metadata.
9. Remove the frame directory if keep-frames is disabled.

## Frame extraction details

- The app extracts frames into a `frame_###.jpg` directory.
- A progress monitor thread updates the UI while extraction is running.
- `ffmpeg.exe` is required for the extraction step.

## Reuse with the image pipeline

Each extracted frame is upscaled with the same AI image core used for still images. This means provider readiness and model-file readiness are shared concerns across both sub-skills.
