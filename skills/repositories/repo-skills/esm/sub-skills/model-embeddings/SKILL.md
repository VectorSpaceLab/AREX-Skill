---
name: model-embeddings
description: "Load ESM/ESM-2/MSA Transformer models, tokenize protein inputs,
  compute representations or contacts, and build bulk FASTA embedding extraction
  commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Embeddings

Use this sub-skill when an agent needs embeddings, logits, or unsupervised contact maps from ESM, ESM-2, ESM-1/1b/1v, or MSA Transformer language models. It covers Python APIs for model loading and tokenization plus the `esm-extract` bulk FASTA CLI.

Do not use this sub-skill for structure prediction, inverse folding, or mutation-effect scoring. Route those tasks to sibling sub-skills instead:

- Structure prediction / ESMFold PDB output: `../structure-prediction/SKILL.md`
- Inverse folding / ESM-IF1 design and structure-conditioned scoring: `../inverse-folding/SKILL.md`
- DMS or zero-shot mutation scoring: `../variant-effect-prediction/SKILL.md`

## Start Here

1. For Python model loading, tokenization, layer selection, output tensors, and MSA shapes, read [references/api-reference.md](references/api-reference.md).
2. For common embedding/contact workflows and safe model choices, read [references/workflows.md](references/workflows.md).
3. For bulk FASTA extraction, `.pt` contents, truncation, CPU/GPU flags, and command construction, read [references/cli-reference.md](references/cli-reference.md).
4. For large ESM-2 15B inference with Fairscale FSDP CPU offload, read [references/fsdp-offloading.md](references/fsdp-offloading.md).
5. For failures such as bad model names, download issues, MSA misuse, duplicate FASTA labels, layer errors, and OOM, read [references/troubleshooting.md](references/troubleshooting.md).

## Bundled Helper

Use the safe command builder when constructing a reproducible `esm-extract` invocation without triggering model downloads:

```bash
python sub-skills/model-embeddings/scripts/esm_extract_command_builder.py \
  esm2_t33_650M_UR50D input.fasta embeddings_out \
  --repr-layers -1 --include mean contacts --nogpu --print-only
```

The helper validates that the FASTA exists, checks extraction options, warns about unsupported MSA Transformer model names, and prints a shell-quoted command by default. It does not import `esm` or load model weights for `--help` or `--print-only`.

## Quick Decisions

- Use `esm.pretrained.load_model_and_alphabet(name)` or a specific `esm.pretrained.<model>()` function for Python embeddings.
- Use `alphabet.get_batch_converter(truncation_seq_length=...)` for single-sequence models and MSA models; MSA alphabets return `MSABatchConverter` automatically.
- Use `model(tokens, repr_layers=[...], return_contacts=True)` for hidden representations plus contact maps.
- Use `esm-extract` only for single-sequence models; MSA Transformer requires Python API input shaped as a batch of MSAs.
- Force CPU with `--nogpu` in `esm-extract` or by keeping tensors/model on CPU in Python; expect slow inference for large models.
