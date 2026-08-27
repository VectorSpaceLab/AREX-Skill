# Workflows

## 1) Choose the corpus form

Pick one input style and keep it consistent throughout preprocessing:

- **Raw text**: one sentence per line, blank line = document boundary.
- **Raw text with paragraphs**: use `<eop>` at the end of a sentence line, without adding a space before it.
- **Pre-tokenized ids**: whitespace-separated integer ids per line, with `--from_raw_text=False`.

`data_utils.py` still loads a SentencePiece model in both modes, because the pretraining pipeline uses piece boundaries while building masks.

## 2) Build or verify SentencePiece first

The README recipe uses:

```bash
spm_train \
  --input=$INPUT \
  --model_prefix=sp10m.cased.v3 \
  --vocab_size=32000 \
  --character_coverage=0.99995 \
  --model_type=unigram \
  --control_symbols=<cls>,<sep>,<pad>,<mask>,<eod> \
  --user_defined_symbols=<eop>,.,(,),",-,–,£,€ \
  --shuffle_input_sentence \
  --input_sentence_size=10000000
```

Keep the special symbols intact. Missing `<eop>` or `<eod>` support is a common source of downstream mismatch.

## 3) Validate the corpus before preprocessing

Use the bundled text validator on every new corpus or shard set:

- `--mode auto` for mixed discovery
- `--mode raw` for raw text with `<eop>` markers or numeric-heavy text
- `--mode ids` for integer-id lines

The validator checks:

- empty input globs
- empty files
- blank-line document boundaries
- `<eop>` suffix placement in raw text
- non-integer tokens in id mode

## 4) Preprocess into TFRecords

Use the bundled command builder in `preprocess` mode to generate the exact `data_utils.py` command.

Typical settings from the README example:

- `--bsz_per_host=32`
- `--num_core_per_host=16`
- `--seq_len=512`
- `--reuse_len=256`
- `--bi_data=True`
- `--mask_alpha=6`
- `--mask_beta=1`
- `--num_predict=85`

Important behavior:

- `task` selects the shard subset with `file_paths[task::num_task]`.
- `pass_id` changes the random seed and the output filename prefix.
- `task=0` writes `corpus_info.json`.
- Each task/pass writes one `record_info-...json` plus one `.tfrecords` file.

If you use multiple workers, keep the same `num_task` across all workers and give each worker a unique `task` index.

## 5) Train on GPU or TPU

### GPU path

Use the command builder in `gpu` mode for `train_gpu.py`.

Key reminders:

- `train_batch_size` is the whole host batch.
- `train_batch_size` must divide evenly by `num_core_per_host`.
- `save_steps` is required because the training loop checkpoints with it.
- `record_info_dir` can be a comma-separated list of directories.

### TPU path

Use the command builder in `tpu` mode for `train.py`.

Key reminders:

- `train.py` is the legacy TPU entrypoint.
- `perm_size > 0` is required.
- `seq_len` and `reuse_len` must be set consistently with preprocessing.
- `save_steps` is forwarded to the TPU `RunConfig`.
- The environment must support the older TensorFlow 1.x TPU stack.

## 6) Keep the large-model sketch handy

The README’s XLNet-Large sketch is the best default starting point when you need a known-good pretraining bundle:

```text
seq_len=512
reuse_len=256
mem_len=384
perm_size=256
n_layer=24
d_model=1024
d_embed=1024
n_head=16
d_head=64
d_inner=4096
untie_r=True
mask_alpha=6
mask_beta=1
num_predict=85
```

Use it as a compatibility baseline, then adjust batch size, cores, and checkpointing for the target hardware.

## 7) Keep preprocessing and training aligned

Before launching training, verify that these values match between preprocessing and training:

- `seq_len`
- `reuse_len`
- `bi_data`
- `mask_alpha`
- `mask_beta`
- `num_predict`
- `uncased`
- `perm_size`

Do not rely on source-script defaults for these shared values: preprocessing and training do not share the same defaults for all of them.

Also keep `model_dir` separate from `init_checkpoint`.
