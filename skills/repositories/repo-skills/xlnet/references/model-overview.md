# XLNet model and artifact overview

## When to read

Read this when a task needs the released XLNet model artifacts, hardware/memory expectations, or the shared assumptions behind the downstream fine-tuning and pretraining sub-skills.

## Repository identity

XLNet is a legacy TensorFlow 1.x implementation of generalized permutation language modeling with a Transformer-XL backbone. The public codebase exposes source scripts rather than an installable Python distribution. Most user workflows therefore run from an XLNet runtime where the source modules and task scripts are importable.

## Released model bundles

The README describes two cased releases:

| Model | Config shape | Bundle contents | Typical use |
| --- | --- | --- | --- |
| XLNet-Large, Cased | 24 layers, 1024 hidden, 16 heads | TensorFlow checkpoint prefix `xlnet_model.ckpt`, `spiece.model`, `xlnet_config.json` | SOTA-sized fine-tuning and pretraining continuation, usually TPU or multiple high-memory GPUs. |
| XLNet-Base, Cased | 12 layers, 768 hidden, 12 heads | Same three artifact types | More practical GPU fine-tuning fallback, especially for SQuAD base recipes. |

Every downstream command needs the `spiece.model` and `xlnet_config.json`. Training commands also usually need `--init_checkpoint` pointing at the checkpoint prefix, while evaluation/prediction-only commands use fine-tuned checkpoints under `--model_dir` or an explicit prediction checkpoint flag.

## Artifact contracts

- `xlnet_config.json` must contain: `n_layer`, `d_model`, `n_head`, `d_head`, `d_inner`, `ff_activation`, `untie_r`, and `n_token`.
- `spiece.model` is the SentencePiece model used by `prepro_utils.encode_pieces()` and all task preprocessing.
- `xlnet_model.ckpt` is a TensorFlow checkpoint prefix, not a single file. A complete checkpoint usually includes index/data/metadata companions.
- Keep `model_dir` separate from the pretrained checkpoint directory. `model_dir` is where fine-tuned checkpoints and TensorFlow events are written.
- Keep `output_dir` separate from `model_dir`; it is the TFRecord/feature cache for task data.

Use `scripts/check_xlnet_environment.py` at the root of this generated skill for a safe runtime/config diagnostic before running XLNet jobs.

## Hardware and memory notes

The original repository was tested with TensorFlow 1.13.1 under Python 2, and this skill verified CPU/API inspection with a TensorFlow 1.15.x CPU runtime. Treat all full training recipes as legacy TensorFlow 1.x workflows.

README memory guidance for single 16GB GPU fine-tuning:

| Model | Sequence length | Max batch size on one 16GB GPU |
| --- | ---: | ---: |
| XLNet-Base | 64 | 120 |
| XLNet-Base | 128 | 56 |
| XLNet-Base | 256 | 24 |
| XLNet-Base | 512 | 8 |
| XLNet-Large | 64 | 16 |
| XLNet-Large | 128 | 8 |
| XLNet-Large | 256 | 2 |
| XLNet-Large | 512 | 1 |

For multi-GPU fine-tuning through task scripts, `num_core_per_host` means number of GPUs and `train_batch_size` is per GPU. For TPU scripts, `num_hosts * num_core_per_host` controls TPU shards.

## Result anchors from the README

Use these only as context, not as verification expectations for new runs:

- SQuAD2.0 XLNet-Large dev F1 around 88.6 with the provided TPU large recipe.
- RACE XLNet-Large accuracy 81.75 with sequence length 512 and batch size 32 on a large TPU pod; batch size 8 on TPU v3-8 gives around 80.3.
- IMDB XLNet-Large TPU recipe expects `eval_accuracy 0.962+`; the Colab GPU notebook reports lower accuracy around 0.92416 with constrained settings.
- STS-B XLNet-Large GPU example expects `eval_pearsonr 0.916+`.

Full reproduction depends on datasets, checkpoints, hardware, and long training time; this generated skill focuses on correct operating guidance, command construction, validation, and troubleshooting.
