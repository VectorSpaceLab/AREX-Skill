# Exploration workflows

AppAgent's exploration phase creates the UI documentation that deployment will later consume.

## Mode 1: autonomous exploration

Goal: let AppAgent infer the function of UI elements while it tries to complete a task on its own.

### Flow
1. Start from the target app's main interface on the device or emulator.
2. Provide the app name and a task description.
3. AppAgent captures screenshots and UI XML on each round.
4. The model proposes the next action in the `Observation / Thought / Action / Summary` format.
5. The action is executed on the device.
6. The reflection step decides whether the action was useful and may write documentation for the interacted element.
7. The loop ends when the task finishes, the max-round limit is reached, or a failure occurs.

### Outputs
- `apps/<app>/demos/self_explore_<timestamp>/...`
- `apps/<app>/auto_docs/<ui_element_id>.txt`
- exploration logs in the same demo directory

## Mode 2: human demonstration

Goal: show AppAgent how to perform a similar task so it can write documentation from before/after screenshots.

### Flow
1. Start the demo on the device.
2. Provide the app name and a task description.
3. The recorder labels interactive elements and asks you which action to perform.
4. Each recorded step is saved with the chosen action and the target resource id.
5. After the demo ends, documentation generation runs over the recorded steps and writes the per-element docs.

### Outputs
- `apps/<app>/demos/demo_<app>_<timestamp>/raw_screenshots/`
- `apps/<app>/demos/demo_<app>_<timestamp>/labeled_screenshots/`
- `apps/<app>/demos/demo_<app>_<timestamp>/record.txt`
- `apps/<app>/demo_docs/<ui_element_id>.txt`

## Mode selection guidance
- Use autonomous exploration when you want AppAgent to infer the task flow on its own.
- Use human demonstration when you already know the task path and want more accurate docs.
- Turn on `DOC_REFINE=true` when you want to improve an existing doc instead of skipping repeated UIDs.

## Operational details
- The element labels come from clickable and focusable nodes in the UIAutomator tree.
- The labeling step suppresses near-duplicate elements using `MIN_DIST`.
- Reflection outputs `BACK`, `CONTINUE`, `SUCCESS`, or `INEFFECTIVE`.
- Documentation is saved per UI resource id, not per screenshot.
