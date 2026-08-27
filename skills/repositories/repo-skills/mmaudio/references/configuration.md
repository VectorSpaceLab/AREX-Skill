# Shared Configuration

Read this for Hydra conventions, common overrides, model sequence facts, and
shared data/model path expectations used across MMAudio inference, training,
and evaluation.

## Hydra command style

Training and batch evaluation use Hydra. Override keys on the command line as
`key=value`, for example:

```bash
torchrun --standalone --nproc_per_node=1 train.py exp_id=debug model=small_16k compile=False
```

For nested keys use dot notation:

```bash
eval_data.VGGSound.video_path=./data/test-videos eval_data.VGGSound.csv_path=./data/vggsound.csv
```

Quote values containing spaces, shell glob characters, or `${...}`.

## Shared defaults

| Key | Default / role | Notes |
| --- | --- | --- |
| `hydra.run.dir` | `./output/${exp_id}` | Parent output directory for training/evaluation runs. |
| `exp_id` | `default` in base, often model name in eval | Controls output path and checkpoint lookup. |
| `model` | `small_16k` in config; CLI demo defaults to `large_44k_v2` | Training code accepts `small_16k`, `small_44k`, `medium_44k`, `large_44k`; inference also accepts `large_44k_v2`. |
| `compile` | `True` | Speeds longer runs but can slow or fail during smoke/debug. Disable with `compile=False`. |
| `amp` | `True` | Uses bfloat16 autocast on CUDA for evaluator/training paths. |
| `seed` | `14159265` in Hydra configs; `42` in demo CLI | Controls generated noise/random setup. |
| `cfg_strength` | `4.5` | Classifier-free guidance strength. |
| `sampling.method` | `euler` | Flow-matching sampler. |
| `sampling.num_steps` | `25` | More steps are slower. |
| `num_workers` | `10` base | Per-GPU dataloader workers; reduce to `0`/`1` for debugging. |
| `pin_memory` | `False` | Enable only when memory pressure is understood. |

## Checkpoint and external-module paths

| Key | Default | Used by |
| --- | --- | --- |
| `vae_16k_ckpt` | `./ext_weights/v1-16.pth` | 16 kHz training/sample path. |
| `vae_44k_ckpt` | `./ext_weights/v1-44.pth` | 44.1 kHz training/sample path. |
| `bigvgan_vocoder_ckpt` | `./ext_weights/best_netG.pt` | 16 kHz vocoder path. |
| `synchformer_ckpt` | `./ext_weights/synchformer_state_dict.pth` | Video sync conditioning. |
| `weights` | `null` | Optional model-weight initialization. |
| `checkpoint` | `null` | Optional exact training resume checkpoint. |

When both an explicit `checkpoint=` and `weights=` are considered, prefer a
single resume mode. An explicit checkpoint restores optimizer/scheduler/EMA
state; weights-only initialization does not.

## Data configuration groups

### Training-side extracted features

| Config entry | Expected fields | Purpose |
| --- | --- | --- |
| `ExtractedVGG` | `tsv`, `memmap_dir` | Main video feature memmap for training. |
| `ExtractedVGG_val` | `tag`, `gt_cache`, `output_subdir`, `tsv`, `memmap_dir` | Validation and periodic eval during training. |
| `ExtractedVGG_test` | same shape as val | Built-in final sample/test path. |
| `AudioCaps`, `AudioSetSL`, `BBCSound`, `FreeSound`, `Clotho` | `tsv`, `memmap_dir` | Audio-text corpora used in `MultiModalDataset`. |
| `Example_video`, `Example_audio` | local example memmap paths | Smoke/test feature stores after running extractors. |

### Evaluation-side datasets

| Dataset selector | Config fields | Schema owner |
| --- | --- | --- |
| `audiocaps` | `eval_data.AudioCaps.audio_path`, `eval_data.AudioCaps.csv_path` | evaluation sub-skill |
| `audiocaps_full` | `eval_data.AudioCaps_full.audio_path`, `eval_data.AudioCaps_full.csv_path` | evaluation sub-skill |
| `vggsound` | `eval_data.VGGSound.video_path`, `eval_data.VGGSound.csv_path` | evaluation sub-skill |
| `moviegen` | `eval_data.MovieGen.video_path`, `eval_data.MovieGen.jsonl_path` | evaluation sub-skill |

## Sequence and data dimensions

The code patches `data_dim.latent_seq_len`, `data_dim.clip_seq_len`, and
`data_dim.sync_seq_len` from the selected model mode. Do not manually edit those
sequence lengths unless you are also changing the model sequence configuration.

| Field | Value |
| --- | ---: |
| `data_dim.text_seq_len` | 77 |
| `data_dim.clip_dim` | 1024 |
| `data_dim.sync_dim` | 768 |
| `data_dim.text_dim` | 1024 |

Mode-derived defaults:

| Mode | latent seq | clip seq | sync seq | audio samples |
| --- | ---: | ---: | ---: | ---: |
| `16k` | 250 | 64 | 192 | 128000 |
| `44k` | 345 | 64 | 192 | 353280 |

## Which sub-skill owns which config details

- Inference model choice, duration mutation, and demo CLI flags ->
  [`../sub-skills/inference/SKILL.md`](../sub-skills/inference/SKILL.md).
- Training memmap inputs and feature extraction outputs ->
  [`../sub-skills/data-preparation/SKILL.md`](../sub-skills/data-preparation/SKILL.md).
- DDP training overrides, checkpoints, EMA, and smoke commands ->
  [`../sub-skills/training/SKILL.md`](../sub-skills/training/SKILL.md).
- Batch evaluation datasets and path schemas ->
  [`../sub-skills/evaluation/SKILL.md`](../sub-skills/evaluation/SKILL.md).
