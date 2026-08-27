# Auto-labeling workflows

doccano auto-labeling is configured from the project settings page and backed by REST testing endpoints.

## Workflow stages

1. **Select a template**
   - Open the Auto Labeling settings tab.
   - Choose a predefined template such as Amazon Comprehend or start from Custom REST Request.
   - The available templates are exposed by the backend template list endpoint.

2. **Set request parameters**
   - Fill in the request-model fields required by the chosen service.
   - For text projects, the request example is plain text.
   - For file-backed projects, the request example is a stored upload path or upload identifier.

3. **Test the request**
   - The backend validates the request model and forwards the sample payload.
   - Common failures here come from missing fields, bad credentials, or unreachable services.

4. **Render the response mapping**
   - Use the Jinja2-style template to reshape the service response into doccano labels.
   - The target shape depends on the task type:
     - classification -> label dictionaries
     - sequence labeling -> span dictionaries
     - seq2seq -> text dictionaries

5. **Apply label mapping**
   - Map external labels into the project's internal label names.
   - If the mapping produces no labels, the sample or label map is probably wrong.

6. **Enable auto-labeling**
   - Switch the feature on from the annotation page.
   - Each time a new example is loaded, doccano can apply the configured pipeline.

## API surfaces

| Purpose | Endpoint family |
| --- | --- |
| List templates | `auto_labeling_templates` |
| Test request parameters | `auto_labeling_parameter_testing` |
| Test response template | `auto_labeling_template_test` |
| Test label mapping | `auto_labeling_mapping_test` |
| Create or list configs | `auto_labeling_configs` |
| Run auto-labeling | `auto_labeling` |

## Important task types

- Classification templates use category labels.
- Span templates use start and end offsets.
- Text templates use text outputs.
- The request and mapping code is project-aware, so the same template can behave differently for text versus file-backed projects.
