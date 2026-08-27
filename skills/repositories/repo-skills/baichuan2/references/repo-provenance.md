# Repo Provenance

## Source snapshot

- schema: `disco.repo-provenance.v1`
- repository: `Baichuan2`
- remote_url: `https://github.com/baichuan-inc/Baichuan2.git`
- branch: `main`
- commit: `ed8b1ae415c62b65a7d41b491ebeb854c54f0653`
- exact_tag: none detected
- package_version: not applicable; this checkout does not define an installable Python distribution version
- working_tree_state: dirty because generated repo-skill and review artifacts were created under `skills/`

## Dirty-state summary

The source evidence files were read from the Git checkout above. The dirty paths are generated construction outputs, primarily:

- `skills/disco/baichuan2/`
- `skills/tests/baichuan2/`
- `skills/Baichuan2.log`

No source workflow files were modified during skill construction.

## Evidence paths used

- `README.md`
- `README_EN.md`
- `requirements.txt`
- `OpenAI_api.py`
- `cli_demo.py`
- `web_demo.py`
- `fine-tune/fine-tune.py`
- `fine-tune/ds_config.json`
- `fine-tune/requirements.txt`
- `fine-tune/data/belle_chat_ramdon_10k.json`
- `LICENSE`

## Generated operating graph

- root skill: `SKILL.md`
- root references: `references/`
- root scripts: `scripts/`
- sub-skills: `sub-skills/inference/`, `sub-skills/deployment/`, `sub-skills/fine-tuning/`

Refresh this skill when the Baichuan2 README, demo scripts, fine-tuning script, dependency files, sample data schema, model-loading conventions, or license/citation text changes.
