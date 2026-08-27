# Architecture and export troubleshooting

## Checkpoint shape mismatch

Symptoms:

- `load_state_dict` reports missing/unexpected keys
- matrix multiplication fails because layer dimensions differ
- comparison scripts print tensor tables that do not line up

Likely causes:

- the checkpoint family is not the one the script was written for
- `n_layer`, `n_embd`, `vocab_size`, or head size differ from the demo defaults
- a text export still contains multimodal tensors

Recovery:

- compare keys and shapes before trying to run logits
- export only the text model weights when comparing to RWKV-7
- use the repository's explicit shape notes to update the script instead of guessing

## Tokenizer mismatch

Symptoms:

- token ids differ between scripts that otherwise look equivalent
- `rwkv_vocab_v20230424` and a Hugging Face tokenizer produce incompatible ids
- `A/B/C/D` or other answer labels become multi-token pieces

Recovery:

- record which tokenizer each script uses
- check whether a label is one token before using it in a scoring rule
- do not compare logits across tokenizers without a tokenizer-normalized prompt

## Local checkpoint path leakage

Symptoms:

- a script points to a maintainer-only absolute path
- the generated skill would tell future agents to use the repository's local
  path instead of their own checkpoint

Recovery:

- replace local absolute paths with explicit CLI flags or config values
- keep the bundled helper path-agnostic and allow the user to supply a checkpoint

## `torch.load` and wrapper prefixes

Symptoms:

- `_forward_module.` or similar prefixes appear in the loaded state dict
- a fine-tuned checkpoint does not load into the comparison helper

Recovery:

- strip wrapper prefixes before comparing keys
- keep the text-export helper's metadata sidecar so the source model and filtered
  tensor count are visible
