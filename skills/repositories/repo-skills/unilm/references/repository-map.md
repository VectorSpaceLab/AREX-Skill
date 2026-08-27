# UniLM Repository Map

UniLM is an umbrella monorepo containing many research projects across language, retrieval, vision/document AI, multimodal generation, audio/speech, and architecture training. Use this map to route a request before opening deeper references.

## Routing Table

| User signal | Route | Typical evidence summarized |
| --- | --- | --- |
| UniLMv1, `biunilm`, `s2s-ft`, summarization, question generation, XSum, CNN/DM, Gigaword, MiniLM NLG, AdaLM, DeltaLM, InfoXLM, EdgeLM, XTune | `sub-skills/language-seq2seq/` | UniLM and s2s fine-tuning/decoding commands, JSONL/parallel text formats, legacy tokenizer/config/checkpoint guidance |
| E5, SimLM, BEIR, MTEB, MS MARCO, DPR/NQ, dense retrieval, reranking, hard negatives, teacher scores | `sub-skills/embeddings-retrieval/` | E5 model/prefix/pooling rules, BEIR/MTEB command planning, SimLM biencoder/reranker/RLM workflows |
| BEiT, BEiT-2, BEiT-3, DiT, LayoutLM, LayoutLMv2/v3, LayoutXLM, MarkupLM, XDoc, TrOCR, VLMo, VL-BEiT | `sub-skills/vision-document-ai/` | Vision/document task map, dataset layout expectations, command templates, backend troubleshooting |
| Kosmos, Kosmos-2.5, TextDiffuser, WavLM, BEATs, SpeechT5, SpeechLM, VALL-E, LatentLM | `sub-skills/multimodal-generation/` | Multimodal generation, literate OCR/markdown, text rendering, audio/speech, latent diffusion input checks |
| Diff-Transformer, YOCO, DeepNet, LongNet, LongViT, RetNet, X-MoE, BitNet, GAD/IAD, PFPO, ReSA | `sub-skills/architectures-training/` | Architecture module notes, distributed launch safety, long-context eval, decoding acceleration, offline math/eval alternatives |

## Evidence Categories

- Public documentation and READMEs identify project intent, model families, supported tasks, and published command examples.
- Source scripts identify native flags, required files, and side effects, but many are long-running or environment-specific.
- Tests/examples in this repository are mostly smoke, benchmark, or source-level evidence; safe final verification should use bundled helper checks and only run native scripts after explicit confirmation.
- Vendored/forked trees such as fairseq, open_clip, torchscale, and infinibatch are treated as evidence for native command shape, not copied into this skill.

## Environment Model

The umbrella repository has no single top-level installable package. Representative live inspection verified a lightweight AdaLM subproject, while legacy UniLMv1 and broader ML stacks were source-inspected because installing every optional dependency would require old PyTorch/Apex/fairseq/Detectron2/DeepSpeed stacks, downloads, and GPU-specific packages.

Use one narrow environment per selected workflow. For example, do not install Detectron2 just to plan E5 commands, and do not install old Apex just to inspect TextDiffuser arguments.
