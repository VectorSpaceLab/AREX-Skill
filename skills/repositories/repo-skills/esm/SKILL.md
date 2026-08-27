---
name: esm
description: "Use the fair-esm repository skill for protein language-model
  embeddings, ESMFold structure prediction, ESM-IF1 inverse folding, and
  zero-shot variant-effect scoring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ESM

Use this repo skill when a task mentions ESM, fair-esm, ESM-2, ESMFold, ESM-IF1, ESM-1v, MSA Transformer, `esm-extract`, or `esm-fold`. It routes future agents to self-contained guidance for protein language-model workflows without depending on the original repository checkout.

## Quick Install Check

```bash
python -m pip install fair-esm
python - <<'PY'
import esm
print(esm.__version__)
print(esm.Alphabet.from_architecture("ESM-1b").mask_idx)
PY
```

For ESMFold and inverse folding, expect additional optional dependencies beyond base `fair-esm`. Read `references/troubleshooting.md` before mutating an environment.

## Route By Task

- Use [`model-embeddings`](sub-skills/model-embeddings/SKILL.md) for loading ESM/ESM-2/MSA Transformer models, tokenizing protein sequences/MSAs, computing logits, representations, contacts, and constructing `esm-extract` commands.
- Use [`structure-prediction`](sub-skills/structure-prediction/SKILL.md) for ESMFold sequence-to-PDB workflows, `esm-fold`, `model.infer_pdb`, PDB output, pLDDT/pTM confidence, chunking, recycles, CPU-only, and CPU offload.
- Use [`inverse-folding`](sub-skills/inverse-folding/SKILL.md) for ESM-IF1 fixed-backbone sequence sampling, structure-conditioned log-likelihood scoring, PDB/mmCIF coordinate extraction, single-chain/multichain conditioning, and encoder representations.
- Use [`variant-effect-prediction`](sub-skills/variant-effect-prediction/SKILL.md) for ESM-1v or MSA Transformer zero-shot DMS scoring with `wt-marginals`, `masked-marginals`, `pseudo-ppl`, mutation-offset validation, and A3M MSA inputs.

## Model Family Cheat Sheet

| User wording | Best route | Typical entry point |
| --- | --- | --- |
| embeddings, logits, contacts, `esm-extract`, ESM-2 | `model-embeddings` | `esm.pretrained.load_model_and_alphabet(...)`, `esm-extract` |
| fold a sequence, output PDB, ESMFold, pLDDT, pTM | `structure-prediction` | `esm.pretrained.esmfold_v1()`, `esm-fold` |
| inverse folding, design sequence from backbone, score sequence against PDB | `inverse-folding` | `esm.pretrained.esm_if1_gvp4_t16_142M_UR50()` |
| variant effect, DMS CSV, ESM-1v, MSA Transformer mutation scores | `variant-effect-prediction` | bundled variant helper and runner |

## Shared References

- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import, model download/cache, optional dependency, backend, CLI, and data issues.
- Read [`references/model-downloads-and-caches.md`](references/model-downloads-and-caches.md) before running workflows that download pretrained weights or use `--model-dir`.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) to decide whether this generated skill is stale relative to the source repository state.
- `references/repo-routing-metadata.json` is structured metadata for DisCo import and router generation.

## Safe Usage Defaults

1. Start with the smallest model that satisfies the task; use `esm2_t6_8M_UR50D` for smoke checks and command validation.
2. Treat model loading as a potential network/cache operation unless the weights are already available.
3. Use bundled command-builder helpers before running heavyweight CLIs; helpers default to printing commands or validating inputs.
4. Do not run native ESMFold, IF1, or DMS scoring on large inputs without confirming optional dependencies, device memory, and model-cache policy.
5. Keep public outputs reproducible: record model names, local checkpoint filenames when used, layer selections, input data schemas, offset numbering, chunk/recycle settings, and output paths.

## Bundled Root Helper

Use `scripts/check_esm_install.py` for safe import/signature checks that do not download weights:

```bash
python scripts/check_esm_install.py
```

It verifies base `esm` import, distribution metadata when available, public alphabet behavior, and whether optional inverse-folding/ESMFold imports are present.
