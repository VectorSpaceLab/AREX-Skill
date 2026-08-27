# Vision And Document Troubleshooting

Use this reference when a UniLM vision/document workflow fails during planning, setup, data validation, or a native run. Favor narrow diagnosis over broad installs or upgrades, because these subprojects depend on mutually incompatible legacy stacks.

## Dependency Stack Triage

| Symptom | Likely cause | Narrow fix path | Avoid |
|---|---|---|---|
| `No module named detectron2` | DiT/LayoutLMv3 detection stack missing Detectron2 | Install a Detectron2 wheel matching the exact Torch and CUDA version, or move to an environment already prepared for that pair | Installing latest Detectron2 without checking Torch/CUDA |
| Detectron2 import raises CUDA symbol or C++ extension error | Wheel built for different Torch/CUDA/Python ABI | Record `python`, `torch.__version__`, `torch.version.cuda`, GPU driver, and wheel source; reinstall only the matching wheel | Upgrading Torch alone in an environment with compiled extensions |
| `mmcv` / `mmcv-full` import or ops failure | BEiT segmentation OpenMMLab version mismatch | Match mmcv-full/mmsegmentation versions from evidence-era configs, then verify CUDA ops import before launching training | Mixing modern mmengine/mmseg with old configs without migration |
| `apex` import failure or O2/FP16 errors | Apex not installed or incompatible with current CUDA/Torch | Disable Deepspeed/Apex only if native script supports torch AMP; otherwise build Apex for the exact environment | Installing Apex from a random binary wheel |
| `Please 'pip install deepspeed==0.4.0'` from BEiT-3 | `--enable_deepspeed` was passed but Deepspeed is absent | Remove `--enable_deepspeed` for a CPU/GPU smoke plan if acceptable, or install the expected Deepspeed version in an isolated environment | Installing modern Deepspeed into an old Torch stack without checking compatibility |
| `fairseq` import or user-dir errors in TrOCR | TrOCR native code expects fairseq plus local user-dir modules | Confirm `fairseq-train`/`fairseq-generate` resolve in the active environment and run from the TrOCR code directory when using native scripts | Treating TrOCR like a pure Transformers-only model when using native fairseq code |
| `transformers` version check fails | LayoutLMv3 scripts require a specific Transformers minimum; XDoc folders may need different versions | Create per-workflow isolated environments and pin around the script's requirement file | Sharing one environment across LayoutLMv3, XDoc, MarkupLM, and legacy BEiT stacks |
| `PreTrainedTokenizerFast` error | LayoutLMv3 token classification requires a fast tokenizer | Use a compatible Hugging Face model/tokenizer with fast tokenizer support; check `tokenizer_name` if separate from model | Forcing a slow tokenizer with LayoutLMv3 data collator |

## Dataset And Schema Checks

### ImageFolder / BEiT Classification

- Required: `train/` and `val/` directories, each containing one subdirectory per class.
- Check that class folder names match between train and validation sets.
- For custom class counts, pass the correct `--nb_classes` if the runner exposes it; ImageNet defaults assume 1000.
- If accuracy is near zero, check whether `--model`, `--input_size`, and checkpoint resolution match.

### BEiT / BEiT v2 Pretraining

- `--discrete_vae_weight_path` or `--tokenizer_weight` must point to an available tokenizer asset; tokenizer checkpoints are not optional.
- `--num_mask_patches` and input size should be compatible with patch size.
- For BEiT v2, base vs large changes `--early_layers`, `--layer_scale_init_value`, and practical per-GPU batch size.
- DALL-E tokenizer assets and VQ-KD weights may be remote in examples; get approval before downloading.

### ADE20K Segmentation

- Confirm ADE20K is prepared according to the mmsegmentation dataset guide expected by the old config.
- `CONFIG_PATH` must match the chosen BEiT/BEiT v2 model size and crop/slide schedule.
- `model.pretrained` should be an ImageNet-pretrained or intermediate-finetuned checkpoint, not a segmentation checkpoint.
- If `tools/dist_train.sh` is missing, the command must be run from the compatible mmsegmentation checkout, not from this skill directory.

### FUNSD / CORD / XFUND Layout Data

- FUNSD/CORD token classification expects words or tokens, labels, bounding boxes, and document images. Missing `words`, `tokens`, `ner_tags`, or bounding boxes will fail preprocessing or produce meaningless labels.
- LayoutLMv3 FUNSD/CORD uses `--dataset_name funsd` or `--dataset_name cord`; misspellings fall into `NotImplementedError` in the source script.
- XFUND requires files named by language such as `zh.train.json`, `zh.val.json`, and matching images under `images/`.
- For LayoutLMv3 visual runs, keep `--segment_level_layout 1 --visual_embed 1 --input_size 224` unless deliberately doing text-only ablation.
- Bounding boxes should be normalized consistently with the dataset loader. If labels align but boxes do not, F1 may collapse without an obvious exception.

### Document Detection Data

- PubLayNet and ICDAR detection require COCO-style annotations and matching image roots. The native DiT instructions often use symlinks named `publaynet_data` or `data`.
- ICDAR cTDaR archival evaluation uses adaptive binarization in the evidence; reproductions should include that preprocessing.
- Config/checkpoint mismatch signals include unexpected key names, incompatible backbone size, or wrong detector head dimensions.
- For FUNSD text detection with DiT, confirm processed `annotations`, `imgs`, `instances_test.json`, and `instances_training.json` are present.

### TrOCR OCR Inputs

- Native single-image inference expects an image readable by PIL, converted to RGB, resized to 384×384, and normalized.
- IAM, SROIE, and STR training/evaluation use different `--data-type`, scoring, BPE, dictionary, and preprocessing flags.
- If recognition output is blank or garbled, check whether the checkpoint matches the BPE/dictionary choice (`gpt2` vs sentencepiece/unilm small-model path).
- For full scanned pages, detect/crop text regions before TrOCR; the native OCR path is not a document layout detector.

### VLMo Arrow Data

- `data_root` should point to pyarrow files generated from the expected raw dataset layout, not raw image folders alone.
- GCC/SBU URL datasets may have many dead URLs; missing images are a data acquisition issue, not a model bug.
- COCO/Flickr retrieval needs Karpathy split JSONs; VQAv2 needs questions and annotations; NLVR2 needs signed access data and generated arrow files.
- Retrieval evaluation should append `get_recall_metric=True`; otherwise it may run without recall metrics.

### MarkupLM / XDoc Web Data

- MarkupLM WebSRC needs generated `websrc1.0_train_.json` and `websrc1.0_dev_.json`, not just the original archive.
- SWDE needs packed and processed data before vertical-specific training.
- XDoc WebSRC instructions reference arguments configured in its folder; inspect the task-specific argument file before running.
- HTML/DOM tasks need XPath or markup features; do not route them to OCR unless the page is only available as an image.

## Command Construction Mistakes

| Mistake | Signal | Correction |
|---|---|---|
| Using `--finetune` for evaluation where script expects `--resume` | Checkpoint ignored or wrong keys | Follow each family's eval example: BEiT often uses `--resume`; BEiT-3 uses `--finetune` with `--eval` |
| Missing BEiT-3 `--sentencepiece_model` | Argument parser error | Always provide the BEiT-3 `.spm` tokenizer path for BEiT-3 tasks |
| Forgetting `--input_size 384/480` for higher-resolution BEiT-3 | Shape mismatch or wrong positional embeddings | Match model suffix (`patch16_384`, `patch16_480`) and `--input_size` |
| Passing raw XFUND directory to FUNSD/CORD script | Unknown columns or missing dataset loader | Use `run_xfund.py` for XFUND and `run_funsd_cord.py` for FUNSD/CORD |
| Mixing DiT base config with large checkpoint | State dict shape mismatch | Align config path, model size, and checkpoint family |
| Running VLMo command without Sacred `with` | Config arguments ignored | Use `python run.py with key=value <config_name>` syntax |
| Reusing old output directory | Resume or non-empty directory error | Pick a fresh output directory or intentionally pass overwrite/resume flags supported by that runner |

## Backend Version Anchors From Evidence

These anchors are not universal install instructions; they explain why conflicts happen.

- BEiT v1 evidence names PyTorch 1.7.1, torchvision 0.8.2, Timm 0.3.2, optional Apex, and Deepspeed use in fine-tuning.
- BEiT v2 evidence names PyTorch 1.7.1, torchvision 0.8.2, Timm 0.4.12, optional Apex, and mmcv-full/mmsegmentation for segmentation.
- BEiT-3 evidence names a PyTorch 1.8.1 CUDA 11.1 container and uses Deepspeed when `--enable_deepspeed` is set.
- DiT evidence names PyTorch 1.9.0, torchvision 0.10.0, Timm 0.5.4, Apex for mixed precision, and Detectron2 for object detection.
- LayoutLMv3 evidence names Python 3.7, Torch 1.10.0+cu111, torchvision 0.11.1+cu111, Detectron2 cu111/torch1.10 wheels, and Transformers-style scripts.
- TrOCR evidence names Python 3.7, fairseq, pybind11, and Apex for native training/evaluation.
- VLMo evidence uses PyTorch Lightning, Sacred configuration, optional Deepspeed/fairscale-style memory reduction, and pyarrow data.

## Safe Escalation Pattern

When a native command fails:

1. Capture the exact command, working directory, Python version, Torch version, CUDA version, and first stack trace frame from project code.
2. Identify whether the failure is data schema, missing checkpoint/tokenizer, dependency import, compiled extension, or command flag misuse.
3. Make the smallest correction: add a missing flag, fix data layout, align config/checkpoint, or switch to the matching isolated environment.
4. Re-run a small validation command if available, such as `--help`, `--eval` on a tiny subset, or one-process smoke mode.
5. Ask before installing large backend stacks, downloading datasets/checkpoints, launching distributed jobs, or overwriting outputs.

## Unsupported Or Reference-Only Cases

- The public skill does not bundle original UniLM heavy training scripts; they remain reference-only because they depend on the source tree, datasets, checkpoints, and backend stacks.
- The lightweight inspection environment only verified the unrelated `adalm` package import; do not infer that BEiT, DiT, LayoutLM, TrOCR, or VLMo imports are installed.
- VL-BEiT had only release-note-level evidence in the inspected checkout. For deep VL-BEiT implementation tasks, use repository evidence if provided by the user or route generation-specific requests to `multimodal-generation`.
