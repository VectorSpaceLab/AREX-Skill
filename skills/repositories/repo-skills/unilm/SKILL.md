---
name: unilm
description: "Use the Microsoft UniLM umbrella repository for language
  generation, embeddings/retrieval, vision/document AI, multimodal generation,
  and architecture-training workflow planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# UniLM

Use this repo skill when a task involves the Microsoft UniLM umbrella repository or its model families: UniLM/UniLMv1, `s2s-ft`, MiniLM, AdaLM, DeltaLM, InfoXLM, E5, SimLM, BEiT, DiT, LayoutLM, MarkupLM, XDoc, TrOCR, VLMo, Kosmos, TextDiffuser, WavLM, BEATs, SpeechT5, SpeechLM, VALL-E, LatentLM, Diff-Transformer, YOCO, DeepNet, LongNet, RetNet, X-MoE, BitNet, PFPO, ReSA, or aggressive decoding.

This is a self-contained routing skill. It summarizes repository evidence and provides safe command builders/checkers, but it does not bundle the original monorepo, model weights, datasets, or heavyweight training stacks.

## Route By Task

- Use [language-seq2seq](sub-skills/language-seq2seq/SKILL.md) for UniLM/UniLMv1 and `s2s-ft` summarization, question generation, JSONL seq2seq training/decoding/evaluation, legacy tokenizer/checkpoint checks, MiniLM language generation, AdaLM, DeltaLM, InfoXLM, EdgeLM, LayoutReader, or XTune language workflows.
- Use [embeddings-retrieval](sub-skills/embeddings-retrieval/SKILL.md) for E5 embeddings, BEIR/MTEB evaluation, SimLM biencoder/reranker/RLM workflows, dense retrieval, hard-negative mining, and teacher-score generation.
- Use [vision-document-ai](sub-skills/vision-document-ai/SKILL.md) for BEiT/BEiT2/BEiT3, DiT, LayoutLM/LayoutLMv2/LayoutLMv3, LayoutXLM, MarkupLM, XDoc, TrOCR, VLMo, VL-BEiT, OCR, form understanding, document layout, image classification, segmentation, VQA, captioning, or vision-language tasks.
- Use [multimodal-generation](sub-skills/multimodal-generation/SKILL.md) for Kosmos/Kosmos-2.5, TextDiffuser/TextDiffuser-2, WavLM, BEATs, SpeechT5, SpeechLM, VALL-E, LatentLM, image/text generation, literate OCR/markdown, audio/speech workflows, and latent diffusion planning.
- Use [architectures-training](sub-skills/architectures-training/SKILL.md) for Diff-Transformer, YOCO, DeepNet, LongNet/LongViT, RetNet, X-MoE, BitNet, aggressive decoding, PFPO/ReSA math evaluation, distributed launch planning, long-context runs, and credential-safe offline alternatives.

## Shared References And Helper

- Read [references/repository-map.md](references/repository-map.md) to map project names, task families, and native evidence to the right sub-skill.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting installation, optional dependency, backend, data/checkpoint, network, credential, and source-checkout issues.
- Read [references/repo-provenance.md](references/repo-provenance.md) to check the source snapshot, dirty state, package facts, and evidence paths used to generate this skill.
- `references/repo-routing-metadata.json` contains structured scenario metadata used by the managed repo-skills router during import.
- Run [scripts/check_unilm_environment.py](scripts/check_unilm_environment.py) for a safe local environment preflight that checks Python, optional packages, GPU visibility, and provided data/checkpoint paths without importing heavyweight UniLM modules or downloading anything.

## Safe Default Workflow

1. Classify the user request by model family and task; use the route map above before reading detailed references.
2. Prefer bundled command builders and validators for planning: they print templates or check local inputs but do not run native training, decoding, downloads, credentialed services, or GPU jobs.
3. Confirm any required source checkout, model weights, dataset files, backend versions, GPU resources, and external credentials before proposing a native command.
4. Treat original UniLM repo scripts as evidence and command shapes, not as bundled runtime dependencies. If a command must be run, tell the user it needs a compatible source checkout and environment.
5. Avoid broad dependency installs. Many subprojects require old PyTorch/Apex/fairseq/Detectron2/DeepSpeed stacks or large downloads; install only the stack for the selected workflow.

## Important Boundaries

- This skill does not make model weights, datasets, external benchmark downloads, or legacy GPU stacks available.
- Do not run full training, distributed launches, BEIR/MTEB benchmarks, image/audio generation, or PFPO service callers unless the user explicitly approves and the runtime is prepared.
- Do not assume one Python environment can cover the whole umbrella monorepo. The generated skill was based on repository evidence plus a lightweight representative package inspection.
- Do not use source-repo paths as runtime links from this skill. Source evidence is summarized in bundled references and safe helper scripts.
