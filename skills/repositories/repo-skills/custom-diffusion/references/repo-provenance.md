# Repo provenance

- repo: custom-diffusion
- source_commit: `7c19c9a7820d07389f5390e09d7b85d702bafd7b`
- branch: `main`
- exact_tag: none
- working_tree_state: dirty because of generated `skills/` output and review artifacts only
- packaging_state: not-packaged; the checkout has no `pyproject.toml`, `setup.py`, `setup.cfg`, or requirements file
- generated_against: Python 3.11.15 with a CUDA-capable inspection stack

## Verified runtime versions

- torch 2.5.1
- torchvision 0.20.1
- diffusers 0.21.4
- accelerate 0.24.1
- transformers 4.31.0
- clip-retrieval 2.45.0
- pandas 2.3.3
- scipy 1.17.1
- scikit-learn 1.9.0
- huggingface-hub 0.20.3
- setuptools 80.9.0

## Source evidence used

- `README.md`
- `assets/concept_list.json`
- `customconcept101/README.md`
- `customconcept101/dataset.json`
- `customconcept101/dataset_multiconcept.json`
- `customconcept101/evaluate.py`
- `src/diffusers_data_pipeline.py`
- `src/diffusers_model_pipeline.py`
- `src/diffusers_sample.py`
- `src/diffusers_training.py`
- `src/diffusers_training_sdxl.py`
- `src/get_deltas.py`
- `src/compress.py`
- `src/diffusers_composenW.py`
- `src/retrieve.py`
- `train.py`
- `sample.py`
- `configs/custom-diffusion/*.yaml`
- `scripts/finetune_gen.sh`
- `scripts/finetune_joint.sh`
- `scripts/finetune_real.sh`

## Refresh baseline

Re-run extraction if the source commit changes, the diffusers or accelerate versions move materially, or the checkout gains packaging metadata that changes install guidance.
