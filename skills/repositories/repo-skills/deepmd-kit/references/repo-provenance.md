# Repo Provenance

```yaml
schema: disco.repo-provenance.v1
skill_id: deepmd-kit
source:
  vcs: git
  commit: b52c359ec6b6f6f34998e00f774c35d253cf09e5
  branch: master
  tag: null
  remote_url: https://github.com/deepmodeling/deepmd-kit
working_tree:
  dirty: true
  note: Generated skill artifacts were present during provenance capture; source code evidence was otherwise read-only for this skill creation run.
package:
  distribution: deepmd-kit
  import: deepmd
  inspected_version: 0.0.0+inspection
  public_version_source: dynamic setuptools_scm metadata
inspection:
  live_checks:
    - import deepmd
    - importlib.metadata.version('deepmd-kit')
    - deepmd.main.main_parser()
    - python -m deepmd -h with backend imports disabled for parser inspection
  limitations:
    - Heavy TensorFlow CPU runtime wheel download timed out in the private inspection environment.
    - Backend runtime smoke tests were not used as final public claims; source docs and parser/source evidence were used for backend guidance.
```

## Evidence Paths

- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `doc/install/`
- `doc/backend.md`
- `doc/data/`
- `doc/train/`
- `doc/model/`
- `doc/freeze/`
- `doc/test/`
- `doc/inference/`
- `doc/third-party/`
- `doc/troubleshooting/`
- `deepmd/`
- `backend/`
- `source/api_c/`
- `source/api_cc/`
- `source/lib/`
- `source/op/`
- `source/lmp/`
- `source/ipi/`
- `source/nodejs/`
- `source/install/`
- `source/tests/`
- `examples/`
- `skills/deepmd-train/`
- `skills/deepmd-finetune-dpa3/`
- `skills/deepmd-python-inference/`
- `skills/lammps-deepmd/`

## Refresh Guidance

Refresh this skill when DeePMD-kit changes CLI flags, backend aliases, model artifact formats, training input schema, data layout support, LAMMPS/i-PI/native API syntax, package extras, build environment variables, or maintainer build/test instructions.
