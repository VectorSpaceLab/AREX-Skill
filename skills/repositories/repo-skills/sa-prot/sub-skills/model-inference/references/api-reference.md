# Model Inference API Reference

This reference summarizes the SaProt inference APIs used by this sub-skill. Source evidence includes `README.md`, `model/saprot/base.py`, `model/saprot/saprot_foldseek_mutation_model.py`, `model/saprot/saprot_if_model.py`, `utils/esm_loader.py`, `utils/constants.py`, and the environment AST inspection report.

## Vocabulary and Sequence Format

- Amino-acid vocabulary: `A C D E F G H I K L M N P Q R S T V W Y #`.
- Foldseek 3Di vocabulary: `p y n w r q h g d l v t m f s a e i k c #`.
- SaProt structure-aware tokens are AA+3Di pairs, such as `M#`, `Ev`, `Vp`, `Qp`, and `L#`.
- `#` in the 3Di half represents masked or low-confidence structure. `#` in the amino-acid half is used as an amino-acid mask for mutation and inverse-folding operations.

## Hugging Face Loading

```python
from transformers import EsmTokenizer, EsmForMaskedLM

tokenizer = EsmTokenizer.from_pretrained(model_dir)
model = EsmForMaskedLM.from_pretrained(model_dir)
```

Use a local Hugging Face model directory, not a `.pt` file. Typical required directory assets include tokenizer files and model/config files such as `config.json` plus one of `pytorch_model.bin`, `model.safetensors`, or sharded equivalents.

## `utils.esm_loader.load_esm_saprot`

```python
from utils.esm_loader import load_esm_saprot

model, alphabet = load_esm_saprot(pt_path)
```

- Input: local `.pt` checkpoint path.
- Requires: `torch` and `fair-esm` importable as `esm`.
- Checkpoint expectation: `torch.load(path)` returns a mapping with `model` weights and `config` entries.
- Return: an ESM2 model and a SaProt alphabet built from all amino-acid and Foldseek-token combinations.

## `SaprotBaseModel`

Constructor:

```python
SaprotBaseModel(
    task,
    config_path,
    extra_config=None,
    load_pretrained=False,
    freeze_backbone=False,
    use_lora=False,
    lora_config_path=None,
    **kwargs,
)
```

- `task` must be one of `classification`, `regression`, `lm`, or `base`.
- `config_path` is a local Hugging Face model directory used by `EsmConfig`, `EsmTokenizer`, and model loading.
- `load_pretrained=True` loads weights from the local directory; `False` initializes from config only.
- `freeze_backbone=True` sets `requires_grad=False` on the ESM backbone.
- `use_lora=True` requires `peft`; with `lora_config_path`, it loads and merges an inference LoRA adapter.

Embedding method:

```python
hidden_states = model.get_hidden_states(inputs, reduction=None)
mean_embeddings = model.get_hidden_states(inputs, reduction="mean")
```

- `inputs` is the tokenizer output dictionary moved to the same device as the model.
- The method adds `output_hidden_states=True` and calls `self.model.esm(**inputs)`.
- The method finds the first EOS token and removes special tokens from the returned representations.
- `reduction=None` returns per-token tensors of shape `[L, D]` per sequence.
- `reduction="mean"` returns one mean tensor of shape `[D]` per sequence.

## `SaprotFoldseekMutationModel`

Constructor:

```python
SaprotFoldseekMutationModel(
    foldseek_path,
    plddt_threshold=0.0,
    mask_rate=None,
    substitute_rate=None,
    MSA_log_path=None,
    log_clinvar=False,
    log_dir=None,
    **kwargs,
)
```

Common inference configuration:

```python
model = SaprotFoldseekMutationModel(
    foldseek_path=None,
    config_path=model_dir,
    load_pretrained=True,
)
```

- The constructor forwards `task="lm"` to `SaprotBaseModel`.
- `foldseek_path` is needed for methods that derive structure tokens from structure content. It is not needed for direct `predict_mut`, `predict_pos_mut`, or `predict_pos_prob` calls when a combined AA+3Di sequence is already supplied.
- `MSA_log_path` optionally mixes MSA log priors into the forward scoring path, but the direct helper methods score from the model probabilities.

Mutation helpers:

```python
score = model.predict_mut(seq, "V3A")
combo_score = model.predict_mut(seq, "V3A:Q4M")
all_effects = model.predict_pos_mut(seq, 3)
all_probs = model.predict_pos_prob(seq, 3)
```

- `seq` is the wild-type combined sequence.
- Positions are 1-indexed amino-acid positions.
- `predict_mut` returns one summed log-ratio effect as `float`.
- `predict_pos_mut` returns a dictionary keyed like `V3A`, with log-ratio effects for all amino acids.
- `predict_pos_prob` returns a dictionary keyed by amino-acid letters, with probabilities for all amino acids at the masked position.
- Internally these helpers mask the selected token by replacing the amino-acid half with `#` while preserving the structure half.

## `SaProtIFModel`

Constructor:

```python
SaProtIFModel(config_path=model_dir, load_pretrained=True)
```

Prediction method:

```python
predicted_sequences = model.predict(
    aa_seq,
    struc_seq,
    method="argmax",
    num_samples=1,
)
```

- `aa_seq` and `struc_seq` must have equal length.
- Use `#` in `aa_seq` for masked amino-acid positions to predict.
- `struc_seq` is the Foldseek 3Di sequence, not a combined AA+3Di string.
- `method` must be `argmax` or `multinomial`.
- `num_samples` must be `1` for `argmax`; multiple samples are supported only with `multinomial`.
- Return value is a list of predicted amino-acid sequences.

## Dependency Map

- `torch`: required for all model execution paths.
- `transformers`: required for Hugging Face tokenizer/model loading and `SaprotBaseModel`.
- `fair-esm`: required for `utils.esm_loader.load_esm_saprot`.
- `peft`: required only for LoRA loading or setup.
- `torchmetrics` and Lightning-related dependencies may be imported by repository model classes even when only inference helpers are used.
