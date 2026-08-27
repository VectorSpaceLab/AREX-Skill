# Cloud Integration Troubleshooting

Start with local preflight before investigating Azure credentials or service behavior:

```bash
python ../scripts/check_cloud_configuration.py --mode cu --endpoint "https://<endpoint>/" --file-types pdf,mp4
```

The checker validates imports, endpoint shape, file-type names, and CLI-style argument combinations without calling Azure by default.

## CLI Parser Failures

### `--use-docintel` without `--endpoint`

Symptom: the CLI exits with an error that Document Intelligence endpoint is required.

Fix:

```bash
markitdown "<input.pdf>" --use-docintel --endpoint "https://<document-intelligence-resource>.cognitiveservices.azure.com/"
```

### `--use-cu` without `--cu-endpoint`

Symptom: the CLI exits with an error mentioning `--cu-endpoint`.

Fix:

```bash
markitdown "<input.pdf>" --use-cu --cu-endpoint "https://<content-understanding-resource>.cognitiveservices.azure.com/"
```

### Cloud mode without filename

Both cloud CLI branches require a filename. Provide a path argument instead of relying on stdin.

### `--use-docintel` conflicts with `--use-cu`

The CLI defines these as mutually exclusive. Choose one cloud converter per command. If the user needs fallback behavior across converter families, implement it in Python with explicit routing and user-approved network calls.

### Unknown CU file type

`--cu-file-types` must contain comma-separated enum values. Use values like `pdf,jpeg,mp4`, not extensions like `.pdf` or MIME types like `application/pdf`.

## Missing Optional Dependencies

Document Intelligence construction requires the Azure Document Intelligence optional dependencies:

```bash
pip install 'markitdown[az-doc-intel]'
```

Content Understanding construction requires the Azure Content Understanding optional dependencies:

```bash
pip install 'markitdown[az-content-understanding]'
```

`markitdown[all]` also includes the cloud extras. Install the needed extra into the active runtime environment before retrying.

## Credential Selection

MarkItDown cloud converters accept explicit Azure credential objects in Python. When omitted, converter behavior is runtime dependent:

- If `AZURE_API_KEY` exists, the converter uses it as an Azure key credential.
- Otherwise the converter falls back to Azure Identity's default credential chain.

Safe handling rules:

- Never hard-code real keys in examples, scripts, source files, or prompts.
- Ask the user to confirm the credential source before a real cloud call.
- Avoid printing secret values. It is acceptable to report whether an expected environment variable is present.
- Endpoint URLs are not credentials, but still avoid leaking private tenant or resource naming unless the user provided them for the active task.

## Content Understanding Analyzer Mismatch

A custom `--cu-analyzer` is not necessarily used for every file. MarkItDown checks analyzer modality and only routes compatible types to it. Incompatible modalities auto-route to default prebuilts.

Typical example:

- User sets a document analyzer and `--cu-file-types pdf,mp4`.
- PDF can use the document analyzer.
- MP4 routes to the video prebuilt because a document analyzer is incompatible with video.

If the user's goal is to avoid sending DOCX files to Azure, restrict `--cu-file-types` to the intended values, such as `pdf,mp4`. DOCX then falls through to non-CU converters when using normal MarkItDown converter routing.

## Network, Availability, and Cost

Cloud conversion is not a dry run. Real conversion sends file bytes to Azure, depends on network/service availability, uses the user's Azure credentials, and can produce billable API calls. Do not run real conversions unless the user explicitly provides the endpoint, confirms credential readiness, and authorizes network/cost.

## Safe Diagnosis Sequence

1. Validate local argument combinations with `scripts/check_cloud_configuration.py`.
2. Confirm the required MarkItDown extra imports successfully.
3. Confirm the endpoint is a placeholder or a user-provided Azure endpoint.
4. Confirm credential source without exposing secret values.
5. Confirm selected file types and analyzer routing match the user's privacy/cost intent.
6. Only then run a real `markitdown` cloud conversion if the user explicitly authorizes it.
