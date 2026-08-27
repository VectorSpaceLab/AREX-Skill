# ESPnet2 Recipe Workflow

ESPnet2 recipes live under `egs2/<dataset>/<task>` and are designed to run from the task directory. For example:

```bash
cd egs2/an4/asr1
./run.sh --stage 2 --stop_stage 6
```

Do not run recipe scripts from `egs2/<dataset>` or `local/`; task scripts assume `path.sh`, `cmd.sh`, `utils/`, `steps/`, `scripts/`, `conf/`, and task-specific wrapper scripts are reachable from the task directory.

## Typical directory layout

```text
conf/       # training, inference, feature, scheduler configs
scripts/    # ESPnet2 task utilities
pyscripts/  # Python task utilities
steps/      # Kaldi-style helper scripts
utils/      # Kaldi-style helper scripts
local/      # corpus-specific data preparation
db.sh       # corpus roots
path.sh     # Python/tool path setup
cmd.sh      # local/slurm/sge/pbs command backend
run.sh      # thin entrypoint wrapper
asr.sh      # or tts.sh, enh.sh, st.sh, s2t.sh, spk.sh, diar.sh, etc.
```

## Creating or adapting a recipe

1. Start from the matching `egs2/TEMPLATE/<task>` setup when creating a new task directory.
2. Keep corpus-specific acquisition and conversion in `local/data.sh`.
3. Produce `data/<split>/` directories using the Kaldi-style files described in `kaldi-data-formats.md`.
4. Make `run.sh` a thin wrapper over the common task script with `train_set`, `valid_set`, `test_sets`, and task-specific text/audio arguments.
5. Keep default training and decoding configs simple (`conf/train.yaml`, `conf/decode.yaml`) and put variants in `conf/tuning/`.
6. Do not enable packing, uploading, Hugging Face publication, or demo stages without user approval.

## Common run controls

```bash
./run.sh --stage 2 --stop_stage 6
./run.sh --skip_data_prep true --skip_train true
./run.sh --nj 8 --inference_nj 4
./run.sh --ngpu 1
```

Stage numbers vary by task script and repository revision. Use `./run.sh --help` or task script help to confirm exact stage meanings before running expensive work.

## Audio formatting

`format_wav_scp.py` and its shell wrapper convert audio referenced by `wav.scp` into the format expected by the downstream model. Common options include `--audio_format`, `--fs`, `--ref_channels`, `--segments`, `--multi_columns_input`, and `--multi_columns_output`. Typical ASR recipes use 16 kHz linear PCM or FLAC, but ESPnet2 can load all formats supported by `soundfile` when the rest of the workflow permits it.
