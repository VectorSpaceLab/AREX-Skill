# CLI reference

## Main console commands

| Command | Purpose | Typical follow-up |
| --- | --- | --- |
| `onmt_build_vocab` | Build source and target vocabularies from corpus YAML | `sub-skills/data-preparation/` |
| `onmt_train` | Train seq2seq or language-model checkpoints | `sub-skills/training/` |
| `onmt_translate` | Run inference, scoring, or alignment-aware decoding | `sub-skills/inference/` |
| `onmt_server` | Start the REST translation server | `sub-skills/inference/` |
| `onmt_average_models` | Average multiple checkpoints | `sub-skills/conversion/` |
| `onmt_release_model` | Strip training state or export CTranslate2 models | `sub-skills/conversion/` |

## Most useful flags

### `onmt_build_vocab`

- `-config`: YAML config file with corpus definitions.
- `-save_data`: output prefix for vocab and sample artifacts.
- `-src_vocab` / `-tgt_vocab`: vocabulary output files.
- `-n_sample`: number of transformed samples to count.
- `-learn_subwords`: learn BPE or SentencePiece before counting.
- `-transforms`: global transforms to apply.

### `onmt_train`

- `-config`: main training config file.
- `-data`: YAML corpus definition.
- `-src_vocab` / `-tgt_vocab`: vocab files.
- `-save_model`: checkpoint prefix.
- `-world_size` / `-gpu_ranks`: distributed training layout.
- `-train_steps` / `-valid_steps`: training schedule.
- `-copy_attn`, `-encoder_type`, `-decoder_type`, `-position_encoding`, `-lambda_align`, `-update_vocab`, `-train_from`, `-lora_layers`, `-quant_layers`: common model and fine-tuning options.

### `onmt_translate`

- `--model`: one or more model paths.
- `--src` / `--tgt`: source and optional reference files.
- `--output`: prediction file.
- `--beam_size`, `--batch_size`, `--batch_type`: decoding controls.
- `--report_align`, `--gold_align`, `--with_score`, `--n_best`: output controls.
- `--transforms`, `--src_feats_defaults`, `--n_src_feats`: tokenization and feature support.
- `--gpu`, `--gpu_ranks`, `--world_size`, `--parallel_mode`: device layout.

### `onmt_server`

- `--model_config`: JSON file describing available models.
- `--ip`, `--port`, `--url_root`: listener settings.
- `--debug`: request logging.

### `onmt_release_model`

- `--model` / `--output`: checkpoint input and output.
- `--format`: `pytorch` or `ctranslate2`.
- `--quantization`: CT2 quantization option.

### `onmt_average_models`

- `-models`: model files to average.
- `-output`: output checkpoint.
- `-fp32`: cast model weights to float32 first.

## Rule of thumb

If a task asks for a command line but does not specify which sub-skill owns it, pick the sub-skill by the main artifact:
- corpora and vocab files -> data preparation
- checkpoints and optimization -> training
- outputs, alignments, or server responses -> inference
- checkpoint transforms and conversion outputs -> conversion
