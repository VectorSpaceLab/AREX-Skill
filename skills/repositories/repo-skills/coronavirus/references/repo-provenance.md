# Repository provenance

- **Source project:** Folding@home coronavirus preparation repository
- **Source commit:** `19f9f08f66368b565710d501604ce95e1fb6ca98`
- **Source branch:** `master`
- **Source dirty state at extraction:** dirty from local/untracked skill production artifacts; the source commit above is the content baseline.
- **Installable package metadata:** no `pyproject.toml`, `setup.py`, requirements file, or installable Python package was found in the source repository. This skill therefore captures repository workflows and verified OpenMM ecosystem behavior rather than a package release API.
- **Inspection facts used:** OpenMM 8.6.0; OpenMMTools 0.26.0; OpenMMForceFields 0.16.0; PDBFixer 1.12.0; ParmEd 4.3.1; progressbar2 4.6.0; OpenFF Toolkit 0.18.0. These are extraction evidence, not runtime-pinned installation requirements.
- **Required backend:** CPU OpenMM. CUDA was enumerated but context creation was limited by `CUDA_ERROR_UNSUPPORTED_PTX_VERSION`; it remains optional and unverified.

## Relative evidence paths

- `README.md`
- `system-preparation/README.md`
- `system-preparation/2ajf_sars-2/README.md`
- `system-preparation/6lu7_receptor/README.md`
- `system-preparation/6lu7_complex/README.md`
- `system-preparation/6vsb_rbd/README.md`
- `system-preparation/6lu7_receptor/simulate_6lu7_receptor.py`
- `system-preparation/6lu7_receptor/simulate_4amu_4fs.py`
- `system-preparation/6lu7_complex/simulate_6lu7_complex.py`
- `system-preparation/6lu7_complex/edit_residues.py`
- `system-preparation/6acg_6vsb/truncate_6acg_6vsb.py`
- `system-preparation/6vsb_rbd/keep_rbd.py`
- `system-preparation/swiss_models/4fs_simulate.py`
- `potential-targets/README.md`
- `potential-targets/target_template.md`
- `publications/README.md`
- `publications/README_template.md`

The generated helpers deliberately replace source-relative, hard-coded, or long-running scripts with explicit-argument bounded versions. No source checkout, private environment, large structure corpus, archive, PDF, trajectory, or generated state is required at runtime.
