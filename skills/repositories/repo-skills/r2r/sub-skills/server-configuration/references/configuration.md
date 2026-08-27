# Configuration Reference

## Install and package shape

- Public Python package: `r2r`
- Common install: `pip install r2r`
- Server/runtime extras: `pip install 'r2r[core]'`
- Requires Python 3.10 through 3.12

## Common built-in config names

- `full`
- `full_azure`
- `full_lm_studio`
- `full_ollama`
- `gemini`
- `lm_studio`
- `ollama`
- `r2r_azure`
- `r2r_azure_with_test_limits`
- `r2r_with_auth`
- `tavily`

## Important environment variables

- `R2R_CONFIG_NAME`
- `R2R_CONFIG_PATH`
- `R2R_HOST`
- `R2R_PORT`
- `R2R_PROJECT_NAME`
- `R2R_POSTGRES_USER`
- `R2R_POSTGRES_PASSWORD`
- `R2R_POSTGRES_HOST`
- `R2R_POSTGRES_PORT`
- `R2R_POSTGRES_DBNAME`
- provider keys such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `VERTEX_API_KEY`, and `XAI_API_KEY`

## Configuration guidance

- Use a config name for the documented presets and a config path when you have a custom TOML file.
- Put deployment-specific overrides in env vars instead of editing the packaged defaults when possible.
- Keep `R2R_PROJECT_NAME` aligned between the server and any client workflows that rely on project scoping.
