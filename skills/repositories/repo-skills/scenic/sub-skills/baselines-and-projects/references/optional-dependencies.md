# Optional dependency groups by Scenic project

Scenic's shared package can import many core modules without every project extra. Install optional dependencies only for the selected project family. Several projects have incompatible pins or heavy transitive dependencies; prefer isolated environments for detection/video-language experiments rather than one monolithic environment.

## Dependency decision table

| Group | Install when selected route uses | Representative packages | Projects that commonly need it | Notes |
|---|---|---|---|---|
| DMVR video input | Video classification/captioning pipelines with DeepMind Video Reader style preprocessing. | `dmvr @ git+https://github.com/deepmind/dmvr.git`, often `seaborn>=0.11.2` for reports. | ViViT, MTV, ObjectViViT, PolyViT, Vid2Seq, Streaming DVC, MBT. | Requires network unless cached. If unavailable, route data setup to `data-pipelines` and do static config inspection only. |
| Lingvo | MBT audio/video recipes that rely on Lingvo audio/data utilities. | `lingvo==0.11.0`. | MBT. | Lingvo can conflict with modern TensorFlow/JAX environments. Use a separate environment and do not install just for ViViT/MTV. |
| T5/T5X | Dense video captioning and text decoder routes. | `t5`, `t5x`, `gin-config`, `six`; Vid2Seq expects `flax==0.5` compatibility. | Vid2Seq, Streaming DVC Vid2Seq configs, PixelLLM T5 configs. | T5/T5X stacks are large and can impose version constraints. Require a T5/T5X checkpoint path before promising training. |
| CLIP/Torch | CLIP checkpoint loading/conversion, OWL-ViT CLIP backbones, or CLIP image/text feature baselines. | `torch>=1.10.2`, `tqdm`, OpenAI CLIP package. | Baseline CLIP, OWL-ViT, DenseVOC CLIP checkpoint preparation, some UnLoc/Video text routes. | Torch checkpoint conversion is separate from JAX training. Do not run conversion notebooks unattended. |
| COCO/LVIS APIs | Detection evaluation and COCO/LVIS-style annotation handling. | COCO API, `pycocotools`, `lvis`. | OWL-ViT evaluation, DETR, Deformable DETR, CenterNet, PixelLLM, DenseVOC. | LVIS eval can be slow and requires local annotations. COCO API sometimes requires build tools. |
| Caption metrics | Dense captioning and dense object captioning metrics. | `pycocoevalcap`; Java runtime and captioning-metrics assets for some evaluators. | Vid2Seq, PixelLLM, DenseVOC, Streaming DVC. | Missing Java or metric assets causes late evaluator failures; collect `JRE_BIN_JAVA`/metric asset path before eval. |
| OTT/Sinkhorn | Alternative DETR/OWL-ViT matching and OT losses. | `ott-jax`; OWL-ViT expects `<0.4.0` for its matcher import; DETR uses `>=0.2.0` for Sinkhorn config. | DETR Sinkhorn config, OWL-ViT. | Version expectations differ by project. Pin in the selected environment, not globally. |
| tensorflow-addons | Big Transfer image preprocessing ops. | `tensorflow-addons`. | Baseline image configs and dataset preprocessing paths that use Big Transfer style `autoaugment`/image ops. | Install only if preprocessing import fails with `tensorflow_addons`. It is not required by every project. |
| big_vision | Checkpoint conversion/utilities and OWL-ViT/REVEAL-style model components. | `big_vision` from the Google Research big_vision package/source distribution. | OWL-ViT layers, AV-MAE/MBT/PolyViT/ViViT/MTV big_vision checkpoint-format restoration, PlainViT, some knowledge-visual-language paths. | Required when config says `checkpoint_format='big_vision'` or imports `big_vision.models`. Keep checkpoint format explicit. |
| Deformable DETR legacy stack | Reproducing Deformable DETR with its pinned CUDA/JAX stack. | `flax==0.5.3`, `jax==0.3.17`, `jaxlib==0.3.15+cuda11.cudnn82`, TensorFlow, TFDS, `ott-jax`, `clu`, `sklearn`, `ipdb`. | Deformable DETR only. | Do not mix with modern JAX projects. Use a dedicated environment matching host CUDA or switch to CPU/static inspection only. |
| Basic detection metrics | COCO detectors not using LVIS/caption metrics. | `pycocotools`, optionally `ott-jax`. | DETR, CenterNet, Deformable DETR. | COCO-format TFRecords or TFDS data still must exist. |

## Per-project requirement groups

| Project family | Required extra group(s) | Optional or conditional extras | Stop if missing |
|---|---|---|---|
| ViViT | DMVR, `seaborn` | big_vision if checkpoint format is big_vision. | Video data preprocessing, pretrained image ViT checkpoint when config expects `init_from`. |
| MTV | DMVR, `seaborn` | big_vision for multiview checkpoint initialization. | Per-view checkpoint paths, video dataset TFRecords/TFDS. |
| AV-MAE | Core Scenic stack | big_vision for transfer checkpoint conversion; audio/video data codecs as needed by dataset pipeline. | AudioSet/VGGSound/ImageNet data and `init_from.checkpoint_path` for finetune configs. |
| MBT | DMVR, Lingvo | big_vision checkpoint format. | Lingvo conflicts or unavailable audio/video dataset tables. |
| Vid2Seq | DMVR, T5/T5X, `gin-config`, `six`, Flax 0.5 compatibility | Caption metrics/Java for evaluation. | T5.1.1 checkpoint path, ASR/CLIP feature columns, dense-caption TFRecords. |
| Streaming DVC | DMVR, `pycocoevalcap`, T5/T5X for Vid2Seq routes | BERT vocab for GIT routes; caption metrics/Java for evaluation. | Missing pretrained GIT/Vid2Seq weights or dense-caption TFRecords. |
| DenseVOC | `pycocotools`, `pycocoevalcap` | CLIP/Torch for checkpoint conversion; Java/caption metrics for some eval. | Visual Genome/Spoken-MiT/VidSTG/VLN TFRecords, BERT tokenizer, converted weights, 32GB-class eval memory when required. |
| PixelLLM | `pycocotools`, `pycocoevalcap` | T5/T5X for T5 configs, BERT vocabulary for BERT configs, SAM/CLIP/GIT checkpoint assets. | Missing Localized Narratives/COCO/VG/RefCOCO/LLaVA data or tokenizer/checkpoint paths. |
| OWL-ViT | CLIP/Torch, COCO API, LVIS, `ott-jax<0.4.0`, big_vision | GPU-enabled JAX for practical speed. | Missing OWL-ViT checkpoint, LVIS/COCO annotations for eval, or text/image query assets for inference. |
| Baseline CLIP | CLIP/Torch | None for pure static inspection. | Missing official Torch checkpoint when conversion/loading is requested. |
| DETR | `pycocotools`; `ott-jax>=0.2.0` for Sinkhorn matcher | Pretrained ResNet50 checkpoint. | COCO data and backbone checkpoint. |
| Deformable DETR | Dedicated legacy JAX/CUDA stack, COCO/pycocotools, OTT | CPU/static inspection if matching CUDA stack unavailable. | Host cannot satisfy required JAX/JAXLIB/CUDA pins and user requires native run. |
| CenterNet/CenterNet2 | `pycocotools` | Converted ConvNeXt/MAE/VitDet checkpoints. | COCO-format data, converted pretrained checkpoint if config.weights is set. |
| BERT | `sklearn` | Official TF preprocessing code if generating data from raw text. | TFRecord pretraining/finetuning data and vocab file. |
| PointCloud/PCT | Core Scenic stack | Dataset-specific loaders/assets. | ModelNet40/S3DIS/ShapeNet data unavailable. |
| TokenLearner | Core Scenic stack | ViViT/DMVR only for video-style usage. | Dataset lacks image/video labels matching selected config. |
| MatViT | Core Scenic stack | big_vision/ViT checkpoint interop if transfer requires it. | MatViT checkpoint missing for mix-and-match eval. |
| SVViT | Core Scenic stack | Performer/XViT dependencies if not already in Scenic env. | Pileup datasets or transfer checkpoint missing. |
| CLAY/layout_denoise | Core Scenic stack | CLAY/Rico data generation dependencies outside Scenic. | Generated UI layout dataset unavailable. |

## Concrete install snippets

Use these snippets as starting points only after selecting a project. Prefer an isolated environment per incompatible group.

### ViViT / MTV / PolyViT / ObjectViViT video stack

```bash
python -m pip install 'dmvr @ git+https://github.com/deepmind/dmvr.git' 'seaborn>=0.11.2'
```

### Vid2Seq dense-caption stack

```bash
python -m pip install 'dmvr @ git+https://github.com/deepmind/dmvr.git' gin-config t5 t5x six 'flax==0.5'
```

### Streaming DVC stack

```bash
python -m pip install 'dmvr @ git+https://github.com/deepmind/dmvr.git' pycocoevalcap t5 t5x six
```

### OWL-ViT / CLIP stack

```bash
python -m pip install 'torch>=1.10.2' tqdm 'git+https://github.com/openai/CLIP.git' lvis 'ott-jax<0.4.0'
python -m pip install 'git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI'
```

### Detection metric stack

```bash
python -m pip install pycocotools
# Only for DETR Sinkhorn matching:
python -m pip install 'ott-jax>=0.2.0'
```

### Dense caption/object caption stack

```bash
python -m pip install pycocotools pycocoevalcap
```

### Big Transfer preprocessing fallback

```bash
python -m pip install tensorflow-addons
```

### big_vision-dependent paths

```bash
python -m pip install 'git+https://github.com/google-research/big_vision.git'
```

If package install fails due network restrictions, stop and ask for a cached wheel/source path or permission to enable network/proxy. Do not replace a required project dependency with an unrelated package.

## Dependency troubleshooting by symptom

| Symptom | Likely group | Recovery |
|---|---|---|
| `ModuleNotFoundError: dmvr` | DMVR video stack | Install DMVR only if the selected project is video/captioning. Otherwise switch to static config inspection. |
| `ModuleNotFoundError: lingvo` | MBT stack | Use a separate MBT environment; do not install Lingvo into a working OWL-ViT/Vid2Seq env without approval. |
| `ModuleNotFoundError: t5`, `t5x`, or `gin` | Vid2Seq/Streaming text decoder | Install T5/T5X stack and verify checkpoint path. |
| `ModuleNotFoundError: clip` or Torch checkpoint loader failures | CLIP/Torch | Install Torch/OpenAI CLIP; verify checkpoint type before conversion. |
| `ModuleNotFoundError: pycocotools`, `pycocoevalcap`, or `lvis` | Detection/caption eval | Install the specific metric package and verify annotations before rerunning eval. |
| `ModuleNotFoundError: tensorflow_addons` | Big Transfer preprocessing | Install tensorflow-addons or choose preprocessing that does not use those ops. |
| `ModuleNotFoundError: big_vision` | big_vision checkpoint/model path | Install big_vision, or change `checkpoint_format` only if the checkpoint is actually Scenic-compatible. |
| JAX/JAXLIB/CUDA version mismatch in Deformable DETR | Legacy detection env | Build a dedicated environment matching the pinned CUDA stack; otherwise restrict to CPU/static inspection. |

## Stop conditions

Stop and ask for data, credentials, or compute instead of attempting a run when:

- A config contains placeholder paths for `config.weights`, `config.init_from.checkpoint_path`, tokenizer paths, `base_dir`, `tables`, annotation JSONs, or TFRecords.
- A project tool would write TFRecords/JSON/checkpoints and the output directory/overwrite policy is unknown.
- The task requires LVIS/COCO/caption metrics but annotations or Java/captioning-metrics assets are missing.
- The selected route requires a GPU/TPU or high-memory accelerator and the user only permits CPU.
- Dependency pins conflict with an existing environment the user asked not to mutate.
