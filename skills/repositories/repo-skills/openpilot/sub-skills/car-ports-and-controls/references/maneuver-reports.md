# Maneuver Reports

`openpilot/tools/lateral_maneuvers/generate_report.py` and `openpilot/tools/longitudinal_maneuvers/generate_report.py` turn uploaded route logs into HTML reports that summarize maneuver timing, validity, and measured response. They are useful for tuning and PR evidence, but they are not safe vehicle commands by themselves.

## Reading the output

- Report titles include platform, route, and commit metadata.
- Each maneuver block can indicate whether the run was valid or invalid.
- Cross-time metrics show how long it took actual response to cross the target threshold.
- The report may embed plots and open a browser tab.

## Preconditions

- A route must already exist and be accessible in the local log store or through `LogReader`.
- Real-world maneuver collection requires a safe area, the appropriate device mode/parameter, and explicit driver oversight.
- If the task is only interpreting an existing report, no live vehicle actions are needed.
