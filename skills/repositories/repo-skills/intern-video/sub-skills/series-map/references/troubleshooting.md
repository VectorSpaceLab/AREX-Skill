# Series-Selection Troubleshooting

## Symptom: the requested checkpoint does not fit the script

Likely cause: mixing Stage1 visual, Stage2 retrieval, CLIP, MLLM, or InternVideo-Next families.

Recovery:
1. Identify the checkpoint source/model ID.
2. Match it to the generation map.
3. Use only that generation's config/entrypoint conventions.

## Symptom: the user asks for "InternVideo3 training" but provides InternVideo2 paths

Likely cause: confusing model release generations.

Recovery: explain that InternVideo3 SFT uses the `InternVideo3_sft` XTuner-style package, environment variables such as `META_DATA_PATH`, `LOAD_FROM`, and `PROCESSOR_PATH`, and different dependencies from InternVideo2.

## Symptom: no task-specific route is obvious

Ask for the intended output, not every environment detail. Useful options are: action-recognition model, video-text retrieval score, long-video MLLM answer, pretraining run, benchmark evaluation, or dataset validation.
