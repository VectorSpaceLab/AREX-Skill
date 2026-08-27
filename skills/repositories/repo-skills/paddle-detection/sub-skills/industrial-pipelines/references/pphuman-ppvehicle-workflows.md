# PP-Human, PP-Vehicle, and PP-Tracking Workflows

## PP-Human

PP-Human combines detection/tracking, attribute recognition, behavior/action modules, ReID/MTMCT, visitor counting, and trace records. Typical questions map to:

- pedestrian detection/tracking: MOT detector/tracker models;
- attribute analysis: detector plus attribute classifier;
- behavior/action: keypoint/action or video/action modules;
- falling/fighting/smoking/phoning/intrusion: specific model chains and post-processing;
- MTMCT/ReID: multi-camera input plus ReID model and post-process.

## PP-Vehicle

PP-Vehicle combines vehicle detection/tracking, plate detection/recognition, vehicle attribute recognition, lane/violation modules, illegal parking, press-line, retrograde, and in/out counting. Confirm whether the model bundle has detection, tracking, OCR/plate, attribute, and lane components before running.

## PP-Tracking

PP-Tracking covers single-camera MOT and multi-camera MTMCT with FairMOT, JDE, DeepSORT, ByteTrack/OC-SORT/BoT-SORT-like routes depending on the config. It usually consumes video input and may require ReID and tracking-specific metrics/results.

## Practical guardrails

- Most out-of-the-box examples rely on remote model downloads; stage local model directories when reproducibility matters.
- Real-time claims require GPU/TensorRT or device-specific validation, not a CPU smoke test.
- Use short clips/images first. Full RTSP or multi-camera runs can hang on I/O, codecs, or network rather than model logic.
- Store output visualizations and stream push URLs explicitly; avoid overwriting previous runs.
