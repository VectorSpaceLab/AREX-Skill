---
name: supervised-extraction
description: "Guide DeepKE supervised NER, RE, AE, EE, cnSchema, and
  scenario-specific extraction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepKE supervised extraction

Use this sub-skill when a task asks to train, predict with, configure, or troubleshoot DeepKE's classic supervised extraction workflows: named entity recognition (NER), relation extraction (RE), attribute extraction (AE), event extraction (EE), cnSchema off-the-shelf NER/RE, and the standard, few-shot, multimodal, document-level, or cross-domain variants.

## Route by intent

- **Choose the right task and scenario**: read [references/workflows.md](references/workflows.md) for task selection and end-to-end recipes.
- **Prepare or inspect input files and Hydra YAMLs**: read [references/data-and-config.md](references/data-and-config.md) for columns, split names, config knobs, checkpoint fields, and path-resolution caveats.
- **Pick a model family or import surface**: read [references/model-overview.md](references/model-overview.md) for the scenario/model table and DeepKE package layout.
- **Debug installation, model, dataset, GPU, or workflow failures**: read [references/troubleshooting.md](references/troubleshooting.md) before changing code or rerunning long training.
- **Check the local runtime safely**: run [scripts/check_supervised_env.py](scripts/check_supervised_env.py) to inspect installed imports, CUDA visibility, and optional data/checkpoint path expectations without training or downloading.

## Owns

- Standard NER with BERT, BiLSTM-CRF, and W2NER.
- Few-shot NER with LightNER-style prompt tuning and cross-domain NER with CP-NER-style prefix transfer.
- Multimodal NER and RE with text plus detected/grounded visual objects.
- Standard RE and AE with CNN/RNN/Capsule/GCN/Transformer/LM families.
- Few-shot RE, document-level RE, and cnSchema quick-load NER/RE.
- Standard EE trigger and role extraction pipelines, including the DEGREE-style variant as a reference-only path.

## Does not own

- Creating or converting datasets from annotation exports; use the sibling `data-preparation` sub-skill for conversion and weak/distant supervision helpers.
- PRGC, PURE, ASP, MT5, or other triple-extraction workflows; use the sibling `triple-extraction` sub-skill.
- DeepKE-LLM, instruction KGC, OpenAI/API workflows, or OneKE-style large-model inference; use the sibling `llm-workflows` sub-skill.
- MCP server/client deployment; use the sibling `mcp-tools` sub-skill.

## Quick operating pattern

1. Classify the request by task (`NER`, `RE`, `AE`, `EE`) and scenario (`standard`, `few-shot`, `multimodal`, `document`, `cross-domain`, `cnSchema`).
2. Confirm whether the user wants training, prediction, config diagnosis, or data validation.
3. Verify the environment with `scripts/check_supervised_env.py` when imports, CUDA, model files, or data layout are uncertain.
4. Read the workflow recipe and data/config reference for the selected scenario.
5. Treat long training, checkpoint downloads, GPU-only multimodal work, and DEGREE/EE variants as explicit resource-dependent operations; do not silently start them without user approval.
