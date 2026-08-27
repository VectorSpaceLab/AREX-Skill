# Batch Evaluation

MMAudio batch evaluation is a batched generation workflow for datasets, not a metric runner. It loads a pretrained MMAudio variant, prepares text/video conditions from an evaluation dataset, generates audio in batches, and saves one `.flac` file per sample.

## When to use it

Use batch evaluation when you need:

- many generated samples from AudioCaps, VGGSound, or MovieGen-style data;
- multi-GPU or per-GPU batched inference;
- generated audio files for a separate metric suite;
- audio-only outputs without video re-encoding/composition.

Use the inference route for a single prompt/video demo or when you need composited videos.

## Launch contract

The evaluator is a CUDA/DDP script. Launch with `torchrun`, including one-process jobs:

```bash
OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=1 batch_eval.py duration_s=8 dataset=vggsound model=small_16k num_workers=2 batch_size=4 compile=False output_name=smoke-vgg
```

Do **not** use `python batch_eval.py` for normal execution. The script reads `LOCAL_RANK` and `WORLD_SIZE` before Hydra starts, then calls `torch.distributed.init_process_group(backend="nccl")`. `torchrun` supplies the needed distributed variables and rendezvous settings.

## Safe command builder

Use the bundled helper to validate common options and print a command without running the model:

```bash
python skills/disco/mmaudio/sub-skills/evaluation/scripts/build_batch_eval_command.py \
  --dataset vggsound \
  --model small_16k \
  --nproc-per-node 1 \
  --batch-size 4 \
  --num-workers 2 \
  --no-compile \
  --output-name local-vgg \
  --vgg-video-path ./data/test-videos \
  --vgg-csv-path ./data/vggsound.csv
```

Rendered command shape:

```bash
OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=1 batch_eval.py exp_id=small_16k-eval dataset=vggsound model=small_16k duration_s=8 batch_size=4 num_workers=2 compile=False amp=True seed=14159265 cfg_strength=4.5 sampling.method=euler sampling.num_steps=25 output_name=local-vgg eval_data.VGGSound.video_path=./data/test-videos eval_data.VGGSound.csv_path=./data/vggsound.csv
```

Add `--check-paths` to the helper when the dataset files are local and you want a read-only schema/path check before rendering. The helper does not import MMAudio, download weights, create outputs, or launch CUDA work.

## Key Hydra overrides

| Override | Default from distilled config | Meaning / caution |
|---|---:|---|
| `dataset` | `audiocaps` | Dataset selector. Recognized prefixes are `audiocaps_full`, `audiocaps`, `moviegen`, and `vggsound`. |
| `model` | `small_16k` | Pretrained model variant. See the model table below. |
| `duration_s` | `8.0` | Requested generation duration. The model sequence config is updated before inference. Video datasets require enough frames for this duration. |
| `batch_size` | `16` | Per-GPU evaluation batch size. Reduce first for OOM. |
| `num_workers` | `10` in base config; docs often use `8` | Per-GPU dataloader workers. Use `0` or `1` while debugging schema/decode failures. |
| `output_name` | `null` | If set, output directory becomes `<dataset>-<output_name>` inside the Hydra run directory. |
| `compile` | `True` | Compiles selected model/feature functions. Disable for quick smoke/debug runs or compiler failures. |
| `amp` | `True` | Uses bfloat16 autocast on CUDA. Disable only for precision/debug needs. |
| `seed` | `14159265` | Seed for the CUDA random generator. |
| `cfg_strength` | `4.5` | Classifier-free guidance strength passed into generation. |
| `sampling.method` | `euler` | Flow-matching inference method. |
| `sampling.num_steps` | `25` | Number of sampling steps. More steps are slower. |
| `eval_data.<Dataset>.*` | see data-format reference | Override evaluation media/metadata paths without editing config files. |
| `hydra.run.dir` | `./output/${exp_id}` | Parent run directory. Quote values containing `${...}` when the shell might expand them. |

## Model variants and generated sample rate

| `model` | Mode | Generated audio sample rate | Runtime asset behavior |
|---|---:|---:|---|
| `small_16k` | `16k` | 16,000 Hz | Uses 16 kHz VAE plus BigVGAN vocoder assets. |
| `small_44k` | `44k` | 44,100 Hz | Uses 44.1 kHz VAE; no 16 kHz vocoder path. |
| `medium_44k` | `44k` | 44,100 Hz | Uses 44.1 kHz VAE; larger network than `small_44k`. |
| `large_44k` | `44k` | 44,100 Hz | Uses 44.1 kHz VAE; heavier GPU memory demand. |
| `large_44k_v2` | `44k` | 44,100 Hz | Uses 44.1 kHz VAE; latest large generation variant. |

For the default 8-second sequence configuration, verified sequence facts are:

| Mode | Audio samples | Latent sequence | CLIP sequence | Sync sequence |
|---|---:|---:|---:|---:|
| `16k` | `128000` | `250` | `64` | `192` |
| `44k` | `353280` | `345` | `64` | `192` |

When `duration_s` changes, the evaluator mutates the model sequence configuration and calls `update_seq_lengths(...)` before generation. Keep the dataset video duration and evaluation metric assumptions aligned with the override.

## Output layout

Hydra creates a run directory under `./output/<exp_id>` by default. Within that directory:

- if `output_name=null`, generated audio goes to `<run-dir>/<dataset>/`;
- if `output_name=<name>`, generated audio goes to `<run-dir>/<dataset>-<name>/`;
- Hydra metadata goes to a timestamped `eval-...-hydra` subdirectory;
- each generated sample is saved as `<sample-name>.flac` at the model mode's sample rate.

Batch evaluation does not save MP4 files or attach generated audio back to source video.

## Common command patterns

### One-GPU VGGSound with explicit local paths

```bash
python skills/disco/mmaudio/sub-skills/evaluation/scripts/build_batch_eval_command.py \
  --dataset vggsound \
  --model small_16k \
  --nproc-per-node 1 \
  --batch-size 4 \
  --num-workers 2 \
  --no-compile \
  --output-name onegpu-vgg \
  --vgg-video-path ./data/test-videos \
  --vgg-csv-path ./data/vggsound.csv
```

Run the printed command from a prepared MMAudio working tree. Expect `.flac` files named after VGGSound clip ids such as `<youtube_id>_<start_sec:06d>.flac`.

### Four-GPU VGGSound throughput run

```bash
OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=4 batch_eval.py duration_s=8 dataset=vggsound model=small_16k num_workers=8 batch_size=16 output_name=4gpu-vgg
```

`batch_size` is per GPU here. Increase only after confirming memory headroom.

### Text-only AudioCaps generation

```bash
OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=1 batch_eval.py dataset=audiocaps model=large_44k_v2 duration_s=8 batch_size=8 num_workers=2 compile=False eval_data.AudioCaps.audio_path=./data/AudioCaps-test-audioldm-ver eval_data.AudioCaps.csv_path=./data/AudioCaps-test-audioldm-ver/data.csv output_name=text-only
```

AudioCaps uses caption text and sample names; it does not condition on source audio content. The audio directory must still exist because the dataset constructor lists it.

### MovieGen-style generation

```bash
OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=1 batch_eval.py dataset=moviegen model=large_44k_v2 duration_s=10 batch_size=2 num_workers=1 compile=False eval_data.MovieGen.video_path=./data/MovieGen/videos eval_data.MovieGen.jsonl_path=./data/MovieGen/metadata output_name=moviegen10s
```

Use `duration_s=10` only when all videos have enough frames for 10 seconds at both CLIP and Sync preprocessing rates.

## Before launch checklist

1. CUDA is visible and the selected `--nproc_per_node` does not exceed available GPUs.
2. The MMAudio package and PyTorch CUDA stack import in the environment.
3. Pretrained MMAudio weights and external VAE/Synchformer/vocoder assets are present, or downloads are permitted for this run.
4. Dataset metadata exists and matches the schema in `evaluation-data-formats.md`.
5. A quick helper call with `--check-paths` succeeds for local paths.
6. `batch_size`, `num_workers`, and `compile` are conservative for the first run.
7. The intended output directory name is clear via `exp_id` and `output_name`.

## After-run validation

Use read-only checks before metrics:

```bash
# Count generated files.
find output -path '*/*.flac' -type f | wc -l

# Inspect a few audio files without modifying them.
python - <<'PY'
from pathlib import Path
import torchaudio
for path in sorted(Path('output').glob('**/*.flac'))[:5]:
    audio, sr = torchaudio.load(path)
    print(path, 'shape=', tuple(audio.shape), 'sample_rate=', sr)
PY
```

Expected signs of success:

- at least one `.flac` per usable dataset item assigned across ranks;
- sample rate matches the model mode (`16000` for `small_16k`, `44100` for 44k variants);
- no video files are expected;
- Hydra logs show the loaded model asset path and sequence lengths.

## Quantitative metrics boundary

Batch evaluation itself only generates audio. FAD/KL/CLAP-style quantitative metrics are handled by the external av-benchmark tooling used by the MMAudio project, not by this sub-skill's bundled scripts. Install and run that metric suite only when the task explicitly asks for those metrics and the required reference/generated datasets are available.
