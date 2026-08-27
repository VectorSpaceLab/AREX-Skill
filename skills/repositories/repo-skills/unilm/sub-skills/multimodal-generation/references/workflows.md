# Multimodal Generation Workflows

Use this reference to translate UniLM multimodal requests into safe plans. The command examples are distilled from repository evidence and remain templates: native scripts require the matching source checkout, model checkpoints, optional downloads, GPU/runtime stack, and user-approved output directories.

## Safety Checklist Before Native Runs

- Confirm whether the user wants a plan, an input validation pass, a single inference run, or heavy training/evaluation.
- Confirm local checkpoints, tokenizer/dictionary/config files, images, audio/manifests, datasets, and reference-stat files exist before launching.
- Ask before downloading model weights, datasets, fonts, demo assets, Hugging Face models, or remote evaluation packages.
- Confirm GPU memory, CUDA, Torch, fairseq, diffusers, xformers, FlashAttention, Apex, or accelerate compatibility for the selected subproject.
- Run a lightweight `--help` or the bundled `scripts/check_multimodal_inputs.py` before a long job when possible.
- Keep output directories user-selected and avoid overwriting non-empty training/evaluation outputs unless the native script explicitly supports resume/overwrite.

## Kosmos-2 Grounded Multimodal Generation

Choose Kosmos-2 for grounded image-text generation, phrase grounding, referring expression comprehension/generation, captioning, and VQA. The source entry point `generate.py` imports UniLM and delegates to `fairseq_cli.generate.cli_main`, so most command flags are fairseq generation flags plus Kosmos task/user-dir/model arguments from the prepared source checkout.

Reference command shape:

```bash
python generate.py <DATA_OR_TASK_ROOT> \
  --path <KOSMOS2_CHECKPOINT.pt> \
  --user-dir <KOSMOS2_USER_DIR> \
  --task <KOSMOS2_TASK_NAME> \
  --gen-subset <SPLIT> \
  --results-path <OUTPUT_DIR> \
  --beam <BEAM> \
  --batch-size <BATCH_SIZE>
```

Practical notes:

- Setup evidence uses Python 3.9-era conda, `requirements.txt`, Apex, and `vl_setup_xl.sh`; do not attempt this inside a lightweight unrelated environment.
- The public checkpoint can be loaded through Hugging Face Transformers or downloaded as `kosmos-2.pt`, but any download must be user-approved.
- GRIT data instances contain image URL, caption, width/height, and normalized noun chunk/referring-expression boxes; generated training config lists TSV source files with `source_lang: grit` and `weight: 1.0`.
- Original demo/evaluation scripts under `demo/` and `evaluation/` are reference-only here because they depend on the source tree, images, datasets, checkpoints, and fairseq/TorchScale/openclip stack.

Use the checker for local prerequisites:

```bash
python scripts/check_multimodal_inputs.py kosmos2 \
  --checkpoint ./kosmos-2.pt \
  --image ./examples/corgi.jpg \
  --prompt "Describe the image and ground noun phrases" \
  --output-dir ./outputs/kosmos2
```

## Kosmos-2.5 Literate OCR And Markdown

Choose Kosmos-2.5 for text-intensive image reading, spatial OCR blocks, and image-to-markdown output. This is the only OCR/document route owned by this sub-skill; route LayoutLM/TrOCR/document layout tasks to `vision-document-ai`.

Native OCR shape:

```bash
python inference.py \
  --do_ocr \
  --image <IMAGE_PATH> \
  --ckpt <KOSMOS2_5_CHECKPOINT.pt> \
  --out_dir <OUTPUT_DIR>
```

Native markdown shape:

```bash
python inference.py \
  --do_md \
  --image <IMAGE_PATH> \
  --ckpt <KOSMOS2_5_CHECKPOINT.pt> \
  --out_dir <OUTPUT_DIR>
```

Aspect-ratio preprocessing shape:

```bash
python inference.py \
  --do_ocr \
  --image <IMAGE_PATH> \
  --ckpt <KOSMOS2_5_CHECKPOINT.pt> \
  --out_dir <OUTPUT_DIR> \
  --use_preprocess \
  --hw_ratio_adj_upper_span "[1.5, 5]" \
  --hw_ratio_adj_lower_span "[0.5, 1.0]"
```

Bounding-box visualization shape after OCR JSON is produced:

```bash
python draw_bbox.py \
  --image <IMAGE_PATH> \
  --ocr_json_path <OCR_JSON_PATH> \
  --out <BOXED_IMAGE_PATH> \
  --line_width 1
```

Practical notes:

- Exactly one of `--do_ocr` or `--do_md` must be selected.
- `--image` must be an existing local image; `--ckpt` should be an existing checkpoint even though the source assertion message has a typo around checkpoint existence.
- Requirements include `omegaconf<=2.1.0`, `fairscale==0.4`, `numpy==1.22`, `scipy==1.10`, xformers from a Git commit, `flash-attn --no-build-isolation`, triton, and forked fairseq/infinibatch/torchscale/transformers packages.
- The README states FlashAttention2 requires Ampere, Ada, or Hopper GPUs such as A100, RTX 3090/4090, or H100.
- Generated OCR/markdown may hallucinate; verify critical text against the image or a second OCR system.

Use the checker:

```bash
python scripts/check_multimodal_inputs.py kosmos25 \
  --task markdown \
  --image ./page.png \
  --checkpoint ./ckpt.pt \
  --output-dir ./outputs/kosmos25 \
  --use-preprocess
```

## TextDiffuser v1 Text Rendering

Choose TextDiffuser v1 for the original two-stage text rendering framework: prompt-only text-to-image, template-conditioned generation, text inpainting, MARIO-Eval sampling, or local Gradio planning.

Prompt-only inference:

```bash
CUDA_VISIBLE_DEVICES=0 python inference.py \
  --mode="text-to-image" \
  --resume_from_checkpoint="<TEXTDIFFUSER_CKPT>/diffusion_backbone" \
  --prompt="A sign that says 'Hello'" \
  --output_dir="<OUTPUT_DIR>" \
  --vis_num=4
```

Template-conditioned inference:

```bash
CUDA_VISIBLE_DEVICES=0 python inference.py \
  --mode="text-to-image-with-template" \
  --resume_from_checkpoint="<TEXTDIFFUSER_CKPT>/diffusion_backbone" \
  --prompt="a poster of monkey music festival" \
  --template_image="<TEMPLATE_IMAGE>" \
  --output_dir="<OUTPUT_DIR>" \
  --vis_num=4
```

Text inpainting:

```bash
CUDA_VISIBLE_DEVICES=0 python inference.py \
  --mode="text-inpainting" \
  --resume_from_checkpoint="<TEXTDIFFUSER_CKPT>/diffusion_backbone" \
  --prompt="a boy draws good morning on a board" \
  --original_image="<ORIGINAL_IMAGE>" \
  --text_mask="<TEXT_MASK_IMAGE>" \
  --output_dir="<OUTPUT_DIR>" \
  --vis_num=4
```

MARIO-Eval sampling:

```bash
CUDA_VISIBLE_DEVICES=0 python evaluate.py \
  --mode="text-to-image" \
  --resume_from_checkpoint="<TEXTDIFFUSER_CKPT>/diffusion_backbone" \
  --prompt_list="<MARIOEVAL_PROMPTS.txt>" \
  --output_dir="<OUTPUT_DIR>" \
  --vis_num=4
```

Practical notes:

- Prompts should enclose text to render in single quotes, such as `A sign that says 'Hello'`.
- v1 checkpoint archive is large and expected to contain `text_segmenter.pth`, `layout_transformer.pth`, and `diffusion_backbone/`.
- Layout generation needs a font file, commonly `assets/font/Arial.ttf`; pass `--font_path` when using a non-default location.
- Optional `--enable_xformers_memory_efficient_attention` reduces memory only when xformers is compatible with the active Torch/CUDA stack.

## TextDiffuser-2 Full, LoRA, Layout, And Inpainting

Choose TextDiffuser-2 for the ECCV 2024 language-model-powered text renderer. It supports text-to-image, text-to-image with template/layout planning, conversational layout editing, LoRA fine-tuning/inference, full fine-tuning/inference, and text inpainting.

Full-parameter text-to-image inference:

```bash
accelerate launch inference_textdiffuser2_t2i_full.py \
  --pretrained_model_name_or_path="runwayml/stable-diffusion-v1-5" \
  --mixed_precision="fp16" \
  --output_dir="<OUTPUT_DIR>" \
  --enable_xformers_memory_efficient_attention \
  --resume_from_checkpoint="JingyeChen22/textdiffuser2-full-ft" \
  --granularity=128 \
  --max_length=77 \
  --coord_mode="ltrb" \
  --cfg=7.5 \
  --sample_steps=20 \
  --seed=43555 \
  --m1_model_path="JingyeChen22/textdiffuser2_layout_planner" \
  --input_format="prompt" \
  --input_prompt="a hotdog with mustard and other toppings on it"
```

LoRA text-to-image inference:

```bash
accelerate launch inference_textdiffuser2_t2i_lora.py \
  --pretrained_model_name_or_path="runwayml/stable-diffusion-v1-5" \
  --mixed_precision="fp16" \
  --output_dir="<OUTPUT_DIR>" \
  --enable_xformers_memory_efficient_attention \
  --resume_from_checkpoint="JingyeChen22/textdiffuser2-lora-ft" \
  --granularity=128 \
  --coord_mode="ltrb" \
  --cfg=7.5 \
  --sample_steps=50 \
  --seed=43555 \
  --m1_model_path="JingyeChen22/textdiffuser2_layout_planner" \
  --input_format="prompt" \
  --input_prompt="a stamp of u.s.a"
```

Prompt-file or layout-file variants use the same native scripts with `--input_format file --input_file <JSON_OR_LAYOUT_FILE>` or `--prompts_txt_file <PROMPTS_TXT>` when supported by the selected script. Validate the file locally first.

Inpainting is released through `demo_textdiffuser2_inpainting_full.py` and full inpainting training scripts. Treat the demo as reference-only: it downloads demo images if absent, loads Hugging Face weights, uses Gradio, and calls CUDA directly. For non-interactive inpainting automation, inspect or adapt the full inpainting training/inference code in a dedicated working checkout and require original image, text mask/layout, checkpoint, GPU, and output path.

Full-parameter training shape:

```bash
accelerate launch train_textdiffuser2_t2i_full.py \
  --pretrained_model_name_or_path="runwayml/stable-diffusion-v1-5" \
  --train_batch_size=<PER_DEVICE_BATCH> \
  --gradient_accumulation_steps=<STEPS> \
  --gradient_checkpointing \
  --mixed_precision="fp16" \
  --num_train_epochs=<EPOCHS> \
  --learning_rate=<LR> \
  --output_dir="<OUTPUT_DIR>" \
  --enable_xformers_memory_efficient_attention \
  --index_file_path="<TRAIN_INDEX.txt>" \
  --dataset_path="<MARIO_OR_LAION_OCR_ROOT>" \
  --granularity=128 \
  --coord_mode="ltrb" \
  --max_length=77
```

LoRA training shape swaps in `train_textdiffuser2_t2i_lora.py`, usually raises `--learning_rate`, adds `--text_encoder_learning_rate`, and writes LoRA weights rather than a full diffusion backbone.

Use the checker:

```bash
python scripts/check_multimodal_inputs.py textdiffuser2 \
  --variant lora \
  --prompt "a stamp of u.s.a" \
  --checkpoint JingyeChen22/textdiffuser2-lora-ft \
  --layout-model JingyeChen22/textdiffuser2_layout_planner \
  --output-dir ./outputs/td2
```

## Audio And Speech Workflows

Choose this section for WavLM, BEATs, SpeechT5, SpeechLM, and VALL-E. Most source examples are Python snippets or shell scripts rather than a single universal CLI.

### WavLM Representation Extraction

Use WavLM for full-stack speech representation extraction and downstream speaker/speech tasks. Evidence snippets load a checkpoint with `checkpoint['cfg']`, construct `WavLMConfig`, load `checkpoint['model']`, normalize waveform if `cfg.normalize`, and call `model.extract_features`.

Pseudocode shape:

```python
checkpoint = torch.load("<WAVLM_CHECKPOINT.pt>")
cfg = WavLMConfig(checkpoint["cfg"])
model = WavLM(cfg)
model.load_state_dict(checkpoint["model"])
model.eval()
waveform_16khz = load_or_prepare_mono_16khz_tensor()
if cfg.normalize:
    waveform_16khz = torch.nn.functional.layer_norm(waveform_16khz, waveform_16khz.shape)
features = model.extract_features(waveform_16khz)[0]
```

### BEATs Tokenization, Representation, And AudioSet Classification

Use BEATs for acoustic tokenizers, audio representation extraction, or AudioSet classification. Checkpoint structure mirrors WavLM with `checkpoint['cfg']` and `checkpoint['model']`; fine-tuned classifiers may include `checkpoint['label_dict']` for top-k labels. BEATs expects 16 kHz audio tensors and internally computes 128-bin Kaldi fbank features.

### SpeechT5 ASR, TTS, ST, And VC

SpeechT5 uses fairseq user-dir tasks and 16 kHz manifests. Training is distributed and reference-only unless the user has explicitly prepared the dataset, labels, BPE/tokenizer, checkpoint, and GPUs.

ASR generation shape:

```bash
fairseq-generate <DATA_ROOT> \
  --gen-subset <SUBSET> \
  --bpe-tokenizer <BPE_TOKENIZER> \
  --user-dir <SPEECHT5_USER_DIR> \
  --task speecht5 \
  --t5-task s2t \
  --path <CHECKPOINT_PATH> \
  --hubert-label-dir <LABEL_DIR> \
  --ctc-weight <CTC_WEIGHT> \
  --lm-weight <LM_WEIGHT> \
  --lm-path <LM_PATH> \
  --max-tokens <MAX_TOKENS> \
  --beam <BEAM> \
  --scoring wer \
  --sample-rate 16000
```

TTS generation shape, where generation is available only with batch size 1:

```bash
python3 <SPEECHT5_CODE_DIR>/scripts/generate_speech.py <DATA_ROOT> \
  --gen-subset <SUBSET> \
  --bpe-tokenizer <BPE_TOKENIZER> \
  --user-dir <SPEECHT5_USER_DIR> \
  --task speecht5 \
  --t5-task t2s \
  --path <CHECKPOINT_PATH> \
  --hubert-label-dir <LABEL_DIR> \
  --batch-size 1 \
  --results-path <RESULTS_PATH> \
  --sample-rate 16000
```

Voice-conversion generation uses the same `generate_speech.py` shape with `--t5-task s2s`; SpeechT5 ST uses `fairseq-generate` with `--scoring sacrebleu` and task `s2t`.

### SpeechLM Feature Extraction And Fairseq Decoding

SpeechLM cleaned checkpoints use `checkpoint['cfg']['model']`, `SpeechLMConfig`, `SpeechLM`, and `checkpoint['cfg']['task']['normalize']`. ASR and ST scripts are shell wrappers around fairseq and expect wav2vec-style manifests such as `train.tsv`, `train.ltr`, matching `dict.ltr.txt`, CoVoST language directories, and optional KenLM/fairseq-lm assets.

### VALL-E

The inspected VALL-E directory only contains release notes and a demo link. Treat VALL-E as reference-only in this UniLM checkout: do not claim local inference or training scripts exist. If a user requests VALL-E implementation details, ask for an external implementation or route to paper/recovery work rather than running UniLM code.

Use the checker for local audio planning:

```bash
python scripts/check_multimodal_inputs.py audio \
  --family wavlm \
  --checkpoint ./WavLM-Base.pt \
  --audio ./sample.wav \
  --sample-rate 16000
```

## LatentLM Sampling, Training, And FID Evaluation

LatentLM README says setup and usage are coming soon, so rely on source-inspected scripts. Workflows are accelerate/Torch/diffusers based and expect a VAE, class-conditional latent model configuration, checkpoint directory, and ImageNet-style class labels.

Single image sample shape:

```bash
python sample_hf.py \
  --model Transformer-L \
  --vae <VAE_NAME_OR_PATH> \
  --checkpoint <CHECKPOINT_DIR> \
  --image_size 256 \
  --num-classes 1000 \
  --mixed_precision fp16 \
  --ddpm_num_inference_steps 250 \
  --cfg-scale 4.0 \
  --image_name sample.png
```

Many-sample shape:

```bash
python sample_many.py \
  --model Transformer-L \
  --vae <VAE_NAME_OR_PATH> \
  --checkpoint <CHECKPOINT_DIR> \
  --batch_size 32 \
  --image_size 256 \
  --num-classes 1000 \
  --mixed_precision fp16
```

Training shape:

```bash
accelerate launch train_hf.py \
  --dataset_name <HF_DATASET_NAME> \
  --train_data_dir <IMAGEFOLDER_ROOT> \
  --model Transformer-L \
  --vae <VAE_NAME_OR_PATH> \
  --image_size 256 \
  --num_classes 1000 \
  --batch_size <PER_DEVICE_BATCH> \
  --num_epochs <EPOCHS> \
  --learning_rate <LR> \
  --output_dir <OUTPUT_DIR> \
  --mixed_precision fp16 \
  --checkpointing_steps <STEPS>
```

Use either `--dataset_name` or `--train_data_dir`; if using a local ImageFolder, class subdirectories must exist and labels must align with `--num_classes`. If using Hugging Face datasets, network/cache behavior must be approved.

FID evaluation shape:

```bash
accelerate launch evaluate_fid.py \
  --model Transformer-L \
  --vae <VAE_NAME_OR_PATH> \
  --checkpoint <CHECKPOINT_DIR> \
  --ref_stat_path <FID_STATS.npz> \
  --image_size 256 \
  --num-classes 1000 \
  --batch_size 32 \
  --steps_per_class 50 \
  --cfg-scale 4.0
```

Checkpoint directory expectations:

- Sampling/evaluation may load `other_state.pth`, `model.safetensors`, or `pytorch_model/mp_rank_00_model_states.pt` from the checkpoint directory.
- `--use_ema` requires EMA state inside `other_state.pth`.
- Evaluation may cache generated latents as `latent_<exp_name>.pth` and writes FID/IS JSON plus compressed images into the checkpoint directory, so use a copy or dedicated output checkpoint directory if mutation is undesirable.

Use the checker:

```bash
python scripts/check_multimodal_inputs.py latentlm \
  --operation fid \
  --checkpoint ./checkpoint-50000 \
  --vae ./vae \
  --ref-stat ./imagenet_256_val.npz \
  --train-data-dir ./imagenet/train \
  --num-classes 1000
```

## Source Script Bundling Decisions

- `scripts/check_multimodal_inputs.py` is a safe bundled wrapper for validating local paths, arguments, and run readiness across Kosmos, TextDiffuser, audio/speech, and LatentLM.
- Original `kosmos-2/generate.py`, Kosmos-2 demo/evaluation scripts, `kosmos-2.5/inference.py`, `textdiffuser*/inference*.py`, SpeechT5/SpeechLM shell scripts, and LatentLM sample/train/evaluation scripts are reference-only because they require source-tree modules, checkpoints, GPUs, large dependencies, datasets, network downloads, and/or may mutate outputs.
- No native script is copied wholesale because the useful safe behavior is validation/planning, not generation itself.
