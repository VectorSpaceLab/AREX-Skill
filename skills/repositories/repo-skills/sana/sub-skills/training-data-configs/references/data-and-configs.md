# Data layouts and config overrides

This reference is for planning Sana training inputs and CLI/config overrides. It is self-contained operational guidance distilled from the repo evidence labels listed in `SKILL.md`.

## Choose the data family first

| User data / goal | Sana loader or tool | Main training family | Safe local check |
|---|---|---|---|
| Image files with matching captions | `SanaImgDataset` | image scratch or image fine-tune | `validate_dataset_layout.py --mode image-pair` |
| Multi-scale image tar shards | `SanaWebDatasetMS` with WIDS metadata | image DDP/FSDP, Sprint | `validate_dataset_layout.py --mode wids` |
| Video zip shards with per-item JSON | `SanaZipDataset` | SANA-Video 480p/720p | `validate_dataset_layout.py --mode sana-zip-video` |
| Source/target paired video zips | `SanaV2VPairDataset` | SANA-Streaming bidirectional V2V | `validate_dataset_layout.py --mode streaming-v2v` |
| Long V2V JSONL manifest | LongSANA V2V manifest dataset | SANA-Streaming long V2V | `validate_dataset_layout.py --mode long-v2v` |
| Raw Sekai-style zips plus latent-cache zips | `SanaWMZipLatentDataset` | SANA-WM Stage-1 and WM distillation | `validate_dataset_layout.py --mode wm-zip-latent --vae-cache-dir ...` |
| Few subject images | DreamBooth dataset in the LoRA trainer | DreamBooth LoRA | `validate_dataset_layout.py --mode lora` |
| Prompt datasets and online rewards | Sol-RL config functions | Sol-RL | command-plan only; actual rewards/model downloads require runtime |

## Image-text pair layout for `SanaImgDataset`

`SanaImgDataset` is the simplest image training loader. The directory should contain one caption text file per image basename. The docs show the pair layout, and the implementation also expects `meta_data.json` listing image names.

```text
data/my_pairs/
|-- 000001.png
|-- 000001.txt
|-- 000002.jpg
|-- 000002.txt
`-- meta_data.json
```

Minimal `meta_data.json`:

```json
{
  "name": "sana-dev",
  "__kind__": "Sana-ImgDataset",
  "img_names": ["000001", "000002"]
}
```

Operational notes:

- Captions are read from the first line of `<basename>.txt`.
- Image extensions can be `.png`, `.jpg`, `.jpeg`, or `.webp`.
- Use `--data.type=SanaImgDataset` and `--model.multi_scale=false`.
- `SanaImgDataset` does not support `data.load_vae_feat=true`; keep VAE features disabled for this layout.
- If `meta_data.json` is absent, make one before training. The validator warns instead of training.
- For DreamBooth LoRA, captions are supplied by `--instance_prompt`; per-image `.txt` files are not required.

Example validation:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/my_pairs \
  --mode image-pair \
  --require-meta \
  --max-samples 50
```

## Multi-scale WIDS/WebDataset layout for `SanaWebDatasetMS`

Use `SanaWebDatasetMS` for multi-scale image training, FSDP training, Sprint training, and data with precomputed VAE latents. The loader expects tar shards and a WIDS metadata JSON.

Typical shard contents:

```text
000000.tar
|-- sample_000001.jpg
|-- sample_000001.json
|-- sample_000002.png
|-- sample_000002.json
`-- sample_000003.npy          # optional when data.load_vae_feat=true
```

Per-sample JSON needs at least:

```json
{"prompt":"a concise caption", "width":1024, "height":1024}
```

Metadata file placed next to shards:

```text
data/my_wids/
|-- 000000.tar
|-- 000001.tar
`-- wids-meta.json
```

Generate metadata after sharding:

```bash
python tools/create_wids_metadata.py data/my_wids > data/my_wids/wids-meta.json
```

The repository also includes an image-pair-to-tar converter:

```bash
python tools/convert_scripts/convert_ImgDataset_to_WebDatasetMS_format.py
```

That converter is interactive and writes one tar by default, so for larger datasets prefer a deliberate sharding script that emits matching image/json members and then run `tools/create_wids_metadata.py`.

Operational notes:

- Use `--data.type=SanaWebDatasetMS` and usually `--model.multi_scale=true`.
- Use `--data.load_vae_feat=true` only when the tar members contain latent arrays with shapes matching the configured aspect ratio and VAE downsample rate.
- If `data.load_text_feat=true`, the text feature path behavior is specialized and should not be enabled unless you have verified the expected `.npz` feature layout.
- `external_caption_suffixes` and `external_clipscore_suffixes` load sidecar JSON files named by replacing `.tar` with the suffix plus `.json`.
- The WIDS loader creates cache files under the user's cache directory; stale caches can preserve old shard lists after moving or replacing data.

Example validation:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/my_wids \
  --mode wids \
  --max-samples 5
```

## Video zip layout for `SanaZipDataset`

SANA-Video training uses zip files that contain video data plus a matching JSON per sample basename.

```text
data/my_video_zips/
`-- shard_000000.zip
    |-- clip_000001.mp4
    |-- clip_000001.json
    |-- clip_000002.npy
    `-- clip_000002.json
```

Per-sample JSON should include at least `prompt`, `width`, and `height`. The loader may append a motion-score suffix to the prompt when configured with motion-score sidecar JSON.

Operational notes:

- 480p config family uses WanVAE and `ASPECT_RATIO_VIDEO_480_MS`.
- 720p config family uses LTX2 VAE, 128 latent channels, spatial dimensions divisible by 32, and `ASPECT_RATIO_VIDEO_720_MS_DIV32`.
- Video configs commonly keep `train.use_fsdp=true`.
- If image joint training is not wanted, set `--train.joint_training_interval=0` or use a config where it is already zero.
- For custom video data, a copied YAML with `data.data_dir` as a dictionary is safer than a complex CLI dict override.

Example validation:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/my_video_zips \
  --mode sana-zip-video \
  --max-samples 10
```

## Streaming V2V paired layout

Bidirectional SANA-Streaming training uses `SanaV2VPairDataset`. The directory must contain `manifest.jsonl`; each row points to a zip shard and source/target members inside that shard.

```text
data/sana_streaming_pairs/
|-- manifest.jsonl
|-- dataset_info.json
|-- checksums.sha256
`-- data/train-00000-of-00010.zip
```

Required manifest fields:

```json
{"id":"pair-000001","shard":"data/train-00000-of-00010.zip","source_member":"source.npy","target_member":"target.npy","prompt":"apply an edit","width":1280,"height":704}
```

Rules enforced by the loader:

- `id` must be unique.
- `shard`, `source_member`, and `target_member` must be dataset-relative paths, not absolute paths and not paths containing `..`.
- Members can be `.npy` or video files. The loader decodes aligned source and target videos and returns the target as the main sample plus the source as conditioning.
- `data.load_vae_feat` and `data.load_text_feat` must be false for this paired raw-video loader.

The public example dataset includes checksums; validate them before training when present:

```bash
cd data/sana_streaming_1k/data/example_data
sha256sum -c checksums.sha256
cd -
```

Safe layout validation:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/sana_streaming_pairs \
  --mode streaming-v2v
```

## Long V2V manifest layout

The long SANA-Streaming fine-tuning stages use a local JSONL manifest. Each row contains an editing prompt, the reverse instruction, and a source video path relative to the manifest directory.

```text
data/sana_streaming_long_441/
|-- manifest.jsonl
`-- videos/example.mp4
```

```json
{"prompt":"Transform the scene into a watercolor painting.","reverse_prompt":"Transform the watercolor scene back into a realistic video.","source_video":"videos/example.mp4"}
```

Operational notes:

- Use separate directories for the 441-frame and 969-frame stages.
- The 969-stage config continues from the 441-stage checkpoint.
- `DISABLE_XFORMERS=1` is part of the public long V2V launch recipe.
- Training expects local checkpoints for the streaming and bidirectional SANA-Streaming DiTs.

## SANA-WM zip-latent layout

SANA-WM Stage-1 and SANA-WM distillation use `SanaWMZipLatentDataset`, which pairs raw metadata zips with VAE latent-cache zips of the same basename.

```text
data/sekai_game_train_961frames_16fps_ovl640/
|-- sekai_game_train_00000000.zip
|-- sekai_game_train_00000000_camera.npz
|-- sekai_game_train_00000000_LongSceneStaticCaption-Qwen3-VL-30B-A3B-Instruct.json
|-- sekai_game_train_00000000_vmafmotion.json
`-- ...

data/vae_cache/LTX2VAE_diffusers_704x1280/sekai_game_train_961frames_16fps_ovl640/
`-- sekai_game_train_00000000.zip
```

Raw zip entries:

```text
sample_000000.json
```

Latent-cache zip entries:

```text
sample_000000.npz     # contains z in C,T,H,W layout
```

Camera sidecar expectations:

- `<raw_zip_stem>_camera.npz` may contain `ids`, `ranges`, `pose`, and `intrinsics`.
- `pose` is camera-to-world over pixel frames; the dataset converts to relative poses.
- `intrinsics` are scaled to latent resolution.
- If camera data is absent, the loader falls back to identity poses and synthetic intrinsics, which is acceptable for smoke tests but not for camera-control quality.

HF and license warnings:

- The public SANA-WM example training dataset is about 235 GB.
- It is redistributed for non-commercial research use only because it is Sekai-derived. Review the dataset card, license, and notices before training or redistributing derivatives.
- The public recipes intentionally use only redistributable Sekai camera-control data; exact original model reproduction also used additional data mixtures that are not part of the public example dataset.

Safe validation:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/sekai_game_train_961frames_16fps_ovl640 \
  --vae-cache-dir data/vae_cache/LTX2VAE_diffusers_704x1280/sekai_game_train_961frames_16fps_ovl640 \
  --mode wm-zip-latent \
  --max-samples 5
```

## Config override syntax

Most image, Sprint, and video trainers use pyrallis-style CLI overrides. The syntax is dot-separated and typed from the config dataclasses:

```bash
--data.data_dir="[data/toy_data]"
--data.type=SanaWebDatasetMS
--model.load_from=hf://Efficient-Large-Model/Sana_1600M_1024px/checkpoints/Sana_1600M_1024px.pth
--train.train_batch_size=2
--train.num_workers=4
--work_dir=output/my_run
```

Practical rules:

- Quote values containing brackets, spaces, braces, or shell-special characters.
- Lists are commonly passed as `[data/path]` for image training examples.
- Dict-valued data directories, such as video and WM configs, are safest when edited in a copied YAML. If you must try a CLI dict override, shell-quote it, for example `--data.data_dir='{"my_video":"data/my_video_zips"}'`.
- For image configs, `work_dir` is top-level; `train.work_dir` may also appear in YAML but the trainers save to top-level `work_dir`.
- The shell wrappers inject defaults. `train_scripts/train.sh` and `train_scripts/train_scm_ladd.sh` add `--resume_from=latest`, `--report_to=tensorboard`, and `--debug=true`. Use a fresh `--work_dir` to avoid unintended resume.
- LongSANA and WM distillation use argparse/OmegaConf with `--config_path`, `--logdir`, `--disable-wandb`, `--max_iters`, and related flags rather than generic pyrallis override behavior.

## Minimum preflight checklist

Before any training plan, report these facts back to the user:

1. Data family and loader.
2. Config path or copied config name.
3. Local data path or HF dataset/model ids.
4. Whether VAE latents or text features are precomputed.
5. GPU count, node count, FSDP/CP settings, and expected memory pressure.
6. Batch size per GPU and gradient accumulation, if known.
7. Logging mode: tensorboard, wandb, wandb offline, or none.
8. Resume policy and checkpoint path.
9. License/usage constraints, especially SANA-WM Sekai-derived data and third-party DreamBooth images.
