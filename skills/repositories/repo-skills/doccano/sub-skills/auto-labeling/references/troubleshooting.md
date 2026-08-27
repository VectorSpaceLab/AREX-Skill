# Auto-labeling troubleshooting

## Configuration failures

- **Unknown model name**: the selected template does not exist in `auto_labeling_pipeline`.
- **Attributes do not match the model**: provide every required request-model field before testing the request.
- **Template render error**: the response mapping template is malformed or the sample response does not contain the fields the template expects.
- **No labels created after running auto-labeling**: the project's label types do not match the labels returned by the mapping or the label map is incomplete.

## Runtime failures

- **Connection error**: the service endpoint cannot be reached.
- **AWS token error**: the credentials or region settings are invalid for the chosen AWS-backed template.
- **JSON decode error**: the external service returned something that was not valid JSON.
- **Empty sample result**: the request or mapping test returned no labels, so the configuration is not yet valid.

## Permission and project-shape failures

- **Project admin required**: template management and request testing are restricted to project admins.
- **Wrong project type**: confirm the template and label collection match the project's task type.
- **Text vs file-backed mismatch**: image and other file-backed projects need an upload identifier or file path rather than raw text.

## Recovery steps

1. Recheck the request model.
2. Recheck the sample payload.
3. Recheck the response mapping.
4. Recheck the label map.
5. Re-run the config tests before enabling the feature.
