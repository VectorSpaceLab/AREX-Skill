# DeepRapper workflow reference

DeepRapper is the lyric-first rap generator in Muzic. It combines rhyme-aware tokenization, beat modeling, reverse decoding, and optional beam/rhyme controls.

## Asset layout

| Asset | Expected layout | Purpose |
|---|---|---|
| Training data | `data/lyrics/<raw_data_dir>/raw/` and generated `processed/` tokenized files | Input lyrics and pinyin/beat annotations |
| Token tables | `tokenizations/` files for Chinese tokens, finals, sentences, beats, or BPE encoder files | Vocabulary and embedding lookup |
| Training config | model config JSON | GPT2-style architecture settings |
| Model output | `model/<root>/<raw_data_dir>[_reverse]/<model_sign>/final_model` | Saved checkpoint used by generation |
| Pretrained model | `model/deeprapper-model/` with `pytorch_model.bin` and `config.json` | Provided pretrained generation path |
| Samples | `samples_save_dir/...` if sample saving is enabled | Human-readable generation output |

## Workflow map

| Stage | Main command family | Key arguments | Output or effect |
|---|---|---|---|
| Data prep | `train.py` with `--raw --tokenize` | `--root_path`, `--raw_data_dir`, `--with_beat`, `--beat_mode`, `--segment`, `--bpe_token` | Builds tokenized lyric pieces and optional final/sentence/beat streams |
| Training | `train.sh` or `python train.py ...` | `--model_dir`, `--model_sign`, `--device`, `--epochs`, `--batch_size`, `--stride`, `--gradient_accumulation`, `--lr`, `--warmup_steps`, `--pretrained_model` | Saves `model_epoch*` and `final_model` checkpoints |
| Generation | `generate.sh` or `python generate.py ...` | `--model_dir`, `--prefix`, `--pattern`, `--beam_width`, `--temperature`, `--topk`, `--topp`, `--dynamic_rhyme`, `--rhyme_*`, `--with_beat`, `--beat_mode` | Prints and optionally saves generated rap samples |
| Pretrained generation | `generate_from_pretrain.sh` equivalent | `--model_dir model/deeprapper-model`, `--prefix`, same generation controls | Uses the provided pretrained checkpoint |

## Important controls

### Training controls
- `--reverse` switches to the reverse language-model variant and changes the output path suffix to `_reverse`.
- `--enable_final`, `--enable_sentence`, `--enable_relative_pos`, and `--enable_beat` must match the checkpoint that was trained.
- `--with_beat` and `--beat_mode` control beat-aware preprocessing and generation.
- `--fp16` requires Apex-compatible mixed-precision support; treat it as optional.
- `--num_pieces`, `--stride`, and `--min_length` control tokenized chunking.

### Generation controls
- `--pattern sample` uses stochastic sampling; `--pattern beam` activates beam search.
- `--beam_width`, `--beam_samples_num`, and `--beam_sample_select_sg` control beam expansion and selection.
- `--temperature`, `--topk`, `--topp`, and `--repetition_penalty` control token sampling.
- `--dynamic_rhyme`, `--rhyme_sentence_num`, `--rhyme_count`, `--rhyme_bonus`, `--rhyme_alpha`, and `--rhyme_prob_bound` bias rhyme selection.
- `--save_samples` stores timestamped text outputs under `save_samples_dir`.

### Pretrained flow
- The pretrained path expects the unzipped model directory to contain the model binary and config file.
- If generation output looks wrong, check that the checkpoint path, reverse setting, and tokenization flags are aligned with the model that was trained.

## Practical command outline

```bash
# Train from prepared lyric data
python train.py \
  --tokenize --raw \
  --root_path data/lyrics/ \
  --raw_data_dir lyrics_samples \
  --model_dir model \
  --model_sign samples \
  --reverse \
  --enable_final --enable_sentence --enable_relative_pos --enable_beat

# Generate from a trained checkpoint
python generate.py \
  --model_dir model/lyrics/lyrics_samples_reverse/samples/final_model \
  --prefix 'your lyric seed' \
  --pattern beam \
  --save_samples
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `from_pretrained` or checkpoint load fails | Wrong `model_dir` or missing `final_model` | Point generation at the actual saved checkpoint directory |
| Output quality collapses after switching `reverse` | Reverse and non-reverse checkpoints were mixed | Match `--reverse` to the checkpoint family |
| Beat or rhyme flags seem ignored | Training and inference flags do not match | Reuse the same control flags used to train the checkpoint |
| `apex` import error with `--fp16` | Mixed precision is not installed | Disable `--fp16` or install a compatible Apex build |
| Tokenization errors or `[SKIP]` placeholders dominate | Wrong tokenizer family for the checkpoint | Use the tokenizer files the model was trained with |
| Sample file is empty | `--save_samples` was omitted or sample directory was not writable | Enable sample saving and point `--save_samples_dir` to a writable path |

## Notes for future agents
- DeepRapper is rap-specific and is not the same as lyric-to-melody translation.
- The generated helper script is a planner only; it does not run training or generation.
- The command examples here are intentionally relative and should be run from the DeepRapper project root in a user workspace.
