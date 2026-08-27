# Multi-Modality Configuration and Data

## Python config system

InternVideo2 multi-modality uses Python config files rather than one fixed YAML schema. The configs under `configs/` and `scripts/**/config.py` are loaded by `Config.from_file`, then overridden by key/value command-line pairs.

Common override pattern:

```text
tasks/pretrain.py <config.py> output_dir <run-dir> evaluate True pretrained_path <checkpoint>
```

Important config behaviors:

- `from configs.data import *` and `from configs.model import *` seed the config namespace.
- String interpolation such as `${num_frames}` is resolved after merge.
- `evaluate True` switches a training config into evaluation-only mode.
- `auto_resume` may replace the provided checkpoint with `ckpt_latest.pth` or `ckpt_best.pth` if the output directory already contains a run.
- `deepspeed.stage` controls the ZeRO level when DeepSpeed is enabled.

## Environment variables and path roles

| Variable | Role |
|---|---|
| `INTERNVIDEO2_DATA_PATH` | Fallback root for dataset annotations and media roots used by `configs/data.py`. |
| `INTERNVIDEO2_MODEL_PATH` | Fallback root for checkpoints, tokenizers, vision encoders, and text encoders. |
| `VL_EXP_DIR` | Output/code staging root used by `tools/run.py`. |
| `MASTER_PORT` | Randomized rendezvous port set by shell launchers. |
| `OMP_NUM_THREADS` | Set to `1` in the documented launchers. |
| `PYTHONPATH` | Must include the multi-modality folder for demo and config import resolution. |

## Checkpoint and path rules

| Field | Expected form | Notes |
|---|---|---|
| `vision_encoder.pretrained` | File path | Stage2 vision weights such as `1B_pt.pth` or `6B_stage1.pth`. |
| `vision_ckpt_path` | File path | CLIP branch vision checkpoint used to seed the retrieval model. |
| `pretrained_path` | File path or resume target | Used for evaluation, resume, or checkpoint selection depending on the config. |
| `tokenizer_path` | Directory | Demo/CLIP configs expect a tokenizer folder, not a single file. |
| `llama_path` | Directory | LLM-style text encoders point at the model directory. |
| `text_ckpt_path` | File path | CLIP branch text backbone checkpoint such as `internvl_c_13b_224px.pth`. |
| `extra_ckpt_path` | File path | Additional distilled asset used by some smaller VideoCLIP variants. |

For BERT-based Stage2 configs, `BertTokenizer.from_pretrained(..., local_files_only=True)` means the tokenizer folder must already exist locally.

## Model families

| Family | Typical config cues |
|---|---|
| Stage2 1B/6B | `model_cls="InternVideo2_Stage2"` or `InternVideo2_Stage2_audiovisual`; `vision_encoder.name` uses `pretrain_internvideo2_1b_patch14_224` or `pretrain_internvideo2_6b_patch14_224`; text encoder is usually BERT-large. |
| CLIP 1B/6B | `model_cls="InternVideo2_CLIP"`; `vision_encoder.name` is `internvideo2` or `internvideo2_6B`; text path uses InternVL/LLM-style assets. |
| Smaller VideoCLIP S/B/L | `model_cls="InternVideo2_CLIP_small"`; MobileCLIP text encoder or distilled text/vision checkpoints. |
| Audio/video Stage2 | `model_cls="InternVideo2_Stage2_audiovisual"`; `audio_encoder.name="beats"`; `audio_input` fields and audio-vision loss weights are required. |

## Data and preprocess expectations

- Pretraining sources include CC3M, CC12M, SBU, VG, COCO, WebVid, and InternVid.
- Evaluation uses original videos or images plus JSON metadata, following the VINDLU-style splits referenced in the repository docs.
- Audio/video configs usually set `audio_sample_rate=16000`, `audio_reader_type` to `torchaudio` or `librosa`, and `max_audio_length` to bound decode cost.
- `configs/data.py` defines corpus aliases such as `msrvtt_1k_test`, `didemo_ret_test`, `anet_ret_val`, `vatex_*`, and action-recognition eval splits.
- `preprocess/create_sqlite_db.py` expects a JSON list of records with one media key (`image` or `video`) and `caption`, then writes an `annos` table.

## Example override patterns

```text
tasks/pretrain.py scripts/pretraining/stage2/1B/config.py output_dir <run-dir> evaluate True pretrained_path <model-root>/1B_stage2_pt.pth
tasks_clip/retrieval.py scripts/evaluation/clip/zero_shot/1B/config_msrvtt.py output_dir <run-dir> pretrained_path <model-root>/InternVideo2_CLIP_1B.pth
```

Treat these as configuration patterns, not submission commands. The bundled launch helper is for printing command skeletons only.
