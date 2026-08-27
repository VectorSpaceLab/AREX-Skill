# Gemini Enterprise registration

## Supported registration styles
### ADK agents on Agent Engine
- Use the Agent Engine resource ID or the deployment metadata file.
- The command can infer the project number and display metadata when available.

### A2A agents on Cloud Run or GKE
- Use an agent card URL.
- The card URL may be constructed from deployment metadata when the information exists.

## Important ID shapes
- Agent Engine ID: `projects/<project-number>/locations/<region>/reasoningEngines/<engine-id>`
- Gemini Enterprise app ID: `projects/<project-number>/locations/<location>/collections/<collection>/engines/<engine-id>`

## What the workflow does
- Resolves project identity and project number.
- Discovers available Gemini Enterprise apps when possible.
- Picks or confirms the registration target.
- Builds the console URL for the resulting registration.

## Helpful environment cues
- `deployment_metadata.json`
- `AGENT_CARD_URL`
- `GEMINI_ENTERPRISE_APP_ID`
- `ID`
- `GEMINI_DESCRIPTION`
- `GEMINI_DISPLAY_NAME`
- `GEMINI_TOOL_DESCRIPTION`

## Troubleshooting cues
- Invalid resource-name format.
- Authentication failure against Google Cloud.
- No accessible Gemini Enterprise app is found in the selected project.
- An A2A agent card cannot be fetched from the provided URL.
