# Deployment workflows

Deployment is the phase that uses previously generated docs to complete a new app task.

## Standard flow
1. Start from the app's main interface on the device or emulator.
2. Choose the app name and provide a task description.
3. AppAgent looks for `apps/<app>/auto_docs/` and `apps/<app>/demo_docs/`.
4. If both exist, it asks which docs base to use.
5. If only one exists, it selects that base automatically.
6. If no docs exist, you can either stop or continue in no-doc mode.
7. The controller captures screenshots and UI XML, labels interactable nodes, and asks the multimodal backend for the next action.
8. The action parser converts the response into a device command.
9. The loop continues until the task is finished, the max-round limit is reached, or a failure occurs.

## Output layout
- `tasks/task_<app>_<timestamp>/`
  - `log_<app>_task_<app>_<timestamp>.txt`
  - per-round labeled screenshots
  - per-round UI XML dumps
  - optional grid screenshots

## Docs-base selection rules
- **Auto docs only:** the app was explored autonomously before.
- **Demo docs only:** the app was documented from a human demonstration.
- **Both bases:** choose one explicitly.
- **No docs:** deployment can still proceed, but reliability is lower.

## Grid overlay path
- Use the grid overlay when a target area is not exposed as a labeled UI element.
- The grid path lets the model choose an area/subarea pair instead of a numbered node.
- Because this path depends on precise coordinate mapping, it is more fragile than normal element actions.

## Useful task families
Deployment is often used for benchmark-style app tasks such as:
- navigation and maps,
- social posting and messaging,
- shopping and coupon flows,
- video and music playback tasks,
- email composition and attachments,
- alarms and clock settings.

These are examples of the kinds of tasks AppAgent was evaluated on; they are not the same as executable unit tests.
