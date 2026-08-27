# Training CLI

The program accepts:

```text
--base_dir PATH             default ~/tacotron
--input PATH                default training/train.txt
--model NAME                default tacotron
--name NAME                 log run name; defaults to model
--hparams STRING            comma-separated name=value overrides
--restore_step INTEGER      restore model.ckpt-<step>
--summary_interval INTEGER  default 100
--checkpoint_interval INTEGER default 1000
--slack_url URL             optional webhook; treat as a secret
--tf_log_level INTEGER      default 1
--git                       require a clean Git checkout and record commit
```

The script creates `<base_dir>/logs-<name>` and initializes `train.log`. It
loads metadata from `<base_dir>/<input>`, constructs a data-feeder queue, and
writes checkpoints plus audio/alignment artifacts at checkpoint intervals.
`tensorboard --logdir <log_dir>` can inspect summaries when TensorBoard is
installed.

Do not put webhook URLs in shell history or public logs. Avoid `--git` when the
working tree contains intentional changes; its cleanliness check uses
`git diff-index --quiet HEAD`.
