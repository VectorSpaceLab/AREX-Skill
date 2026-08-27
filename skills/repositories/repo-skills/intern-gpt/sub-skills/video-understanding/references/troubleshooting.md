# Video troubleshooting

## Quick diagnosis table

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Captioning fails before any text appears | The caption checkpoint is missing, unreadable, or mismatched | Treat `VideoCaption` as unavailable and fall back to action recognition or upload-only behavior until the caption checkpoint is restored. |
| Action recognition does not initialize | The action checkpoint or cache is missing, or the download path is blocked | Keep the plan to a caption-only or upload-only workflow until the action model is available. |
| Dense captioning crashes during import or predictor setup | Detectron2 build problems, compiled-extension mismatch, or missing GRiT weights | Do not promise dense captions; use caption/action-only output or repair the Detectron2/GRiT environment first. |
| TikTok generation stops before narration | OpenAI key is missing or invalid | The timestamp and narration stages are blocked; return the analysis tools' outputs instead of fabricating a clip. |
| TikTok generation reaches audio generation but fails at muxing | ffmpeg binary is missing, misconfigured, or cannot probe the media | Use the analysis outputs only, or fix the system ffmpeg path before retrying the clip step. |
| TikTok generation fails during narration synthesis | Bark or its audio stack is missing | Do not claim a narrated clip; keep the plan at caption/action/dense analysis. |
| Video path is rejected | The path is empty, remote, or does not have a supported local video suffix | Use a local video file with a supported extension such as `.mp4`; if the file does not exist yet, treat the plan as incomplete. |
| GPU memory runs out | Too many video tools are loaded together, or the clip is too large for the device | Reduce the plan to the smallest tool set, enable e-mode if available, or switch from TikTok generation to a single analysis tool. |
| Inference is slow but memory is lower than expected | e-mode is moving models back to CPU between calls | This is expected behavior; keep e-mode on for lower VRAM use, or load fewer tools if latency matters more than memory. |

## Checkpoint-specific reminders

- **Tag2Text** supports `VideoCaption`; if it is missing, pre-captioning during upload should degrade to a generic video note.
- **uniformerv2** supports `ActionRecognition`; if it is missing, the action label cannot be produced.
- **detectron2 + GRiT** support `DenseCaption`; if they are missing, dense descriptions are unavailable.
- **ffmpeg** is required for probe, trim, concat, and mux steps in the TikTok flow.
- **Bark** is required for generated narration audio.
- **OpenAI** is required for the timestamp-selection and narration-polish stages.

## Recovery guidance

- If only the composite TikTok step fails, keep the upstream analysis outputs and report the partial block clearly.
- If a user only wanted action recognition, do not escalate the failure into a TikTok or dense-caption problem.
- If the validation helper rejects the plan, fix the plan first rather than forcing a runtime attempt.
