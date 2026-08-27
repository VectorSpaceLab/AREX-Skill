# PyTorch Training Workflows

## Purpose

Read this when the user wants to move from a teacher checkpoint and audio data to a trained or evaluated student model in the PyTorch stack.

## Stage 1: pseudo-labelling

Use `training/run_pseudo_labelling.py` to create pseudo labels from a teacher checkpoint.

```bash
python training/run_pseudo_labelling.py \
  --model_name_or_path "openai/whisper-large-v3" \
  --dataset_name "mozilla-foundation/common_voice_16_1" \
  --dataset_config_name "hi" \
  --dataset_split_name "train+validation+test" \
  --text_column_name "sentence" \
  --id_column_name "path" \
  --output_dir "./common_voice_16_1_hi_pseudo_labelled" \
  --return_timestamps \
  --concatenate_audio \
  --streaming False \
  --generation_num_beams 1
```

Key flags:

- `--concatenate_audio` improves throughput and long-form compatibility.
- `--return_timestamps` keeps the pseudo labels useful for timestamp-aware training.
- `--streaming` is helpful for large Hub datasets.
- `--generation_num_beams 1` is the recommended fast path unless the teacher is hallucinating.

## Stage 2: student initialization

Use `training/create_student_model.py` to copy the encoder and selected decoder layers from a teacher checkpoint.

```bash
python training/create_student_model.py \
  --teacher_checkpoint "openai/whisper-large-v3" \
  --encoder_layers 32 \
  --decoder_layers 2 \
  --save_dir "./distil-large-v3-init"
```

Key ideas:

- Keep the full encoder unless the user explicitly wants a shorter context-length variant.
- Default to two decoder layers for the standard distilled checkpoint.
- Consider `distil-whisper/distil-large-v3` as the teacher when the user wants language transfer from an already distilled English model.

## Stage 3: distillation training

Use `training/run_distillation.py` for the teacher-student training loop.

```bash
accelerate launch training/run_distillation.py \
  --model_name_or_path "./distil-large-v3-init" \
  --teacher_model_name_or_path "openai/whisper-large-v3" \
  --train_dataset_name "../common_voice_16_1_hi_pseudo_labelled+../common_voice_16_1_hi_pseudo_labelled" \
  --train_split_name "train+validation" \
  --text_column_name "sentence+sentence" \
  --train_dataset_samples "7+4" \
  --eval_dataset_name "../common_voice_16_1_hi_pseudo_labelled" \
  --eval_split_name "test" \
  --do_train --do_eval \
  --freeze_encoder \
  --streaming \
  --push_to_hub
```

Key flags:

- `--freeze_encoder` saves memory when the encoder is copied exactly from the teacher.
- `--train_dataset_samples` controls multi-dataset sampling under streaming mode.
- `--wer_threshold` filters bad pseudo labels.
- `--language` is useful when you are mixing languages or training on a non-English language.

## Stage 4: evaluation

Use `training/run_eval.py` for the evaluation pass.

```bash
python training/run_eval.py \
  --model_name_or_path "./distil-large-v3-init" \
  --dataset_name "librispeech_asr+librispeech_asr" \
  --dataset_config_name "all+all" \
  --dataset_split_name "validation.clean+validation.other" \
  --output_dir "./distil-large-v3-init" \
  --streaming \
  --predict_with_generate
```

## Language mixing

When a low-resource language benefits from a closely related language, pseudo-label each dataset separately and then combine them in the training command. Keep the target language in the training script even if the pseudo labels carry the source-language tokens.

## Smoke vs full run

- For smoke validation, prefer `--max_steps 1`, a tiny dataset, and `--use_cpu` when the user only needs to prove that the command is wired correctly.
- For real training, follow the README guidance in the original repo and expect the run to be expensive.
