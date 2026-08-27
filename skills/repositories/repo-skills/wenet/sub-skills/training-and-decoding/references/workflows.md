# Training and Decoding Workflows

## Staged recipe pattern

WeNet recipes are easiest to adapt stage by stage:

| Stage family | What to verify before continuing |
|---|---|
| Data acquisition | corpus path exists; downloads are approved; enough storage |
| Data preparation | `wav.scp` and `text` keys match; data lists are valid |
| CMVN/features | audio decodes; feature config matches model config |
| Dictionary/tokenizer | reserved tokens and tokenizer files match config |
| Training | config, train/cv data, device, distributed launcher, output directory |
| Averaging | enough checkpoints exist; validation-best or last-N policy is intended |
| Recognition | `train.yaml`, checkpoint, test `data.list`, decoding modes, result directory |
| Scoring | reference/hypothesis keys match; word or character unit is intentional |
| Export | `train.yaml` and checkpoint are stable; route to model-export |

Run a new recipe one stage at a time. Do not launch a full multi-stage job until
each upstream artifact is validated.

## Training command shape

Prefer module execution in installed or editable environments:

```bash
torchrun --nnodes=1 --nproc_per_node=<num_gpus> \
  --rdzv_id=<job_id> --rdzv_backend=c10d --rdzv_endpoint=localhost:0 \
  -m wenet.bin.train \
  --train_engine torch_ddp \
  --config train.yaml \
  --data_type raw \
  --train_data train.data.list \
  --cv_data dev.data.list \
  --model_dir exp/conformer \
  --tensorboard_dir tensorboard \
  --ddp.dist_backend nccl \
  --num_workers 8 --prefetch 10 --pin_memory
```

Important choices:

- `--train_engine`: `torch_ddp`, `torch_fsdp`, or `deepspeed`.
- `--device`: `cuda` by default in training code; use `cpu` only for tiny
  debugging and expect distributed code paths to need adjustment.
- `--data_type`: `raw` or `shard`.
- `--override_config`: can be repeated to modify YAML values.
- `--checkpoint`: resumes or initializes from an existing checkpoint.
- `--use_lora` and LoRA arguments enable fine-tuning paths when the config and
  checkpoint support them.

For multi-node training, set rendezvous endpoint, node count, rank/world-size
environment, and network variables explicitly. Do not rely on a single-node
command on a cluster.

## Resume training

If an experiment stopped after checkpoint `N.pt`, resume the training stage with
that checkpoint:

```bash
torchrun --nnodes=1 --nproc_per_node=<num_gpus> ... \
  -m wenet.bin.train \
  --config exp/conformer/train.yaml \
  --train_data train.data.list --cv_data dev.data.list \
  --model_dir exp/conformer \
  --checkpoint exp/conformer/N.pt
```

Keep the same tokenizer/data/config assumptions unless intentionally
fine-tuning. After training, WeNet writes epoch checkpoints, YAML snapshots, and
a `final.pt` symlink or final checkpoint in the model directory.

## Checkpoint averaging

Checkpoint averaging is commonly used before evaluation:

```bash
python -m wenet.bin.average_model \
  --dst_model exp/conformer/avg_30.pt \
  --src_path exp/conformer \
  --num 30 --val_best
```

Use `--val_best` when validation metrics should select checkpoints. Without it,
verify the script's selection policy before publishing scores.

## Offline recognition

Recognition reads a config, checkpoint, and test manifest:

```bash
python -m wenet.bin.recognize \
  --config exp/conformer/train.yaml \
  --data_type raw \
  --test_data test.data.list \
  --checkpoint exp/conformer/avg_30.pt \
  --modes ctc_greedy_search ctc_prefix_beam_search attention attention_rescoring \
  --beam_size 10 --batch_size 32 \
  --result_dir exp/conformer/decode \
  --device cuda
```

Common modes include:

- `ctc_greedy_search`
- `ctc_prefix_beam_search`
- `attention`
- `attention_rescoring`
- `rnnt_greedy_search`, `rnnt_beam_search`, `rnnt_beam_attn_rescoring`
- `hlg_onebest`, `hlg_rescore`
- `paraformer_greedy_search`, `paraformer_beam_search`

For `ctc_prefix_beam_search` and `attention_rescoring`, keep `batch_size=1`
when the selected model/mode combination requires single-utterance beam search.

## Streaming and context options

Use `--decoding_chunk_size`, `--num_decoding_left_chunks`, and
`--simulate_streaming` to evaluate streaming behavior. Context biasing uses
`--context_bias_mode`, `--context_list_path`, and `--context_graph_score`.
Check that tokenizer resources and context-list tokenization are compatible.

## LM, FST, and k2 paths

Language-model and k2 paths require extra graph-building dependencies and
language resources. Treat them as optional advanced stages:

- prepare dictionary/lexicon resources;
- train or locate an LM;
- build TLG or HLG graph artifacts;
- run recognition modes such as `hlg_onebest` or `hlg_rescore` with word/HLG
  paths and scale parameters.

Do not start LM/k2 graph construction without checking OpenFST/k2/SRILM or
other required toolchain availability.

## Scoring

For full recipes, score with the same normalization and unit choices used by
the recipe. For small local checks, use the bundled helper:

```bash
python sub-skills/training-and-decoding/scripts/score_text.py \
  --reference ref.txt --hypothesis hyp.txt --unit char --details
```
