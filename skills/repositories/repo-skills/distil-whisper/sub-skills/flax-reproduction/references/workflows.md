# Flax Reproduction Workflows

## Purpose

Read this when the user wants the original JAX/Flax Distil-Whisper package, pipeline, evaluation, or conversion helpers.

## Package surface

The verified package exports:

- `FlaxWhisperForConditionalGeneration`
- `FlaxWhisperPipeline`
- `InferenceState`
- `PjitPartitioner`

## Quick inspection pattern

```python
from distil_whisper import FlaxWhisperPipeline

pipe = FlaxWhisperPipeline(checkpoint="distil-whisper/distil-large-v3")
```

## Student initialization

Use `training/flax/create_student_model.py` to copy layers from a teacher checkpoint and optionally shorten the source context length.

```bash
python training/flax/create_student_model.py \
  --teacher_checkpoint "openai/whisper-large-v3" \
  --encoder_layers 32 \
  --decoder_layers 2 \
  --save_dir "./distil-large-v3-init"
```

## Evaluation

Use `training/flax/run_eval.py` for short-form evaluation.

```bash
python training/flax/run_eval.py \
  --model_name_or_path "./distil-large-v3-init" \
  --dataset_name "librispeech_asr+librispeech_asr" \
  --dataset_config_name "all+all" \
  --dataset_split_name "validation.clean+validation.other" \
  --output_dir "./distil-large-v3-init" \
  --streaming \
  --predict_with_generate
```

## Long-form transcription

Use `training/flax/run_long_form_transcription.py` for long audio files.

- `--chunk_length_s` controls the chunking window.
- `--return_timestamps` is useful when the user wants timestamp-aware output.
- `--compilation_cache` can shorten repeat runs on the same machine.

## Conversion to Hugging Face weights

Use `scripts/convert_train_state_to_hf.py` when the user needs the bundled helper for exporting a Flax training state.

Important caveat:

- This bundled copy keeps distributed JAX initialization opt-in so that help checks and single-host smoke runs stay safe.
- Set `DISTIL_WHISPER_ENABLE_JAX_DISTRIBUTED_INIT=1` before a real multi-host conversion job if the environment expects explicit distributed initialization.
- Read the troubleshooting reference before attempting to run it outside a distributed context.
- The source repository script remains `training/flax/convert_train_state_to_hf.py` if you need to compare behavior.

## Training and fine-tuning notes

The repo also contains longer-running recipes for:

- `training/flax/run_distillation.py`
- `training/flax/run_finetuning.py`
- `training/flax/run_pseudo_labelling_pt.py`
- `training/flax/run_pt_long_form_transcription.py`
- `training/flax/run_speculative_decoding.py`
- `training/flax/run_speed.sh`

Treat these as heavy or specialized recipes unless the user explicitly wants them.
