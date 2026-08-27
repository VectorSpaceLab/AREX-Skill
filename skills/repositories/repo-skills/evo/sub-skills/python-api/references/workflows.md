# Python API workflows

These recipes show how to use evo as a library instead of a shell command.

## 1. Copy-safe APE/RPE in a custom script

```python
from copy import deepcopy

from evo.core.metrics import PoseRelation, Unit
from evo.main_ape import ape
from evo.main_rpe import rpe

ape_result = ape(
    deepcopy(traj_ref),
    deepcopy(traj_est),
    PoseRelation.translation_part,
    align=True,
)
rpe_result = rpe(
    deepcopy(traj_ref),
    deepcopy(traj_est),
    PoseRelation.translation_part,
    delta=1,
    delta_unit=Unit.frames,
)
```

Use this pattern whenever you need the original inputs later, because the helpers mutate trajectories in place.

## 2. Build a notebook-friendly trajectory workflow

- Import `evo.tools.settings` early if you want the package settings initialized.
- Set the Matplotlib backend before importing plotting helpers when you are in a headless notebook or script.
- Use `sync.associate_trajectories()` before alignment if the trajectories carry timestamps.
- Convert to a DataFrame with `trajectory_to_df()` when you want notebook inspection or pandas operations.

## 3. Custom plotting and export

Create an output directory first if you are exporting to a new path. The snippet below assumes `traj_ref` and `traj_est` already exist in your script or notebook.

```python
from copy import deepcopy
from pathlib import Path

from evo.core.metrics import PoseRelation
from evo.main_ape import ape
from evo.tools import plot
import matplotlib.pyplot as plt

Path("out").mkdir(exist_ok=True)
ape_result = ape(
    deepcopy(traj_ref),
    deepcopy(traj_est),
    PoseRelation.translation_part,
    align=True,
)

plot_collection = plot.PlotCollection("Example")
fig = plt.figure(figsize=(8, 8))
ax = plot.prepare_axis(fig, plot.PlotMode.xy)
plot.traj(ax, plot.PlotMode.xy, traj_ref, "--", "gray", "reference")
plot.traj_colormap(
    ax,
    traj_est,
    ape_result.np_arrays["distances"],
    plot.PlotMode.xy,
    min_map=float(min(ape_result.np_arrays["distances"])),
    max_map=float(max(ape_result.np_arrays["distances"])),
)
plot_collection.add_figure("traj", fig)
plot_collection.export("out/example.pdf", confirm_overwrite=False)
```

## 4. Rerun and geo-tile integration

- Use `evo.tools.rerun_bridge` only when the `rerun-sdk` extra is installed.
- Use `evo.tools.contextily_helper.get_provider()` only when you have georeferenced data and the `geo` extra installed.
- If a map provider requires a token, set it through `evo_config` before plotting.

## 5. Notebook or IPython sessions

- `plot.apply_settings()` skips backend forcing inside IPython/Jupyter shells.
- If you need notebook graphics, configure the backend before the first plotting import.
- The source examples under `examples/` are best treated as recipes to distill, not as runtime dependencies.

## 6. Run the bundled smoke helper

```bash
python scripts/programmatic_api_smoke.py
```

This helper uses tiny synthetic trajectories to exercise APE/RPE, pandas round-tripping, and plot export without relying on repo fixtures.
