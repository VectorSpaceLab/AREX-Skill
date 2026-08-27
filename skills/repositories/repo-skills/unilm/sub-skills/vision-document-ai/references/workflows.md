# Vision And Document Workflows

Use this reference to translate a user request into safe UniLM command plans. The command examples are templates distilled from repository evidence; they are not guaranteed to run without the matching source checkout, dependencies, data, and checkpoints. Prefer the bundled `scripts/build_vision_doc_command.py` helper to generate a clean starting command.

## Safety Checklist Before Native Runs

- Confirm the user wants to run heavy training/evaluation, not only build a plan.
- Confirm GPU count, CUDA version, Torch version, and whether the workflow requires Detectron2, MMCV, Apex, fairseq, Deepspeed, or Hugging Face Transformers.
- Confirm dataset layout and size before launching: ImageNet, ADE20K, PubLayNet, ICDAR, VQAv2, COCO, Flickr30k, and RVL-CDIP are large or access-controlled.
- Confirm checkpoints/tokenizers exist locally or that the user approves downloads. Do not silently download model weights or datasets.
- For distributed templates, start with `--nproc_per_node=1` only for smoke checks if the script supports it; preserve multi-GPU schedules for real reproduction plans.
- Keep outputs in user-selected directories and avoid overwriting non-empty training directories unless the command explicitly includes a safe overwrite flag.

## BEiT Image Classification

Choose this for ImageNet-style image classification with BEiT or BEiT v2. Input data should look like:

```text
DATA_ROOT/
  train/
    class_a/*.jpg
    class_b/*.jpg
  val/
    class_a/*.jpg
    class_b/*.jpg
```

Template:

```bash
OMP_NUM_THREADS=1 python -m torch.distributed.launch --nproc_per_node=<GPUS> run_class_finetuning.py \
  --model <beit_base_patch16_224|beit_large_patch16_224|beit_base_patch16_384|beit_large_patch16_384> \
  --data_path <DATA_ROOT> \
  --finetune <CHECKPOINT_OR_URL> \
  --output_dir <OUTPUT_DIR> \
  --batch_size <PER_GPU_BATCH> \
  --lr <LR> \
  --update_freq <GRAD_ACCUM_STEPS> \
  --warmup_epochs <WARMUP_EPOCHS> \
  --epochs <EPOCHS> \
  --layer_decay <LAYER_DECAY> \
  --drop_path <DROP_PATH> \
  --weight_decay <WEIGHT_DECAY> \
  --enable_deepspeed
```

Practical defaults from evidence:

- BEiT-large 224 fine-tuning used 8 GPUs, `--batch_size 32`, `--lr 2e-5`, `--update_freq 2`, `--epochs 30`, `--layer_decay 0.9`, `--drop_path 0.4`, and `--weight_decay 1e-8` for an intermediate ImageNet-22k fine-tuned checkpoint.
- BEiT-base 224 used `--batch_size 64`, `--lr 2e-5`, `--update_freq 1`, `--layer_decay 0.85`, and `--drop_path 0.1`.
- For 384 or 512 resolution, set `--input_size` and choose a matching model name.
- Effective batch size equals GPUs × per-GPU batch × update frequency.

Validation notes:

- Ensure `train/` and `val/` are both present and class names are consistent.
- Evaluation adds `--eval` and typically uses `--resume <FINETUNED_CHECKPOINT>` instead of `--finetune` for BEiT v1.
- Deepspeed enables Apex O2 behavior in these legacy scripts; if Deepspeed/Apex is unavailable, remove `--enable_deepspeed` only after checking whether native code supports torch AMP fallback.

## BEiT And BEiT v2 Pretraining

Choose this for masked image modeling or VQ-KD tokenizer work, not ordinary fine-tuning. These are large distributed jobs.

BEiT v1 pretraining shape:

```bash
OMP_NUM_THREADS=1 python -m torch.distributed.launch --nproc_per_node=<GPUS> run_beit_pretraining.py \
  --data_path <IMAGE_FOLDER_TRAIN> \
  --output_dir <OUTPUT_DIR> \
  --num_mask_patches 75 \
  --model beit_base_patch16_224_8k_vocab \
  --discrete_vae_weight_path <TOKENIZER_DIR_OR_WEIGHT> \
  --batch_size <PER_GPU_BATCH> \
  --lr <LR> \
  --warmup_epochs <WARMUP_EPOCHS> \
  --epochs <EPOCHS> \
  --clip_grad 3.0 \
  --drop_path 0.1 \
  --layer_scale_init_value 0.1
```

BEiT v2 pretraining shape:

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> run_beitv2_pretraining.py \
  --data_set image_folder \
  --data_path <IMAGE_FOLDER_TRAIN> \
  --output_dir <OUTPUT_DIR> \
  --log_dir <OUTPUT_DIR> \
  --model <beit_base_patch16_224_8k_vocab_cls_pt|beit_large_patch16_224_8k_vocab_cls_pt> \
  --shared_lm_head True \
  --early_layers <9_FOR_BASE_OR_21_FOR_LARGE> \
  --head_layers 2 \
  --num_mask_patches 75 \
  --second_input_size 224 \
  --second_interpolation bicubic \
  --min_crop_scale 0.2 \
  --tokenizer_model vqkd_encoder_base_decoder_3x768x12_clip \
  --tokenizer_weight <VQKD_WEIGHT> \
  --batch_size <PER_GPU_BATCH> \
  --lr 1.5e-3 \
  --warmup_epochs 10 \
  --clip_grad 3.0 \
  --drop_path 0.1 \
  --layer_scale_init_value <0.1_BASE_OR_1e-5_LARGE> \
  --imagenet_default_mean_and_std \
  --epochs <EPOCHS>
```

VQ-KD tokenizer training shape:

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> run_vqkd_training.py \
  --data_set image_folder \
  --data_path <TRAIN_IMAGES> \
  --eval_data_path <EVAL_IMAGES> \
  --output_dir <OUTPUT_DIR> \
  --log_dir <OUTPUT_DIR> \
  --model vqkd_encoder_base_decoder_3x768x12_clip \
  --teacher_input_size 224 \
  --codebook_n_emd 8192 \
  --codebook_emd_dim 32 \
  --quantize_kmeans_init \
  --rec_loss_type cosine \
  --batch_size 64 \
  --opt adamw \
  --warmup_epochs 10 \
  --epochs 100
```

## BEiT Semantic Segmentation

Choose this for ADE20K semantic segmentation. It uses mmsegmentation/OpenMMLab style commands, not `run_class_finetuning.py`.

Training shape:

```bash
bash tools/dist_train.sh <CONFIG_PATH> <NUM_GPUS> \
  --work-dir <OUTPUT_DIR> \
  --seed 0 \
  --deterministic \
  --options model.pretrained=<IMAGENET_CHECKPOINT_OR_URL>
```

Evaluation shape:

```bash
bash tools/dist_test.sh <CONFIG_PATH> <CHECKPOINT_PATH_OR_URL> <NUM_GPUS> --eval mIoU
```

Observed BEiT v2 configs include UPerNet base/large 512 slide configs, while BEiT v1 used 640 crop variants. Confirm the config path exists in the working source copy before running.

## BEiT-3 Fine-Tuning And Evaluation

Use BEiT-3 for image classification plus vision-language tasks through `run_beit3_finetuning.py`.

General training shape:

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> run_beit3_finetuning.py \
  --model <MODEL_NAME> \
  --input_size <224|384|480|768> \
  --task <imagenet|vqav2|nlvr2|coco_captioning|nocaps|coco_retrieval|flickr30k> \
  --batch_size <PER_GPU_BATCH> \
  --layer_decay <LAYER_DECAY> \
  --lr <LR> \
  --epochs <EPOCHS> \
  --warmup_epochs <WARMUP_EPOCHS> \
  --drop_path <DROP_PATH> \
  --sentencepiece_model <BEIT3_SPM> \
  --finetune <PRETRAINED_OR_FINETUNED_CHECKPOINT> \
  --data_path <DATA_ROOT> \
  --output_dir <OUTPUT_DIR> \
  --log_dir <LOG_DIR> \
  --weight_decay <WEIGHT_DECAY> \
  --seed 42 \
  --save_ckpt_freq 5 \
  --enable_deepspeed
```

Task-specific notes:

- `imagenet`: use `beit3_base_patch16_224` or `beit3_large_patch16_224`, `--task imagenet`, often `--mixup 0.8 --cutmix 1.0 --dist_eval`.
- `vqav2`: use `*_patch16_480`, `--input_size 480`, `--task_head_lr_weight 20`, and VQA question/annotation/images layout.
- `nlvr2`: use `*_patch16_224`, signed NLVR2 images plus generated index JSONs.
- `coco_captioning` and `nocaps`: use `*_patch16_480`, `--num_max_bpe_tokens 32`, `--captioning_mask_prob`, and caption index files.
- `coco_retrieval` and `flickr30k`: use `*_patch16_384`, ITC checkpoints, retrieval index files, and optionally gradient checkpointing.
- Evaluation adds `--eval`; distributed evaluation adds `--dist_eval`.

Dataset index generation in BEiT-3 docs uses Python calls in the local datasets package. Do not assume these index files exist just because raw images exist.

## DiT Classification And Detection

### RVL-CDIP Classification

Use DiT classification for document image classes, not natural ImageNet. The native command resembles BEiT classification:

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> run_class_finetuning.py \
  --model <beit_base_patch16_224|beit_large_patch16_224> \
  --data_path <RVL_CDIP_ROOT> \
  --eval_data_path <RVL_CDIP_ROOT> \
  --nb_classes 16 \
  --data_set rvlcdip \
  --finetune <DIT_CHECKPOINT> \
  --output_dir <OUTPUT_DIR> \
  --log_dir <OUTPUT_DIR>/tf \
  --batch_size <PER_GPU_BATCH> \
  --abs_pos_emb \
  --disable_rel_pos_bias
```

Add `--eval` for evaluation. Training adds learning-rate, epochs, warmup, layer decay, drop path, weight decay, and clip-grad flags.

### Document Layout Or Text Detection

Use DiT detection for PubLayNet, ICDAR cTDaR, and FUNSD text detection. It requires Detectron2 and matching configs/checkpoints.

Inference shape:

```bash
python inference.py \
  --image_path <IMAGE_PATH> \
  --output_file_name <OUTPUT_IMAGE> \
  --config <CONFIG_YAML> \
  --opts MODEL.WEIGHTS <CHECKPOINT_OR_URL>
```

Evaluation/training shape:

```bash
python train_net.py \
  --config-file <CONFIG_YAML> \
  --eval-only \
  --num-gpus <GPUS> \
  MODEL.WEIGHTS <CHECKPOINT_OR_URL> \
  OUTPUT_DIR <OUTPUT_DIR>
```

Remove `--eval-only` to train. For ICDAR archival detection, the evidence describes an adaptive binarization preprocessing step before linking data; do not skip that when reproducing archival scores.

## LayoutLM And LayoutLMv3 Form Understanding

### LayoutLM / LayoutLMv2 FUNSD

Use `layoutlmft/examples/run_funsd.py` for older LayoutLM and LayoutLMv2 workflows:

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> examples/run_funsd.py \
  --model_name_or_path <microsoft/layoutlm-base-uncased|microsoft/layoutlmv2-base-uncased> \
  --output_dir <OUTPUT_DIR> \
  --do_train \
  --do_predict \
  --max_steps 1000 \
  --warmup_ratio 0.1 \
  --fp16
```

LayoutLM cased uses a different tokenizer family than uncased. Confirm fast tokenizer availability before training.

### LayoutLMv3 FUNSD/CORD

Use this for English form or receipt token classification with visual embeddings:

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> --master_port <PORT> examples/run_funsd_cord.py \
  --dataset_name <funsd|cord> \
  --do_train --do_eval \
  --model_name_or_path <MODEL_OR_CHECKPOINT> \
  --output_dir <OUTPUT_DIR> \
  --segment_level_layout 1 \
  --visual_embed 1 \
  --input_size 224 \
  --max_steps 1000 \
  --save_steps -1 \
  --evaluation_strategy steps \
  --eval_steps <EVAL_STEPS> \
  --learning_rate <LR> \
  --per_device_train_batch_size <BATCH> \
  --gradient_accumulation_steps <STEPS> \
  --dataloader_num_workers <WORKERS>
```

Data/schema checks:

- FUNSD/CORD examples rely on dataset loader scripts with columns such as words/tokens, NER tags, bounding boxes, and images.
- `--segment_level_layout 1`, `--visual_embed 1`, and `--input_size 224` are central LayoutLMv3 visual/layout flags.
- A fast tokenizer is required by the source script.
- Existing non-empty output directories cause checkpoint/resume checks; use a fresh output or explicit overwrite only when intended.

### LayoutLMv3 XFUND

Use this for multilingual XFUND token classification:

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> --master_port <PORT> examples/run_xfund.py \
  --data_dir <XFUND_DATA_DIR> \
  --language <zh|ja|es|fr|it|de|pt> \
  --do_train --do_eval \
  --model_name_or_path <microsoft/layoutlmv3-base-chinese|CHECKPOINT> \
  --output_dir <OUTPUT_DIR> \
  --segment_level_layout 1 \
  --visual_embed 1 \
  --input_size 224 \
  --max_steps 1000 \
  --save_steps -1 \
  --evaluation_strategy steps \
  --eval_steps <EVAL_STEPS> \
  --learning_rate <LR> \
  --per_device_train_batch_size <BATCH> \
  --gradient_accumulation_steps <STEPS> \
  --dataloader_num_workers <WORKERS>
```

XFUND layout should include language JSON files such as `<lang>.train.json`, `<lang>.val.json`, and an `images/` directory with matching image filenames.

### LayoutXLM XFUND SER/RE

Use LayoutXLM when the request explicitly mentions older LayoutXLM or relation extraction in XFUND:

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> examples/run_xfun_ser.py \
  --model_name_or_path microsoft/layoutxlm-base \
  --output_dir <OUTPUT_DIR> \
  --do_train --do_eval \
  --lang <LANG> \
  --max_steps 1000 \
  --warmup_ratio 0.1 \
  --fp16
```

```bash
python -m torch.distributed.launch --nproc_per_node=<GPUS> examples/run_xfun_re.py \
  --model_name_or_path microsoft/layoutxlm-base \
  --output_dir <OUTPUT_DIR> \
  --do_train --do_eval \
  --lang <LANG> \
  --max_steps 2500 \
  --per_device_train_batch_size 2 \
  --warmup_ratio 0.1 \
  --fp16
```

## MarkupLM Webpage Understanding

Use MarkupLM for text plus DOM/XPath workflows.

WebSRC flow:

1. Download WebSRC and split metadata with user approval.
2. Generate dataset JSONs:

```bash
python dataset_generation.py --root_dir <WEBSRC_ROOT> --version websrc1.0
```

3. Fine-tune/evaluate:

```bash
CUDA_VISIBLE_DEVICES=<GPU_IDS> python run.py \
  --train_file <WEBSRC_ROOT>/websrc1.0_train_.json \
  --predict_file <WEBSRC_ROOT>/websrc1.0_dev_.json \
  --root_dir <WEBSRC_ROOT> \
  --model_name_or_path microsoft/markuplm-large \
  --output_dir <OUTPUT_DIR> \
  --do_train \
  --do_eval \
  --eval_all_checkpoints \
  --per_gpu_train_batch_size 8 \
  --warmup_ratio 0.1 \
  --num_train_epochs 5
```

SWDE flow uses `pack_data.py` and `prepare_data.py` before running vertical-specific `run.py` with `--vertical`, `--n_seed`, and `--n_pages`.

## XDoc Cross-Format Workflows

Use XDoc when the task spans plain text, scanned documents, and webpages through one model family.

- SQuAD uses Hugging Face QA flags such as `--dataset_name squad` or `squad_v2`, `--max_seq_length 384`, and `--doc_stride 128`.
- FUNSD uses distributed `run_funsd.py` and requires Detectron2 for visual components.
- WebSRC uses manually downloaded data and web arguments in its fine-tuning folder.
- The XDoc source warns that each downstream folder may require different Transformers versions; do not combine requirements blindly.

## TrOCR OCR

Use TrOCR when the output should be recognized text from image crops or line/word images. If the user starts from full document pages, consider DiT/LayoutLMv3 detection first to produce regions.

Native inference shape, distilled from `pic_inference.py`:

```bash
python pic_inference.py \
  --model_path <TROCR_FAIRSEQ_CHECKPOINT> \
  --image_path <IMAGE_PATH> \
  --beam <BEAM>
```

The original script hardcodes placeholder paths, so adapt it before native use. A safe adaptation should expose `--model_path`, `--image_path`, `--beam`, and `--device`, then perform these steps: load fairseq model ensemble and task, resize RGB image to 384×384, normalize with mean/std 0.5, run text-recognition generation, decode BPE output, and print text.

Training/evaluation paths use `fairseq-train` and `fairseq-generate` with task `text_recognition`, `--data-type STR|SROIE|Receipt53K`, `--input-size 384`, BPE/dictionary flags, and checkpoint paths.

## VLMo Data Conversion And Runs

Use VLMo for vision-language pretraining/fine-tuning with pyarrow data.

Data conversion assumptions:

- GCC/SBU: image URL/caption pairs, many URLs may be inaccessible; user-owned download scripts are needed.
- VG: `images/VG_100K`, `images/VG_100K_2`, and `annotations/region_descriptions.json`.
- COCO: `train2014`, `val2014`, and Karpathy split JSON.
- Flickr30k: `flickr30k-images` plus Karpathy split JSON.
- VQAv2: COCO images, VQA questions, and annotations.
- NLVR2: signed image access plus NLVR/NLVR2 repo data.

Run shape:

```bash
python run.py with \
  data_root=<ARROW_ROOT> \
  num_gpus=<NUM_GPUS> \
  num_nodes=<NUM_NODES> \
  <CONFIG_NAME> \
  per_gpu_batchsize=<BATCH_THAT_FITS> \
  load_path=<VLMO_WEIGHT> \
  log_dir=<OUTPUT_DIR>
```

Evaluation shape:

```bash
python run.py with \
  data_root=<ARROW_ROOT> \
  num_gpus=<NUM_GPUS> \
  num_nodes=1 \
  <CONFIG_NAME> \
  per_gpu_batchsize=<BATCH_THAT_FITS> \
  load_path=<FINETUNED_VLMO_WEIGHT> \
  test_only=True
```

Add `get_recall_metric=True` for COCO/Flickr retrieval evaluation.

Common config names from evidence:

- VQA: `task_finetune_vqa_base_image480`, `task_finetune_vqa_base_plus_image480`, `task_finetune_vqa_large_image480`.
- NLVR2: `task_finetune_nlvr2_base_image384`, `task_finetune_nlvr2_base_plus_image384`, `task_finetune_nlvr2_large_image384`.
- COCO retrieval: `task_finetune_irtr_coco_base_image384`, `task_finetune_irtr_coco_base_plus_image384`, `task_finetune_irtr_coco_large_image384`.
- Flickr30k retrieval: `task_finetune_irtr_f30k_base_image384`, `task_finetune_irtr_f30k_base_plus_image384`, `task_finetune_irtr_f30k_large_image384`.
- Pretraining examples use `task_textmlm_base` and `task_mlm_itm_itc_base` with `whole_word_masking=True` and schedule flags such as `step200k`.

## Source Script Bundling Decisions

- `beit/run_class_finetuning.py`, `beit/run_beit_pretraining.py`, `beit2/run_class_finetuning.py`, `beit2/run_beitv2_pretraining.py`, `beit2/run_vqkd_training.py`, `beit3/run_beit3_finetuning.py`, `layoutlmv3/examples/run_funsd_cord.py`, `layoutlmv3/examples/run_xfund.py`, `trocr/pic_inference.py`, and `vlmo/run.py` are reference-only because they require heavy source trees, data, checkpoints, and backend stacks.
- The bundled `scripts/build_vision_doc_command.py` wraps command planning for common tasks without importing native packages, training, downloading, or reading image/model files.
- If a future agent needs runnable TrOCR single-image inference, adapt the small `pic_inference.py` logic into a separate bundled script only after deciding target fairseq version and CLI arguments; do not copy the hardcoded source script as-is.
