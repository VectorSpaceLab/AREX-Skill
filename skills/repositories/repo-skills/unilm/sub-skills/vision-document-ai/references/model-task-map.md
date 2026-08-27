# Model And Task Map

This map distills the UniLM umbrella repository's vision, vision-language, webpage, OCR, and document-AI families into self-contained routing guidance. Original repository files are evidence only; use bundled references and helper scripts before running heavyweight native programs.

## Quick Routing Matrix

| Request | Prefer | Typical task names | Native entry point class | Data/checkpoint assumptions | Route away when |
|---|---|---|---|---|---|
| ImageNet image classification or masked image modeling | BEiT / BEiT v2 / BEiT-3 | `imagenet`, BEiT pretraining, VQ-KD tokenizer | `run_class_finetuning.py`, `run_beit_pretraining.py`, `run_beitv2_pretraining.py`, `run_vqkd_training.py` | ImageFolder `train/` and `val/`, ImageNet-style classes, pretrained `.pth`, optional tokenizer weight | Task is text retrieval, text generation, or generic architecture training |
| ADE20K semantic segmentation | BEiT / BEiT v2 segmentation | UPerNet on ADE20K | mmseg `tools/dist_train.sh` / `tools/dist_test.sh` style command | mmcv-full/mmsegmentation stack, ADE20K prepared per mmseg, pretrained BEiT checkpoint | Task is document layout detection, use DiT/LayoutLMv3 instead |
| BEiT-3 vision-language downstream | BEiT-3 | `imagenet`, `vqav2`, `nlvr2`, `coco_captioning`, `nocaps`, `coco_retrieval`, `flickr30k` | `run_beit3_finetuning.py` | `beit3.spm`, model checkpoint, task-specific index files, image folders and annotations | Request asks for pure E5/SimLM retrieval or generation outside BEiT-3 captioning |
| Document image classification | DiT | RVL-CDIP | DiT classification `run_class_finetuning.py` | RVL-CDIP extracted, 16 classes, DiT `.pth`, `--abs_pos_emb --disable_rel_pos_bias` | Need form token labels or key-value extraction; use LayoutLM/LayoutLMv3 |
| Document layout/table/text detection | DiT / LayoutLMv3 object detection | PubLayNet, ICDAR cTDaR, FUNSD text detection | Detectron2 `train_net.py`, inference script patterns | Matching YAML and checkpoint, Detectron2 built for exact Torch/CUDA, COCO-format data or symlinks | Need OCR transcription; use TrOCR |
| Form or receipt understanding | LayoutLM, LayoutLMv2, LayoutLMv3 | FUNSD, CORD, SROIE | `layoutlmft/examples/run_funsd.py`, `layoutlmv3/examples/run_funsd_cord.py` | Words/tokens, labels, bounding boxes, document images; visual flags for v3 | Need multilingual XFUND; use LayoutXLM/LayoutLMv3 Chinese route |
| Multilingual form understanding and relation extraction | LayoutXLM / LayoutLMv3 | XFUND SER, XFUND RE | `run_xfun_ser.py`, `run_xfun_re.py`, `layoutlmv3/examples/run_xfund.py` | Language code, `*.train.json`/`*.val.json`, images, bounding boxes | Need English-only CORD/FUNSD; use LayoutLMv3 FUNSD/CORD |
| Webpage QA and webpage information extraction | MarkupLM / XDoc | WebSRC, SWDE | MarkupLM `run.py`, dataset generation scripts, XDoc WebSRC runner | HTML/DOM root, XPath features, generated JSON or pickle artifacts | Need document images with boxes; use LayoutLM family |
| Cross-format document understanding | XDoc | SQuAD, FUNSD, WebSRC | XDoc fine-tuning runners | Task-specific requirements; may use different Transformers versions per downstream task | Need model-family-specific LayoutLMv3 flags or BEiT image tasks |
| OCR transcription | TrOCR | IAM, SROIE, STR, single image inference | fairseq train/generate, `pic_inference.py` style | fairseq user-dir, checkpoint, image(s), BPE/dict settings, CUDA optional for inference | Need layout regions or boxes first; use DiT/LayoutLMv3 detection route |
| Vision-language pretraining/fine-tuning with pyarrow data | VLMo | VQA, NLVR2, COCO/Flickr retrieval, MLM/ITM/ITC | Sacred-style `python run.py with ...` | Arrow data root, config name, VLMo checkpoint, PyTorch Lightning stack | Need BEiT-3 finetuning rather than VLMo configs |
| VL-BEiT mention or generative vision-language pretraining | VL-BEiT | generative VL pretraining evidence | README-level evidence only in this checkout | Only a release note was present in the inspected checkout | Route deeper generation requests to `multimodal-generation` unless tied to BEiT evidence |

## Family Notes

### BEiT And BEiT v2

- BEiT v1 targets masked image modeling and image classification/segmentation using old PyTorch/Timm/Apex-era code. Its image classification fine-tuning expects ImageFolder with `train/` and `val/` directories.
- BEiT pretraining requires a discrete VAE/tokenizer asset and distributed launch. Key flags include `--num_mask_patches`, `--discrete_vae_weight_path`, `--batch_size`, `--lr`, `--warmup_steps` or `--warmup_epochs`, `--epochs`, `--clip_grad`, `--drop_path`, and `--layer_scale_init_value`.
- BEiT v2 adds VQ-KD visual tokenizer training and pretraining through `run_beitv2_pretraining.py`; key tokenizer flags include `--tokenizer_model vqkd_encoder_base_decoder_3x768x12_clip` and `--tokenizer_weight`.
- BEiT and BEiT v2 ADE20K segmentation use OpenMMLab/mmsegmentation command shapes (`tools/dist_train.sh <CONFIG_PATH> <NUM_GPUS> ... --options model.pretrained=<checkpoint>`), not the image classification runner.

### BEiT-3

- BEiT-3 covers both image-only and vision-language downstream tasks through one `run_beit3_finetuning.py` runner.
- Supported task choices observed in source are `nlvr2`, `vqav2`, `flickr30k`, `coco_retrieval`, `coco_captioning`, `nocaps`, and `imagenet`.
- The runner requires `--sentencepiece_model` for all tasks, even image-centric templates in the docs.
- Use `BEiT3-base` or `BEiT3-large` for deep-fusion vision-language tasks; use `*-itc` checkpoints for retrieval when following the repo guidance.
- Higher-resolution VQA/captioning uses `--input_size 480` and model names such as `beit3_base_patch16_480`; retrieval commonly uses `--input_size 384`.

### DiT

- DiT is document-image oriented, not generic natural-image BEiT. It has classification, layout/table detection, and text-detection paths.
- Classification on RVL-CDIP uses 16 labels and BEiT-style `run_class_finetuning.py` with DiT checkpoints, `--abs_pos_emb`, and `--disable_rel_pos_bias`.
- Object and text detection use Detectron2. Commands must match the YAML config (`maskrcnn` vs `cascade`, base vs large, PubLayNet vs ICDAR/FUNSD text detection) with the checkpoint.
- Detectron2 wheels are tightly coupled to Torch and CUDA; do not recommend broad upgrades as a first fix.

### LayoutLM Family

- LayoutLM and LayoutLMv2 use `layoutlmft` for form understanding and key-value extraction, with examples like `examples/run_funsd.py`.
- LayoutLMv3 adds unified text/image masking and visual embedding flags. For FUNSD/CORD, `examples/run_funsd_cord.py` accepts `--dataset_name funsd` or `--dataset_name cord`, plus `--segment_level_layout 1 --visual_embed 1 --input_size 224`.
- LayoutLMv3 XFUND uses `examples/run_xfund.py`, `--data_dir`, `--language`, and the same visual/layout flags.
- LayoutXLM is the multilingual form-understanding route for XFUND semantic entity recognition and relation extraction in older `layoutlmft` scripts.
- Document object detection under LayoutLMv3 reuses Detectron2-style `train_net.py` in the object detection examples; treat it like the DiT detection stack.

### MarkupLM And XDoc

- MarkupLM focuses on text plus markup language, especially WebSRC and SWDE. It uses generated dataset artifacts before running fine-tuning scripts.
- XDoc is a cross-format model spanning plain text, document images, and webpages. Its fine-tuning folders warn that different downstream tasks may require different Transformers versions.
- Route webpage extraction and WebSRC/SWDE to MarkupLM or XDoc; route scanned forms with OCR boxes to LayoutLM/LayoutLMv3.

### TrOCR

- TrOCR native code is fairseq-based and includes training/evaluation commands for IAM, SROIE, and STR benchmarks.
- Single-image inference follows `pic_inference.py`: load a fairseq checkpoint, resize image to 384x384 RGB, normalize, run text-recognition task generation, and decode BPE output.
- The bundled command builder prints a safe inference planning template only; it does not import fairseq, load images, or load checkpoints.

### VLMo

- VLMo uses PyTorch Lightning plus Sacred configuration: `python run.py with data_root=<ARROW_ROOT> num_gpus=<NUM_GPUS> num_nodes=<NUM_NODES> <CONFIG_NAME> per_gpu_batchsize=<BATCH> load_path=<WEIGHT> log_dir=<OUT>`.
- The data root is expected to contain pyarrow conversions for GCC, SBU, VG, COCO, Flickr30k, VQAv2, NLVR2, or WikiBK generated from ViLT-style writer functions.
- Evaluation appends `test_only=True`; retrieval evaluation should also append `get_recall_metric=True`.

## Exclusions And Sibling Routes

- Text-only embedding retrieval (`e5`, `simlm`) belongs to `embeddings-retrieval`, even when the user says retrieval without images.
- TextDiffuser, Kosmos, audio models, LatentLM, and other generative multimodal systems belong to `multimodal-generation` unless the task is specifically BEiT-3 captioning or VLMo/BEiT vision-language fine-tuning.
- Generic distributed training setup, architecture configuration, or optimizer mechanics belongs to `architectures-training` when not tied to a concrete vision/document workflow here.
