# teams-autonomous-prebuilt Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AutonomousAgent` refuses a command | The sandbox blocked a dangerous or out-of-workspace command. | Rewrite the command to stay inside the workspace and keep it shell-safe. |
| A prebuilt agent cannot find its template assets | The template directory is missing or the packaged layout changed. | Re-check the prebuilt template files and the bundled inspection helper. |
| `RalphLoop` stops too early | The test/build/lint backpressure command failed or a max-iteration guard triggered. | Fix the validation command or increase the safety limit only after the failure is understood. |
| A simulation step cannot be executed | The simulation object or the model output schema is invalid. | Validate the domain object and the step-output schema separately before rerunning. |
| Team routing feels random | The mode or router/leader configuration is not set the way you expect. | Re-check the team mode and the router/leader inputs before changing the agents. |

## Smoke check

```bash
python sub-skills/teams-autonomous-prebuilt/scripts/inspect_prebuilt_templates.py
```
