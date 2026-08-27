# Recipe and Data Troubleshooting

## Common data-layout failures

- **`text` key missing from `utt2spk`**: regenerate speaker mappings so every utterance has exactly one speaker.
- **`spk2utt` mismatch**: rebuild `spk2utt` from `utt2spk` or vice versa; the bundled validator reports the mismatched speaker.
- **`segments` recording not in `wav.scp`**: remember that `wav.scp` keys are recording ids when `segments` exists.
- **`end <= start` in `segments`**: fix timestamp extraction before audio formatting.
- **Audio command-pipe failure**: check host tools (`ffmpeg`, `sph2pipe`, `sox`) and shell quoting.

## Recipe execution failures

- **Wrong current directory**: run from `egs2/<dataset>/<task>`, where `path.sh`, `cmd.sh`, `utils/`, and task scripts are visible.
- **Missing corpus roots**: edit `db.sh` or use an already-downloaded corpus path; do not start downloads without approval.
- **Stage confusion**: stage numbers vary by task. Use `./run.sh --help` or the task script before running expensive ranges.
- **Skipping too much**: `--skip_data_prep true` and `--skip_train true` require already-existing artifacts.
- **Cluster command failure**: check `cmd.sh` and scheduler configs before blaming ESPnet Python modules.

## Tokenization and audio formatting

- `tokenize_text` BPE mode needs a `--bpemodel`; phoneme/G2P modes may need language-specific dependencies.
- `format_wav_scp` command-pipe examples require shell tools and can duplicate large corpora; ask before converting full datasets.
- Multi-channel `wav.scp` rows need consistent channel handling through `--multi_columns_input` or `--multi_columns_output`.
