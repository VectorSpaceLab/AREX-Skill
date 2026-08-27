# Testing and Contributing to ESPnet

ESPnet contributor work falls into major features, minor fixes, and recipes. Major features should be discussed through issues before implementation. Recipe contributions must preserve reproducibility, shared-file conventions, and result/model publication expectations.

## Python tests

- Tests live under `test/` and use `test_*.py` files with `test_*` functions.
- Prefer focused small tests over one large integration test.
- Use `pytest --cov-report term-missing <path>` when checking coverage.
- ESPnet uses timeout-aware pytest settings; keep tests small and mark longer tests only when justified.
- Focused examples:
  ```bash
  pytest -q test/espnet2/bin/test_asr_train.py
  pytest -q test/espnet2/tasks/test_asr.py
  pytest -q test/espnet3/utils/test_stages.py
  ```

## CI and style

ESPnet uses Black/isort-compatible style conventions, pycodestyle/flake8 ignore settings from project config, and CI scripts under `ci/`. Broad CI scripts can be slow and dependency-heavy; select focused checks based on changed files.

## Recipe contribution policy

For new or modified ESPnet2 recipes:

- Keep common/shared files (`utils`, `steps`, task scripts, cluster configs) linked or generated from templates.
- Preserve default scheduler configs (`cmd.sh`, `conf/slurm.conf`, `conf/queue.conf`, `conf/pbs.conf`) unless intentionally changing infrastructure.
- Update recipe indexes and `db.sh` entries when adding corpora.
- Keep initial configs simple and place variants in `conf/tuning/`.
- Include results and pretrained model information when appropriate.
- Do not upload models or create Hugging Face assets without credentials and maintainer approval.
