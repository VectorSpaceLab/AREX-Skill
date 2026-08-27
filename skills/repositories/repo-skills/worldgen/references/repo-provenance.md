# Repository Provenance

- **Repository**: WorldGen
- **Source commit**: `7ce7b2767fdf31e2727b69a2e61e2e950e3a017f`
- **Branch**: `main`
- **Exact tag**: none detected
- **Working tree state at skill creation**: dirty; the checkout contains generated `skills/` runtime and review artifacts in addition to the source snapshot
- **Package version**: `0.1.0`
- **Remote URL**: `https://github.com/ZiYang-xie/WorldGen.git`
- **Evidence paths**:
  - `README.md`
  - `pyproject.toml`
  - `demo.py`
  - `.gitmodules`
  - `src/worldgen/__init__.py`
  - `src/worldgen/worldgen.py`
  - `src/worldgen/pano_depth.py`
  - `src/worldgen/pano_gen.py`
  - `src/worldgen/pano_inpaint.py`
  - `src/worldgen/pano_seg.py`
  - `src/worldgen/pano_sharp.py`
  - `src/worldgen/utils/general_utils.py`
  - `src/worldgen/utils/splat_utils.py`
  - `src/worldgen/models/inpaint_model.py`

## Refresh baseline

Refresh this skill when the source commit or package version changes, or when
any listed evidence path changes materially. In particular, re-check the skill
if WorldGen changes its `WorldGen` constructor, adds a new generation mode,
changes output formats, changes its demo flags, updates the FLUX/DA-2/Nunchaku
stack, or changes the optional Sharp or background-inpainting paths.
