# Troubleshooting

## Installation and import problems

- **`doccano` command not found**: install the package in the active environment with `pip install doccano`, then re-run `python -m pip check` and `doccano --help`.
- **Import errors after editable install**: verify the target environment with `python -m pip check`, then reinstall the package in that same environment instead of mixing interpreters.
- **Unsupported Python version**: use Python 3.10 or newer. The CI matrix exercises 3.10, 3.11, and 3.12.
- **Missing optional extras**: install only the extra that matches the selected workflow, such as PostgreSQL support when `DATABASE_URL` points to PostgreSQL.

## Database and startup problems

- **`django.db.utils.OperationalError: no such function: JSON_VALID`**: the SQLite build lacks the JSON1 extension. Use a Python/SQLite build with JSON1 enabled or switch to PostgreSQL.
- **`Database unavailable` during `doccano init`**: check `DATABASE_URL`, database credentials, host reachability, and whether the database service is running.
- **Migration failures**: confirm the selected database matches the runtime docs and that the environment variable overrides are correct.
- **Admin creation problems**: `createuser` requires a username and password. The default password `password` is accepted but should be changed immediately.

## Server and browser problems

- **Port already in use**: start `doccano webserver` with a different `--port`.
- **CSRF failures**: add the frontend origin to `CSRF_TRUSTED_ORIGINS`, especially when the app runs behind a proxy or on a non-default port.
- **Login or permission errors**: confirm the user is in the project and has the expected role. Admin, annotator, and approver roles differ.
- **Static files missing after a source build**: run the collectstatic step from the build workflow and confirm the frontend assets were copied into the backend package layout.

## Data import and export problems

- **Bad JSON or JSONL**: validate the file content first. JSONL must be one JSON object per line.
- **Bad CSV**: check the delimiter, headers, empty fields, and column order.
- **Bad CoNLL**: each non-empty line must have two tab-separated columns.
- **Unexpected MIME or file-type rejection**: confirm `ENABLE_FILE_TYPE_CHECK` and the expected format match the uploaded asset.
- **File too large**: raise `MAX_UPLOAD_SIZE` or reduce the upload size.
- **Encoding issues**: retry with UTF-8 or explicitly choose the documented encoding if automatic detection is wrong.
- **Wrong import/export shape for the project type**: confirm the project type before choosing a format. Sequence labeling, seq2seq, bounding box, segmentation, and speech/image tasks each have different expectations.

## Auto-labeling problems

- **Unknown model name**: the config must use a template or request model known to `auto_labeling_pipeline`.
- **Attributes do not match the model**: supply every required field for the chosen request model before testing the request.
- **Connection or AWS token failures**: inspect the external endpoint, credentials, and network access.
- **Template mapping errors**: the response template must render a non-empty label collection in the target doccano shape.
- **No labels are created**: confirm the project has matching label types and that the label mapping converts response labels into the project's internal labels.

## Docker, deployment, and helper-script problems

- **Missing container env vars**: the helper scripts expect `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `ADMIN_EMAIL` for bootstrap, plus port and worker settings in the runtime scripts.
- **`FLOWER_BASIC_AUTH` absent**: Flower starts without basic auth only when the variable is unset; set it explicitly if access control is required.
- **Heroku or cloud deploy issues**: confirm the cloud template, image build, and bootstrap variables before troubleshooting application code.
- **Package build problems**: install both Node/Yarn and Poetry before running the source packaging workflow.

## When to escalate

- If the selected workflow needs a database backend, external credentials, or container tooling that is not available, narrow the scope or switch to the working deployment path.
- If the repository state changed after this skill was created, refresh the skill from the current checkout before trusting the references.
