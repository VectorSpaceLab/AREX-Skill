# KAIR repo provenance and evidence

- Schema: `disco.repo-provenance.v1`

## Source anchor

- Repository: `https://github.com/cszn/KAIR.git`
- Checked branch: `master`
- Checked commit: `fc1732f4a4514e42ce15e5b3a1e18c828af47a1e`
- Working tree state at integration: source tree unchanged except generated `skills/` artifacts.
- Package/import version: not applicable; KAIR is a source-script repository with no installable package metadata.
- Packaging: source-script repository; no `pyproject.toml`, `setup.py`, or `setup.cfg` was present.
- Generation policy: create a repository-specific operating skill for DisCo Researcher, do not import it automatically.

## Generated skill layout

- Root skill: `skills/disco/kair/SKILL.md`
- Sub-skills:
  - `skills/disco/kair/sub-skills/image-training/`
  - `skills/disco/kair/sub-skills/image-testing/`
  - `skills/disco/kair/sub-skills/video-restoration/`
  - `skills/disco/kair/sub-skills/data-preparation/`
- Integration and verification artifacts: `skills/tests/kair/`

## Primary repository evidence inspected

- `README.md`, `model_zoo/README.md`, `trainsets/README.md`, `testsets/README.md`, `matlab/README.md`, `retinaface/README.md`.
- `docs/README_SwinIR.md`, `docs/README_VRT.md`, `docs/README_RVRT.md`.
- Training entry points: `main_train_dncnn.py`, `main_train_drunet.py`, `main_train_psnr.py`, `main_train_gan.py`, `main_train_usrnet.py`, `main_train_vrt.py`.
- Testing entry points: `main_test_dncnn.py`, `main_test_fdncnn.py`, `main_test_ffdnet.py`, `main_test_dncnn3_deblocking.py`, `main_test_ircnn_denoiser.py`, `main_test_srmd.py`, `main_test_dpsr.py`, `main_test_msrresnet.py`, `main_test_rrdb.py`, `main_test_imdn.py`, `main_test_usrnet.py`, `main_test_swinir.py`, `main_test_face_enhancement.py`, `main_test_vrt.py`, `main_test_rvrt.py`, `main_challenge_sr.py`, `main_download_pretrained_models.py`.
- Core routing modules: `utils/utils_option.py`, `utils/utils_lmdb.py`, `utils/utils_video.py`, `data/select_dataset.py`, `data/dataset_video_train.py`, `data/dataset_video_test.py`, `models/select_model.py`, `models/select_network.py`, `models/network_rvrt.py`, `models/network_faceenhancer.py`, and `models/op/*.py`.
- Data preparation and evaluation helpers under `scripts/data_preparation/` and `scripts/matlab_scripts/`.
- Option templates under `options/`, including `options/swinir/`, `options/vrt/`, and `options/rvrt/`.

## Runtime evidence captured during construction

The private inspection environment verified these facts before skill writing:

- `requirement.txt` dependencies can be installed in an isolated environment.
- `torch` was CUDA-capable and detected A100-class GPUs in the construction environment.
- `nvcc`, `ninja`, and CUDA extension imports were available after setting the correct CUDA toolkit and extension cache environment variables.
- Safe parser/help checks succeeded for representative scripts: `main_download_pretrained_models.py`, `main_test_dncnn.py`, `main_test_swinir.py`, `main_train_psnr.py`, `main_test_vrt.py`, and `main_test_rvrt.py`.
- Live signatures were captured for `data.select_dataset.define_Dataset`, `models.select_model.define_Model`, `utils.utils_option.parse`, `utils.utils_lmdb.make_lmdb_from_imgs`, and representative network constructors.

Private environment paths and shell-specific details are intentionally omitted from the public skill. The public operating guidance describes requirements and portable checks instead.

## Scope boundaries

Included:

- Image model training with KAIR option JSONs and training entry scripts.
- Image restoration testing/inference command selection and hard-coded script cautions.
- VRT/RVRT video restoration testing and training command selection.
- Dataset layout, meta-info, subimage extraction, LMDB planning, and destructive data-preparation warnings.
- Model-zoo/download selection and environment readiness checks.

Excluded or reference-only:

- Full native training and full native inference during construction.
- MATLAB evaluation execution.
- Destructive dataset regrouping/move/copy scripts.
- Importing this skill into live routers or external agents.
