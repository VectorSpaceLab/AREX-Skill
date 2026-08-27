# Training and Data Troubleshooting

## Missing corpus roots

**Symptoms**

- Wrapper expands `all_ud` to nothing.
- Commands fail before reading train/dev/test files.
- Paths under `data/tokenize`, `data/ner`, or similar are absent.

**Recovery**

1. Replace placeholders in `scripts/config_template.sh` and source it in the shell that launches training.
2. Confirm `UDBASE`, `NERBASE`, `CONSTITUENCY_BASE`, and task data directories exist.
3. Run a converter on one tiny fixture before full corpora.
4. Prefer explicit `--train_file`, `--eval_file`, `--txt_file`, and `--label_file` over implicit defaults when debugging.

## Empty or malformed training data

**Symptoms**

- Errors mention empty training data.
- CoNLL-U parser reports field-count or ID failures.
- NER evaluation is nonsensical after conversion.

**Recovery**

- Validate CoNLL-U with the `documents-and-conllu` validator.
- Check train/dev/test split sizes and ensure blank-line sentence boundaries are preserved.
- For NER, confirm BIO/BIOES/BEIOS scheme and tag-column counts before training.
- For tokenization labels, verify text and label files cover the same character stream.

## Pretrain or charlm not found

**Symptoms**

- A wrapper tries to download a default pretrain or charlm.
- Errors mention missing `.pt` files under model/resource roots.
- Multiple pretrain candidates exist and no exact path was provided.

**Recovery**

1. Decide whether downloads are allowed.
2. If not, pass explicit `--wordvec_pretrain_file`, `--charlm_forward_file`, `--charlm_backward_file`, or disable the dependency with a model-family flag such as `--no_charlm` or `--no_pretrain` when scientifically valid.
3. If downloads are allowed, use the pipeline/resources sub-skill to stage resources first and record cache location plus resource version.

## Optional transformer, PEFT, and tokenizer extras

**Symptoms**

- `ImportError: No module named transformers` or `peft`.
- LoRA/PEFT flags are accepted but model construction fails later.
- External tokenizer variants fail to import.

**Recovery**

- Install only the needed extra or dependency for the selected model family.
- Use `--no_bert_model`, `--no_bert_finetune`, or omit `--use_peft` for a no-transformer baseline.
- Do not install all extras just to inspect a command.

## CUDA OOM or device mismatch

**Symptoms**

- CUDA out-of-memory during training.
- Torch says CUDA is unavailable after `--cuda`.
- Tensor device mismatch errors appear during model update.

**Recovery**

1. Run `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"`.
2. Force CPU with `--cpu` for a tiny functional smoke.
3. Reduce `--batch_size`, `--max_batch_words`, sequence lengths, or transformer finetuning layers.
4. Disable transformer/PEFT/charlm features to isolate the failure.
5. Do not claim GPU validation from CPU-only imports.

## W&B or remote logging side effects

**Symptoms**

- Training prompts for credentials.
- Runs appear in the wrong W&B project.

**Recovery**

- Remove `--wandb` and `--wandb_name` unless logging is explicitly required.
- If W&B is required, configure credentials outside the command and record the run name.

## Save-dir collisions and accidental overwrites

**Symptoms**

- Wrapper skips training because a model already exists.
- `--force` overwrites a checkpoint unexpectedly.

**Recovery**

- Always set a task-specific `--save_dir`.
- Review computed model names before training.
- Use `--force` only after preserving or intentionally replacing the old checkpoint.
- Keep dev/test outputs out of training checkpoint directories.

## Large word-vector downloads

Bulk vector downloads are network-heavy and perform decompression, deletion, and symlink creation. Treat them as reference-only. Build an explicit download plan with target directory, expected size, checksum or source provenance, and operator approval before using it.
