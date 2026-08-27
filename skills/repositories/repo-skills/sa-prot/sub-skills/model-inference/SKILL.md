---
name: model-inference
description: "Load local SaProt checkpoints, tokenize structure-aware sequences,
  extract embeddings, score mutations, and run inverse folding."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SaProt Model Inference

Use this sub-skill when an agent needs to run SaProt inference from local model assets: Hugging Face model directories, ESM-style `.pt` checkpoints, mutation-effect helpers, embedding extraction, or inverse folding. It assumes the caller already has a valid amino-acid plus 3Di structure-aware sequence when structure context is required.

## Route First

- For PDB/mmCIF to AA+3Di sequence conversion, route to `structure-sequences` before using this sub-skill.
- For LMDB schemas, YAML task configs, or dataset placement, route to `datasets-configs`.
- For training, fine-tuning, benchmark evaluation, or ClinVar/ProteinGym scripts, route to `training-evaluation`.

## Local Asset Check

Validate local assets before writing inference code:

```bash
python scripts/check_model_assets.py /path/to/SaProt_650M_AF2
python scripts/check_model_assets.py /path/to/SaProt_650M_AF2.pt --kind esm-pt
python scripts/check_model_assets.py /path/to/SaProt_650M_AF2 --try-tokenizer
```

The repository does not bundle model weights. Hugging Face loading expects a local model directory; `utils.esm_loader.load_esm_saprot` expects a local `.pt` checkpoint file.

## Hugging Face Masked-LM Loading

Use this path for standard tokenizer/model inference from a local SaProt Hugging Face directory:

```python
import torch
from transformers import EsmForMaskedLM, EsmTokenizer

model_dir = "/path/to/local/SaProt_650M_AF2"
device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = EsmTokenizer.from_pretrained(model_dir)
model = EsmForMaskedLM.from_pretrained(model_dir).to(device).eval()

seq = "M#EvVpQpL#VyQdYaKv"
inputs = tokenizer(seq, return_tensors="pt")
inputs = {name: tensor.to(device) for name, tensor in inputs.items()}

with torch.no_grad():
    outputs = model(**inputs)
print(outputs.logits.shape)
```

Structure-aware SaProt tokens are two-character AA+3Di units such as `Ev`, `Qp`, and `L#`. Do not insert spaces unless a specific SaProt helper has already tokenized and rejoined tokens for masked mutation scoring.

## Embeddings With `SaprotBaseModel`

Use `SaprotBaseModel(task="base", config_path=model_dir, load_pretrained=True)` to get last-layer hidden states. `get_hidden_states(inputs, reduction="mean")` returns one tensor per input sequence; with `reduction=None`, each tensor preserves per-token hidden states excluding special tokens.

```python
import torch
from transformers import EsmTokenizer
from model.saprot.base import SaprotBaseModel

model_dir = "/path/to/local/SaProt_650M_AF2"
device = "cuda" if torch.cuda.is_available() else "cpu"

model = SaprotBaseModel(task="base", config_path=model_dir, load_pretrained=True)
model = model.to(device).eval()
tokenizer = EsmTokenizer.from_pretrained(model_dir)

seq = "M#EvVpQpL#VyQdYaKv"
inputs = tokenizer(seq, return_tensors="pt")
inputs = {name: tensor.to(device) for name, tensor in inputs.items()}

with torch.no_grad():
    embeddings = model.get_hidden_states(inputs, reduction="mean")
print(embeddings[0].shape)
```

For the 35M and 650M SaProt checkpoints, prefer SA-token input for frozen embeddings. AA-only input works syntactically but is not the intended frozen-embedding mode for those checkpoints. The 1.3B SaProt variants are documented as better for AA-only usage.

## Mutation Effects

Use `SaprotFoldseekMutationModel` with a local Hugging Face model directory. `foldseek_path` can be `None` for the direct helper methods below when you already provide a combined AA+3Di sequence.

```python
import torch
from model.saprot.saprot_foldseek_mutation_model import SaprotFoldseekMutationModel

model_dir = "/path/to/local/SaProt_650M_AF2"
device = "cuda" if torch.cuda.is_available() else "cpu"

model = SaprotFoldseekMutationModel(
    foldseek_path=None,
    config_path=model_dir,
    load_pretrained=True,
)
model = model.to(device).eval()

seq = "M#EvVpQpL#VyQdYaKv"
score = model.predict_mut(seq, "V3A:Q4M")
substitution_scores = model.predict_pos_mut(seq, 3)
substitution_probs = model.predict_pos_prob(seq, 3)
```

Mutation strings are 1-indexed and use the amino-acid position, for example `V3A`. Multiple substitutions use colon syntax such as `V3A:Q4M`. `predict_pos_mut(seq, pos)` returns log-ratio mutation effects for all 20 amino acids at that 1-indexed position; `predict_pos_prob(seq, pos)` returns amino-acid probabilities at the masked position.

## ESM-Style `.pt` Loading

Use `load_esm_saprot` only for the SaProt `.pt` checkpoint format:

```python
from utils.esm_loader import load_esm_saprot

pt_path = "/path/to/local/SaProt_650M_AF2.pt"
model, alphabet = load_esm_saprot(pt_path)
model.eval()
```

This path requires `torch` and `fair-esm`. It builds the SaProt alphabet from the AA vocabulary plus Foldseek 3Di vocabulary and then loads the checkpoint `model` and `config` entries.

## Inverse Folding

Use `SaProtIFModel` with a local inverse-folding Hugging Face model directory. The amino-acid string and Foldseek structure string must have equal length. Mask amino acids to predict with `#`.

```python
import torch
from model.saprot.saprot_if_model import SaProtIFModel

model_dir = "/path/to/local/SaProt_650M_AF2_inverse_folding"
device = "cuda" if torch.cuda.is_available() else "cpu"

model = SaProtIFModel(config_path=model_dir, load_pretrained=True)
model = model.to(device).eval()

predicted_sequences = model.predict("##########", "dddddddddd", method="argmax")
print(predicted_sequences[0])
```

`method` must be `"argmax"` or `"multinomial"`. `num_samples` must be `1` for `argmax`; use `method="multinomial"` for multiple sampled designs. The method returns a list of predicted amino-acid sequences, even for deterministic `argmax`.

## References

- `references/api-reference.md` for signatures, return shapes, and method distinctions.
- `references/model-assets.md` for checkpoint catalog, local asset layout, and AA-only caveats.
- `references/troubleshooting.md` for dependency, path, tokenization, CUDA/CPU, mutation, and inverse-folding failures.
