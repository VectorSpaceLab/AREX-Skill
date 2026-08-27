# Repo Provenance

## Source snapshot

| Field | Value |
|---|---|
| Repository | Muzic |
| Public remote | `https://github.com/microsoft/muzic.git` |
| Branch | `main` |
| Commit | `2b8739671ba06f819f31f568b8a79da581aaf6f9` |
| Commit date | `2026-08-06 05:14:32 +0800` |
| Commit subject | `[MusicBERT] Fix expired download link` |
| Exact tag | none detected |
| Package version | none; this repository has no single package metadata file |
| Working tree state during skill generation | dirty only because generated `skills/` artifacts were created |

## Evidence paths used

Root evidence:

- `README.md`
- `requirements.txt`
- `LICENSE`

Music understanding and retrieval evidence:

- `musicbert/README.md`
- `musicbert/preprocess.py`
- `musicbert/gen_nsp.py`
- `musicbert/gen_genre.py`
- `musicbert/binarize_pretrain.sh`
- `musicbert/binarize_nsp.sh`
- `musicbert/binarize_genre.sh`
- `musicbert/train_mask.sh`
- `musicbert/train_nsp.sh`
- `musicbert/train_genre.sh`
- `musicbert/eval_nsp.py`
- `musicbert/eval_genre.py`
- `pdaugment/README.md`
- `pdaugment/flac2wav.py`
- `pdaugment/text2phone.py`
- `pdaugment/pdaugment.py`
- `pdaugment/midi_preprocess/`
- `pdaugment/utils/frequency.json`
- `clamp/README.md`
- `clamp/clamp.py`
- `clamp/utils.py`
- `clamp/inference/`

Lyric and melody songwriting evidence:

- `deeprapper/README.md`
- `deeprapper/train.py`
- `deeprapper/generate.py`
- `deeprapper/*.sh`
- `deeprapper/tokenizations/`
- `deeprapper/config/`
- `songmass/README.md`
- `songmass/*.sh`
- `songmass/data/`
- `songmass/evaluate/`
- `songmass/mass/`
- `telemelody/README.md`
- `telemelody/training/`
- `telemelody/inferrence/`
- `telemelody/evaluation/`
- `telemelody/test/`
- `relyme/Readme.md`
- `relyme/score/`
- `relyme/telemelody_en/`
- `relyme/telemelody_zh/`
- `relyme/songmass_en/`
- `relyme/songmass_zh/`
- `roc/README.md`
- `roc/lyrics_to_melody.py`
- `roc/gen.py`
- `roc/utils/`
- `roc/lyrics.txt`
- `roc/chord.txt`

Symbolic generation and structure evidence:

- `getmusic/README.md`
- `getmusic/track_generation.py`
- `getmusic/position_generation.py`
- `getmusic/preprocess/`
- `getmusic/configs/train.yaml`
- `getmusic/example_data/`
- `getmusic/getmusic/`
- `musecoco/README.md`
- `musecoco/1-text2attribute_dataprepare/`
- `musecoco/1-text2attribute_model/`
- `musecoco/2-attribute2music_dataprepare/`
- `musecoco/2-attribute2music_model/`
- `musecoco/evaluation/`
- `musecoco/requirements.txt`
- `museformer/README.md`
- `museformer/tools/`
- `museformer/ttrain/`
- `museformer/tval/`
- `museformer/tgen/`
- `museformer/museformer/`
- `museformer/data/meta/`
- `meloform/README.md`
- `meloform/*.py`
- `meloform/*.sh`
- `meloform/meloform/`
- `meloform/data/`
- `emogen/readMe.md`
- `emogen/*.sh`
- `emogen/data_process/`
- `emogen/jSymbolic_lib/`
- `emogen/linear_decoder/`

MusicAgent evidence:

- `musicagent/README.md`
- `musicagent/agent.py`
- `musicagent/gradio_agent.py`
- `musicagent/plugins.py`
- `musicagent/model_utils.py`
- `musicagent/config.yaml`
- `musicagent/models/download.sh`
- `musicagent/skills/`

## Refresh guidance

Refresh this skill if the Muzic repository changes its top-level project list, per-project README commands, dependency pins, CLaMP model names, MusicAgent config fields, checkpoint locations, or script argument names. Because there is no package version, compare future checkouts by Git commit and the relative evidence paths above.
