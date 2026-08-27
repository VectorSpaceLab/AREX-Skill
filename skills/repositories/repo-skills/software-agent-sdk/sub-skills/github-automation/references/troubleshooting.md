# GitHub Automation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Runner exits because both prompt sources are set | Conflicting configuration. | Provide either `PROMPT_STRING` or a prompt location, not both. |
| Prompt cannot be loaded | File missing, bad URL, or permission issue. | Verify the path/URL and keep the prompt text small and explicit. |
| Example report omits cost | Example did not print `EXAMPLE_COST:`. | Update the example or its runner so the marker is always emitted. |
| TODO scan returns too much noise | Identifier or filters are too broad. | Narrow the identifier and keep the default exclusions for tests and example directories. |
| GitHub Action fails without credentials | Missing `LLM_API_KEY` or repo permissions. | Configure the required secret and GitHub token permissions in the workflow. |
