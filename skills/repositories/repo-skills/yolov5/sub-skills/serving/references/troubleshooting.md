# Serving Troubleshooting

## Flask import failure

Install `Flask` in the active environment. The REST API example cannot run without it.

## Model loading downloads weights

The live server loads YOLOv5 models through PyTorch Hub. If the selected model is not already cached, the startup path may download weights. Use the smoke helper instead when you only need request validation.

## Upload errors

- `400 No image file provided`: the multipart form did not include an `image` field.
- `400 Invalid file type`: the filename extension is not in the allowlist.
- `400 Invalid image file`: the payload bytes are not a valid image.
- `413 File too large`: the uploaded body exceeded 16 MB.
- `404 Model not found`: the requested model name was not added to the server registry.

## API key errors

- `401 Unauthorized` means `API_KEY` is set in the server environment and the request header is missing or mismatched.
- Send `X-API-Key` exactly as the server expects.

## Runtime and binding issues

- The example server binds to `127.0.0.1`; it is not exposed externally by default.
- Multiple models may be loaded with `--model`, but each one can trigger its own download or initialization cost.
- Do not use the live server as a smoke check when a Flask test client can prove the upload and auth contract.

## Safe verification signals

- The Flask smoke helper returns `200`, `400`, `401`, and `413` exactly as expected for the corresponding cases.
- The dummy model's `.pandas().xyxy[0].to_json(orient="records")` path works without a real checkpoint.
