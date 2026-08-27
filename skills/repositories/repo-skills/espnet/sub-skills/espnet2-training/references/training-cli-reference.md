# ESPnet2 Training CLI Reference

ESPnet2 train modules are Python CLIs under `espnet2.bin`. Common train modules include:

- `asr_train`, `asr_transducer_train`, `lm_train`, `mt_train`
- `tts_train`, `tts2_train`, `svs_train`, `gan_tts_train`, `gan_svs_train`
- `enh_train`, `enh_tse_train`, `enh_s2t_train`
- `st_train`, `s2t_train`, `s2t_train_ctc`, `s2st_train`, `ps2st_inference`
- `slu_train`, `lid_train`, `spk_train`, `diar_train`, `cls_train`
- `ssl_train`, `hubert_train`, `uasr_train`, `beats_train`, `codec`/`gan_codec` variants

Show available options safely:

```bash
python -m espnet2.bin.asr_train --help
python -m espnet2.bin.asr_train --print_config
python -m espnet2.bin.asr_train --optim adam --print_config
```

ESPnet2 Python CLIs generally use underscores, not hyphens: `--batch_size`, not `--batch-size`.

## CPU dry-run pattern

A dry-run checks parser/config/model construction without iterating over real data:

```bash
python -m espnet2.bin.asr_train   --config conf/train_asr.yaml   --iterator_type none   --dry_run true   --output_dir out   --token_list dummy_token_list
```

The exact placeholder options differ by task; use the bundled `make_dry_run_command.py` for safe command skeletons and inspect task help before executing.

## Resume, fine-tune, freeze

```bash
python -m espnet2.bin.asr_train --resume true
python -m espnet2.bin.asr_train --init_param model.pth
python -m espnet2.bin.asr_train --init_param model.pth:decoder:decoder
python -m espnet2.bin.asr_train --init_param model.pth:::encoder,decoder.embed
python -m espnet2.bin.asr_train --freeze_param encoder.embed decoder.embed
```

Checkpoints save model, optimizer, scheduler, reporter, and AMP state at epoch boundaries. Data iterators are rebuilt per epoch, so interrupted epochs restart from the epoch boundary.

## Logging and monitoring

- `--log_interval` controls intermediate training log frequency.
- `--num_iters_per_epoch` bounds training iterations per epoch for very large corpora.
- TensorBoard logs are usually under `exp/*_train_*/tensorboard/` for recipe runs.
- `--use_wandb true` requires network/account setup and should be disabled for smoke checks unless requested.
