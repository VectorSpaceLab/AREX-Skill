# Cloud and API-key usage plan

This reference covers remote DeepAnalyze access through the hosted API-key path. It does not replace the local vLLM server instructions.

## What the cloud path is

The repo documents a hosted service path on HeyWhale/DeepAnalyze where the model is reached through a remote API endpoint instead of a local GPU process.

The guide describes a service URL shaped like:

```text
https://www.heywhale.com/api/model/services/<service-id>/app/v1/chat/completions
```

## API key acquisition

The repo announcement and guide point to public request forms for a DeepAnalyze API key. The guide describes short-lived keys, so treat them as temporary credentials.

## Safe usage rules

- Keep the key in an environment variable or secret manager.
- Do not embed the key in prompts, notebook cells, Dockerfiles, or model configs.
- Do not display the key in terminal output or commit it to the repo.
- If the task is about actual client calls against a running server, hand off to `api-and-clients`.

## Minimal header pattern

```text
Authorization: Bearer <api_key>
```

Use the bearer header against the remote service path provided by the hosted platform.

## What to decide before use

- Whether the task should use the remote hosted model or a local vLLM deployment.
- Whether the key lifecycle fits the current job window.
- Whether the downstream work belongs to client integration instead of model-serving guidance.

## Boundary reminder

This reference only covers the cloud access concept and secret hygiene. It does not document the file-upload protocol, thread tracking, or streaming client payloads.
