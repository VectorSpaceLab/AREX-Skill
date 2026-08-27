# Installation and dependency guidance

AB3DMOT is a repository-oriented Python project. It does not expose a packaged console entry point; most workflows run Python scripts from an AB3DMOT checkout or use modules from `AB3DMOT_libs` through `PYTHONPATH`.

## Documented baseline

The repository documentation states it was tested on:

- Ubuntu 18.04
- Python 3.6

Documented base dependencies include:

```text
numpy                 # required by AB3DMOT_libs
scipy                 # required by dist_metrics/matching
wheel
scikit-learn
filterpy
numba
matplotlib
pillow
opencv-python
glob2
PyYAML
easydict
llvmlite
```

NumPy and SciPy are core runtime requirements even though the historical
upstream `requirements.txt` omitted them. Use versions compatible with the
selected Python and the other pins; the old Python 3.6 baseline generally
requires older NumPy/SciPy wheels. Xinshuo is **not** a PyPI dependency that
this skill can pin reliably: it is an external `Xinshuo_PyToolbox` checkout
and must be installed separately or supplied through `--toolbox-root` /
`PYTHONPATH`.

AB3DMOT also depends on the Xinshuo Python toolbox. A runtime must make toolbox modules such as `xinshuo_io`, `xinshuo_miscellaneous`, `xinshuo_visualization`, and `xinshuo_video` importable.

## Practical setup pattern

The following install commands run **inside the AB3DMOT checkout**, not inside
the generated skill directory:

```bash
cd /path/to/AB3DMOT
python -m pip install -r requirements.txt
# clone/install Xinshuo_PyToolbox separately, following its own requirements
export PYTHONPATH="${PYTHONPATH}:$(pwd):/path/to/Xinshuo_PyToolbox"
python main.py --help
```

The generated checker is a separate, read-only skill helper. Run it from the
generated skill directory (or use its absolute path) and always identify the
checkout with `--repo-root`; its cwd is not the checkout cwd:

```bash
cd /path/to/generated-skill/skills/disco/ab3dmot
python scripts/ab3dmot_environment_check.py \
  --repo-root /path/to/AB3DMOT \
  --toolbox-root /path/to/Xinshuo_PyToolbox \
  --smoke-track
```

For modern hosts, exact old pins may not have wheels for the available Python. Use a compatible Python version and equivalent package versions only after verifying imports and a small smoke check.

## Synthetic smoke checks

The tracking smoke also takes explicit roots and adds them to `sys.path` before
importing AB3DMOT. It does not need ambient `PYTHONPATH`:

```bash
python /path/to/generated-skill/skills/disco/ab3dmot/sub-skills/tracking-pipeline/scripts/smoke_track_synthetic.py \
  --repo-root /path/to/AB3DMOT \
  --toolbox-root /path/to/Xinshuo_PyToolbox
```

The checker above additionally performs import/config/help checks. Missing
checkout and missing Xinshuo are reported separately; evaluator/export help is
checked where those CLIs expose `--help`, while legacy positional evaluators
are explicitly reported as not checked. It does not download data or run full
tracking/evaluation.

## Import facts to expect

Core imports should include:

```python
from AB3DMOT_libs.model import AB3DMOT
from AB3DMOT_libs.box import Box3D
from AB3DMOT_libs.matching import data_association
from AB3DMOT_libs.utils import Config, get_subfolder_seq, get_threshold
```

Live inspection confirmed these signatures for the source snapshot used by this skill:

```text
AB3DMOT.__init__(self, cfg, cat, calib=None, oxts=None, img_dir=None, vis_dir=None, hw=None, log=None, ID_init=0)
AB3DMOT.track(self, dets_all, frame, seq_name)
Box3D.__init__(self, x=None, y=None, z=None, h=None, w=None, l=None, ry=None, s=None)
data_association(dets, trks, metric, threshold, algm='greedy', trk_innovation_matrix=None, hypothesis=1)
```

## Known warnings

- Newer Python interpreters emit `SyntaxWarning` for `is`/`is not` comparisons with string literals in a few files. Treat this as a compatibility warning unless it becomes an exception under a future runtime.
- Numba may emit deprecation warnings for `@jit` without an explicit `nopython` argument. If tracking still runs and smoke checks pass, these warnings are not dataset failures.
- Missing Xinshuo toolbox modules are the most common import blocker after installing `requirements.txt`.
