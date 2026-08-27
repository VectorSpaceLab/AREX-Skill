---
schema: disco.repo-provenance.v1
source_repository: igel
public_remote_url: https://github.com/nidhaloff/igel.git
current_commit: bf4544d6c86ab4ace21254cb38a011ce3e845700
branch: master
exact_tag: none
dirty: false
package_version: 0.7.0
evidence_paths:
  - pyproject.toml
  - setup.cfg
  - tox.ini
  - Makefile
  - .github/workflows/build.yml
  - igel/__main__.py
  - igel/igel.py
  - igel/auto/cnn.py
  - igel/servers/fastapi_server.py
  - docs/README.rst
  - docs/usage.rst
  - docs/installation.rst
  - tests/test_igel/test_igel.py
  - examples/
---

# Igel repository provenance

- Source repository: `igel`
- Public remote URL: `https://github.com/nidhaloff/igel.git`
- Current commit: `bf4544d6c86ab4ace21254cb38a011ce3e845700`
- Branch: `master`
- Exact tag at HEAD: none
- Working tree state at analysis time: clean
- Package version from repository metadata: `0.7.0`
- Repository evidence paths used:
  - `pyproject.toml`
  - `setup.cfg`
  - `tox.ini`
  - `Makefile`
  - `.github/workflows/build.yml`
  - `igel/__main__.py`
  - `igel/igel.py`
  - `igel/auto/cnn.py`
  - `igel/servers/fastapi_server.py`
  - `docs/README.rst`
  - `docs/usage.rst`
  - `docs/installation.rst`
  - `tests/test_igel/test_igel.py`
  - `examples/`

## Refresh baseline

If the repository changes, refresh this skill when any of the following drift:

- command names or flags in `igel/__main__.py`
- core API signatures in `igel/igel.py` or `igel/auto/cnn.py`
- data/config assumptions in `igel/preprocessing.py` or `igel/configs.py`
- serving request/response behavior in `igel/servers/fastapi_server.py`
- example or test fixtures used as native verification candidates
