# Checkpoints and tokenizers

## VAE source options

A DALL-E training run must choose exactly one VAE source:

| Choice | How it is selected | Notes |
| --- | --- | --- |
| Trained `DiscreteVAE` checkpoint | `--vae_path <vae.pt>` | Checkpoint must contain `hparams` and `weights`. |
| Resume full DALL-E checkpoint | `--dalle_path <dalle.pt>` | Restores DALL-E hparams, VAE params/class, weights, optimizer, scheduler, and epoch when present. |
| OpenAI VAE | no `--vae_path`, no `--taming` | Source asserts torch `<=1.10`; constructor downloads cached pickle weights if compatible. |
| Taming VQGAN | `--taming` plus optional VQGAN paths | Default paths can download; custom model requires both checkpoint and config. |

## DALL-E checkpoint payload

The helper saves:

```python
{
    "hparams": dalle_params,
    "vae_params": vae_params,
    "epoch": epoch,
    "version": __version__,
    "vae_class_name": vae.__class__.__name__,
    "weights": dalle.state_dict(),
    "opt_state": opt.state_dict(),
    "scheduler_state": scheduler.state_dict() if scheduler else None,
}
```

For DeepSpeed, a checkpoint directory plus `auxiliary.pt` may be written. ZeRO stage 2/3 may not yield ordinary weights directly; use distributed/backend guidance before generation.

## Tokenizer choices

| Flag/API | Tokenizer | Notes |
| --- | --- | --- |
| default | OpenAI-style `SimpleTokenizer` | Uses packaged BPE vocabulary. |
| `--bpe_path <path>` | `YttmTokenizer` by default | BPE model must use padding id `0`. |
| `--bpe_path <path> --hug` | `HugTokenizer` | Expects a HuggingFace `tokenizers` JSON file. |
| `--chinese` | `ChineseTokenizer` | Uses HuggingFace `bert-base-chinese`; may need model cache/network. |

Training and generation must agree on tokenizer family and `text_seq_len`. A checkpoint trained with one vocabulary size cannot be safely generated with a different tokenizer unless the model was constructed accordingly.

## Resume checklist

Before resuming:

- confirm `--dalle_path` points to the same type of checkpoint the helper expects;
- do not also pass `--vae_path` because the parser treats VAE and DALL-E paths as mutually exclusive;
- preserve tokenizer choices and model size unless they are stored in the checkpoint;
- for DeepSpeed checkpoints, check whether `auxiliary.pt` and partitioned folders exist;
- for generation, ensure `vae_class_name` matches `--taming`/VAE wrapper selection.
