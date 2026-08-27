# GPT-2 LoRA workflows

## Model and training options

The historical model cards are `gpt2.sm`, `gpt2.md`, and `gpt2.lg`. The training
entry point exposes these LoRA controls:

| Option | Purpose |
| --- | --- |
| `--lora_dim` | Adapter rank; zero disables LoRA. |
| `--lora_alpha` | Low-rank scaling numerator. |
| `--lora_dropout` | Dropout on the LoRA input path. |
| `--init_checkpoint` | Original pretrained GPT-2 checkpoint. |
| `--work_dir` | Output directory for logs and checkpoints. |

A representative training command is:

```bash
python gpt2_ft.py \
  --train_data ./data/e2e/train.jsonl \
  --valid_data ./data/e2e/valid.jsonl \
  --train_batch_size 8 --valid_batch_size 4 \
  --seq_len 512 --model_card gpt2.md \
  --init_checkpoint ./pretrained_checkpoints/gpt2-medium-pytorch_model.bin \
  --platform local --clip 0.0 --lr 0.0002 --weight_decay 0.01 \
  --scheduler linear --warmup_step 500 --max_epoch 5 \
  --lora_dim 4 --lora_alpha 32 --lora_dropout 0.1 \
  --work_dir ./trained_models/GPT2_M/e2e
```

The original recipe launches one distributed process even for a single GPU. Use
the launcher supported by the installed PyTorch version and start with a tiny
fixture or low `max_step` when validating wiring.

## Generation and decoding

The beam stage must use the same model card, base checkpoint, LoRA rank/alpha,
and work directory as training. Important controls include `--beam`,
`--length_penalty`, `--no_repeat_ngram_size`, `--repetition_penalty`,
`--eos_token_id`, and `--output_file`.

Then decode the prediction JSONL with the original formatted input and the
matching vocabulary. E2E writes one reference block per example; WebNLG and
DART write one file per reference id. Pass `--ref_type webnlg` or `--ref_type
dart` and the correct `--ref_num` when creating those files.

## Checkpoint semantics

During training, intermediate checkpoints are saved as a dictionary containing
`model_state_dict: lora_state_dict(model)` when the rank is positive. The final
checkpoint path may contain the full model state in the historical code. Inspect
the keys before assuming a file is adapter-only. When loading a base GPT-2
checkpoint, the model code also normalizes historical `.w`, `.b`, and `.g`
parameter suffixes.

## Evaluation boundaries

E2E, WebNLG, and DART evaluation uses external projects and metric runtimes.
The repository's setup helper clones those projects and may require network,
Perl, Java, NLTK data, and metric-specific Python packages. Keep evaluation as
a separate, explicit stage after validating decoded files; do not run external
installation scripts as an implicit side effect of a smoke check.
