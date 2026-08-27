# Model access and credentialed evaluation

GenAILab and Qualcomm deployment workflows cross several credential boundaries. Keep each boundary explicit and avoid printing secrets.

## Credential map

| Boundary | Typical signal | Safe verification | Notes |
| --- | --- | --- | --- |
| Hugging Face model/dataset access | gated model, private model, `transformers` download, `datasets` download | `hf auth whoami` or checking that `HF_TOKEN` is set without echoing it | Accept gated-model terms in the account UI before running. |
| GitHub Actions online scorecard | `python -m GenAILab --online`, `--download <run_id>` | `gh auth status` and workflow exists on branch | Online mode uses pushed branch code. |
| AWS/S3 GenAI artifacts | checkpoint zip, profiling artifacts, S3 upload/download | `aws sts get-caller-identity --profile <profile>` | SAML-backed profiles may expire. |
| SAML2AWS | `SAML2AWS_APP_ID`, `genai-laboratory` profile | `saml2aws login --profile <profile>` | Do not write App IDs or tokens into public skill files. |
| Qualcomm AI Hub/QNN | `qai_hub`, device compile/profile/inference | package import plus user-authenticated AI Hub tooling | Device availability and model support are external. |

## Hugging Face model and dataset access

- Set `HF_TOKEN` in the environment or log in via the Hugging Face CLI before launching GenAILab.
- Do not hard-code tokens into YAML configs.
- For private local checkpoints, set `model.model_id` to the local path and ensure tokenizer/config files are present.
- Datasets such as Wikitext, MMLU, MMMU, C4, and AOKVQA can download from Hugging Face or other hosted sources; pin revisions outside AIMET if exact historical reproduction matters.

## Online scorecard lifecycle

```bash
python -m GenAILab --framework torch --config config.yaml --online
python -m GenAILab --framework torch --config config.yaml --online --wait
python -m GenAILab --framework torch --config config.yaml --download <run_id>
```

- `--online` dispatches a GitHub Actions workflow with a base64-encoded config.
- `--wait` watches the run, downloads test-data artifacts, merges profiling JSON/CSV, and prints a summary.
- Extra pytest arguments are ignored in online mode; only framework, config, and branch/ref are sent.
- Use `--branch` when the desired ref is not the current branch.

## S3 checkpoint download lifecycle

Use `scripts/download_genai_checkpoint.sh --dry-run <s3-or-https-url>` first. The bundled downloader does not auto-install AWS or SAML tools; it reports missing tools instead.

Expected destination:

```text
GenAILab/artifacts/exports/<checkpoint-dir>/
```

It prints `model_id: <path>` so the extracted directory can be used as a local model/checkpoint path in follow-up configs.

## Cache and result comparability rules

- FP cache stores full-precision outputs for distance metrics.
- Recipe cache stores expensive cacheable steps such as SeqMSE and AdaScale.
- Model cache stores ONNX exports for repeated ONNX evaluation.
- Compare metrics only when metric name, model/config, dataset assumptions, and `scoring_version` match.
- Use `python scripts/genai_results_summary.py GenAILab/artifacts/results/profiling_data.json` to inspect existing result files without rerunning benchmarks.
- Old scoring implementations are not kept live; reproduce an old number by using the commit that produced it.
