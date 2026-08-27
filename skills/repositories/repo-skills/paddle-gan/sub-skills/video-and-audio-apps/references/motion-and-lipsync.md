# Motion driving and lip-sync

## First Order Motion

`FirstOrderPredictor` animates a source image with a driving video.

### Key inputs and knobs
- source image + driving video
- `relative` and `adapt_scale` for keypoint motion handling
- `find_best_frame` or `best_frame` for face-aligned starts
- `ratio` for multi-face paste size
- `face_detector` for detector choice
- `multi_person` for source images with multiple faces
- `image_size` for face crop size; common values are 256 and 512
- `face_enhancement` for optional post-processing
- `batch_size` for peak memory control
- `mobile_net` for the smaller compressed model path
- `slice_size` for chunking long driving videos under tight memory budgets

### Detector and recovery notes
- Supported detector backends are `sfd` and `blazeface`.
- `find_best_frame` needs face-alignment support and is best treated as optional.
- `slice_size` is the safest fallback when the driving video is too large to process in one pass.
- If multiple faces are close together, keep `ratio` modest so the pasted face does not bleed into neighbors.
- `mobile_net` reduces model size when the default model is too heavy.

### Output
- The predictor writes an animated result video, normally `output/result.mp4` unless a different filename is chosen.

## Wav2Lip

`Wav2LipPredictor` synchronizes mouth motion in a face image or face video to a target audio clip.

### Key inputs and knobs
- face image or face video
- audio file supported by ffmpeg, commonly `.wav`, `.mp3`, or `.m4a`
- `checkpoint_path` for explicit weights
- `static` for still-image mode
- `fps` for static-image inputs
- `pads` in top, bottom, left, right order
- `face_det_batch_size` for face detection memory
- `wav2lip_batch_size` for model batch size
- `resize_factor` to shrink large clips before detection
- `crop` to pre-crop the video area
- `box` as a last-resort constant face box
- `rotate` for rotated phone videos
- `nosmooth` to disable temporal smoothing of detections
- `face_detector` for detector choice
- `face_enhancement` for optional post-processing

### Recovery notes
- `Face not detected!` usually means the detector needs help. Try `resize_factor`, `crop`, `box`, or `rotate`, and switch detectors if needed.
- `Mel contains nan!` usually means the audio stream is malformed, silent, or TTS-like. Re-encode the audio, add a tiny epsilon to the waveform if needed, and recheck ffmpeg decoding.
- The predictor already shrinks `face_det_batch_size` on face-detection OOM, but the better fix is still to lower detection and model batch sizes up front.
- Use `box` only after simpler detector and crop fixes fail.

### Output
- The predictor writes a synced video to the requested `outfile` path and uses temporary working files while composing the result.

## Shared readiness rules

- The video stack should be checked before any heavy run.
- ffmpeg, imageio, and librosa are required for the normal video/audio path.
- CPU is acceptable for stack checks and tiny proof-of-life probes; real motion or lip-sync runs are GPU-first tasks.
