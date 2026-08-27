# P-Tuning Command Templates

## P-Tuning v2 on ADGEN

The source template uses `torchrun` with one process, a soft-prompt length
(`PRE_SEQ_LEN`, sample 128), learning rate, gradient accumulation, generated
output directory, `--predict_with_generate`, and `--quantization_bit 4`.
A safe configurable shape is:

```text
torchrun --standalone --nnodes=1 --nproc-per-node=N sub-skills/ptuning/scripts/ptuning_runner/main.py \
  --do_train --train_file TRAIN --validation_file VALIDATION \
  --prompt_column content --response_column summary \
  --model_name_or_path MODEL --output_dir OUTPUT \
  --pre_seq_len 128 --quantization_bit 4 \
  --per_device_train_batch_size 1 --gradient_accumulation_steps 16
```

Add `--max_source_length`, `--max_target_length`, `--learning_rate`,
`--max_steps`, `--save_steps`, and `--preprocessing_num_workers` deliberately.
The sample uses an effective batch size of 16 from batch size 1 times gradient
accumulation 16; adjust the product to trade memory for throughput.

## Multi-turn chat training

Use `--prompt_column prompt --response_column response --history_column
history` and provide the train/validation paths. The repository's shell
launcher reads `CHAT_TRAIN_DATA`, `CHAT_VAL_DATA`, and `CHECKPOINT_NAME`; the
bundled command builder accepts explicit arguments instead of relying on those
ambient variables.

## Prediction

For a prefix checkpoint, pass the base model path plus
`--ptuning_checkpoint CHECKPOINT`, matching `--pre_seq_len` and optional
`--quantization_bit`. For a full fine-tune checkpoint, pass the full checkpoint
as `--model_name_or_path` and omit prefix loading. Use `--do_predict`, a test
file, column names, an output directory, and `--predict_with_generate`.

## Full fine-tuning / DeepSpeed

The source includes a four-GPU DeepSpeed launcher and a ZeRO-2 JSON config.
Treat it as optional and expensive: install a DeepSpeed version compatible with
the selected PyTorch/CUDA stack, verify `deepspeed --help`, reserve four GPUs,
and start with a tiny data subset. Do not install or execute it as a minimum
inspection check.

## Web demo for a prefix checkpoint

The P-Tuning Gradio demo accepts model/checkpoint arguments, `pre_seq_len`, and
optional `quantization_bit`. Load the base model and prefix state before
moving the model to CUDA. Use the legacy Gradio compatibility guidance from
`chat-and-demos`.

The bundled `build_ptuning_command.py` prints these forms and refuses to run
them. Its default runner path is `sub-skills/ptuning/scripts/ptuning_runner/main.py`, and its default prefix web demo path is `sub-skills/ptuning/scripts/ptuning_runner/web_demo.py`. Review the printed paths and data fields before copying a command into a real training shell.
