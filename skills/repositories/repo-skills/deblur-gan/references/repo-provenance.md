# DeblurGAN repo provenance

- schema: `disco.repo-provenance.v1`
- canonical_skill_id: `deblur-gan`
- source_repository: `DeblurGAN`
- source_commit: `2499a87f96f34f262ea294c7e4cd3fd7e90251f8`
- branch: `master`
- exact_tag: `none`
- dirty_state: `dirty checkout; untracked skills/`
- package_version: `not declared in repository metadata`
- public_remote_url: `omitted-private-or-unknown`

## Relative evidence paths

- `README.md`
- `train.py`
- `test.py`
- `options/base_options.py`
- `options/train_options.py`
- `options/test_options.py`
- `data/aligned_dataset.py`
- `data/single_dataset.py`
- `data/unaligned_dataset.py`
- `data/image_folder.py`
- `datasets/combine_A_and_B.py`
- `models/conditional_gan_model.py`
- `models/networks.py`
- `models/losses.py`
- `models/test_model.py`
- `util/metrics.py`
- `util/visualizer.py`
- `util/html.py`
- `util/util.py`
- `util/get_data.py`
- `checkpoints/experiment_name/opt.txt`
- `checkpoints/experiment_name/web/index.html`

## Notes

- The repository has no `pyproject.toml`, `setup.py`, `setup.cfg`, or requirements lockfile.
- The generated skill therefore uses the source tree, the README, and installed-package inspection as the canonical evidence set.
- Generated runtime guidance should not depend on the original checkout path or on the inspection environment used to build this skill.
