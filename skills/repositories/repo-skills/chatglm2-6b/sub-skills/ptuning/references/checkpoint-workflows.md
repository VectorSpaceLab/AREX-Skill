# Checkpoint Workflows

## Prefix checkpoint

P-Tuning v2 training freezes the base model and saves the trainable
`transformer.prefix_encoder` state. To use it:

1. Load the base tokenizer and base model/config.
2. Set `config.pre_seq_len` to the value used during training and set
   `config.prefix_projection` consistently.
3. Load `pytorch_model.bin` from the prefix checkpoint.
4. Keep only keys beginning with `transformer.prefix_encoder.` and strip that
   prefix before loading them into `model.transformer.prefix_encoder`.
5. Apply the same quantization choice, move to the selected backend, and call
   `.eval()`.

The checkpoint directory is not the same as the base model directory. A
missing or mismatched `pre_seq_len` usually means the prefix module shape does
not match the saved state.

## Full checkpoint

Full-parameter fine-tuning saves the complete model. Load the checkpoint path
directly with `AutoModel.from_pretrained(CHECKPOINT, trust_remote_code=True)`;
do not also attach a prefix checkpoint. Keep the tokenizer aligned with the
checkpoint.

## Predict and serve

Use the bundled P-Tuning runner's `--do_predict` mode with the appropriate
checkpoint type and data columns. After a successful local load, the same
`model.chat`/`stream_chat` contract can feed the `chat-and-demos` UI or the
`api-serving` endpoint. Keep checkpoint loading outside request handlers and
document whether the service expects a base, prefix, or full checkpoint.

## Output artifacts

P-Tuning prediction writes generated outputs under the selected `output_dir`,
including `generated_predictions.txt` when generation is enabled. Preserve the
training arguments and checkpoint step in the output naming scheme; do not
overwrite a prefix run with a full-finetune run.
