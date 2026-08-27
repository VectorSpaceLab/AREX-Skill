---
name: vision-document-ai
description: "Use UniLM vision, vision-language, OCR, webpage, and document-AI
  workflows across BEiT, DiT, LayoutLM, MarkupLM, XDoc, TrOCR, VLMo, and
  VL-BEiT."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Vision Document AI

Use this sub-skill when the task is about UniLM vision or document-AI models: image classification/pretraining, semantic segmentation, document layout/text detection, OCR, form understanding, token classification, relation extraction, visual question answering, captioning, retrieval, NLVR2, webpage extraction, or cross-format document understanding.

## Route Here

- Build or adapt command plans for BEiT, BEiT v2, BEiT-3, DiT, LayoutLM/LayoutLMv2/LayoutLMv3, LayoutXLM, MarkupLM, XDoc, TrOCR, VLMo, or VL-BEiT.
- Validate dataset assumptions for ImageFolder, ADE20K-style segmentation, FUNSD, CORD, XFUND, PubLayNet, ICDAR cTDaR, WebSRC, SWDE, SQuAD, COCO, Flickr30k, VQAv2, NLVR2, or pyarrow vision-language data.
- Diagnose vision/document dependency failures involving legacy PyTorch, CUDA wheels, Detectron2, MMCV/mmsegmentation, Apex, fairseq, Deepspeed, or Hugging Face Transformers drift.
- Choose among OCR, document layout, form extraction, webpage markup, image-only, and vision-language routes before constructing a command.

## Route Elsewhere

- Use `embeddings-retrieval` for E5, SimLM, dense retrieval, embedding indexing, or text-only retriever training.
- Use `multimodal-generation` for TextDiffuser, Kosmos, audio, LatentLM, image/text generation, or open-ended multimodal generation systems.
- Use `architectures-training` for architecture-only distributed training, generic TorchScale/Magneto/DeepNet wiring, optimizer schedules, or Deepspeed mechanics not tied to a vision/document task.

## Read Or Run

- Read [references/model-task-map.md](references/model-task-map.md) to pick the correct model family, task owner, native entry point class, dependency stack, and sibling route.
- Read [references/workflows.md](references/workflows.md) before building training, evaluation, data-conversion, OCR, or vision-language commands.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a dependency stack, dataset schema, checkpoint, tokenizer, bounding-box, OCR, or Hugging Face version error blocks progress.
- Run [scripts/build_vision_doc_command.py](scripts/build_vision_doc_command.py) to print safe command templates for BEiT classification, BEiT-3 tasks, LayoutLMv3 FUNSD/CORD/XFUND, DiT detection, TrOCR inference, or VLMo runs without training, downloading, or requiring model/data files.

## Safe Default Workflow

1. Classify the request by modality: image-only, document OCR/layout, form/entity extraction, webpage markup, cross-format document QA, or vision-language.
2. Use the model-task map to select the family and confirm whether the original workflow expects legacy PyTorch, Detectron2/MMCV, fairseq, Deepspeed, or Transformers.
3. Use the command builder for a template, then replace placeholders only after confirming data layout, checkpoint availability, GPU count, and backend versions.
4. Treat original UniLM training and inference programs as heavy reference entry points; do not run them until the user confirms environment, data, checkpoint, and hardware readiness.
