# AppAgent workflow overview

AppAgent has two end-user phases:

1. **Exploration** — generate documentation for UI elements by either autonomous exploration or a human demonstration.
2. **Deployment** — use the generated documentation to complete a new task on the same app.

The generated skill routes the two phases into separate sub-skills, but they share the same setup, config, device, and adb prerequisites.

## Shared output layout
- `apps/<app>/demos/<demo_name>/...` — exploration/demo artifacts
- `apps/<app>/auto_docs/` — docs from autonomous exploration
- `apps/<app>/demo_docs/` — docs from human demonstration
- `tasks/task_<app>_<timestamp>/...` — deployment logs and screenshots

## Representative task families from the benchmark
The repository's benchmark overview focuses on nine app families. These are useful as mental models for the kinds of tasks AppAgent can be asked to do:

| App family | Example task style |
| --- | --- |
| Google Maps | search, route planning, navigation |
| X | post, follow, community actions, profile edits |
| Telegram | chat, profile settings, groups, theme changes |
| Temu | shopping, coupons, cart, payment settings |
| YouTube | search, comment, subscribe, share, playback settings |
| Spotify | artist search, playlist edits, profile changes, playback settings |
| Yelp | restaurant search, filtering, reviews, recent views |
| Gmail | send mail, attachments, scheduling, drafts |
| Clock | alarms, world clock, style changes, bedtime settings |

## When to route where
- Use **exploration** when you need the app documentation base or want to capture new UI knowledge.
- Use **deployment** when a documentation base already exists and the goal is to complete a task.
- If docs are missing, decide whether to generate them first or proceed in no-doc mode with lower reliability.
