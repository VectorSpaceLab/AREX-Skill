# Python API reference

This reference covers the public evo objects and helpers that are most useful when embedding evo into a custom Python script or notebook.

## Trajectory and metric helpers

- `evo.main_ape.ape(...) -> Result` — high-level APE helper used by the CLI and by programmatic scripts.
- `evo.main_rpe.rpe(...) -> Result` — high-level RPE helper used by the CLI and by programmatic scripts.
- `evo.core.metrics.APE(...)` and `evo.core.metrics.RPE(...)` — lower-level metric constructors when you want finer control.
- `evo.core.sync.associate_trajectories(...)` — timestamp association helper for paired trajectories.
- `evo.core.trajectory.PosePath3D` and `PoseTrajectory3D` — core data containers for path-only and timestamped trajectories.
- `evo.core.trajectory_bundle.TrajectoryBundle` — batch operations over multiple trajectories.

## File and pandas helpers

- `evo.tools.file_interface` — read/write TUM, KITTI, EuRoC, ROS bag, ROS2 bag, MCAP, result zips, and transform files.
- `evo.tools.pandas_bridge.trajectory_to_df(...)`
- `evo.tools.pandas_bridge.df_to_trajectory(...)`
- `evo.tools.pandas_bridge.result_to_df(...)`
- `evo.tools.pandas_bridge.load_results_as_dataframe(...)`

## Plotting helpers

- `evo.tools.plot.PlotCollection` — collects one or more figures for showing or exporting.
- `evo.tools.plot.prepare_axis(...)` — creates 2D or 3D trajectory axes.
- `evo.tools.plot.traj(...)` — plots a trajectory line.
- `evo.tools.plot.traj_colormap(...)` — plots a trajectory with scalar coloring.
- `evo.tools.plot.error_array(...)` — plots raw metric values.
- `evo.tools.plot.apply_settings(...)` — applies the current package plot settings.

## Optional integrations

- `evo.tools.rerun_bridge` — helper layer for Rerun streaming, including trajectory, scalar, and statistics senders.
- `evo.tools.contextily_helper` — map-tile provider selection and API-token handling for georeferenced plots.
- `evo.tools.settings.SETTINGS` — shared settings container used by plotting, Rerun, and export helpers.

## Practical notes

- The plotting helpers and Rerun helpers expect the evo settings object to be initialized; importing `evo.tools.settings` does that automatically.
- `PlotCollection.export()` can write a single PDF when the collection is not split, or one file per figure when split output is configured.
- `contextily_helper.get_provider()` only works with actual tile providers, not with provider bunches.
- `rerun_bridge` requires `rerun-sdk >= 0.34.0`.
