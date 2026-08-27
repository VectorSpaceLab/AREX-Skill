# Native Workflow Troubleshooting

- Model load URL/cache errors: retry, configure `HANLP_HOME`, use a compatible `HANLP_URL`, or copy caches from a machine where the model loaded.
- Local path load errors: verify the directory contains HanLP component metadata such as `meta.json`.
- Optional AMR/TF/fastText errors: install only the needed extra.
- Input shape errors: split documents before local MTL, use nested token lists with `skip_tasks='tok*'`, and distinguish RESTful document input from native sentence input.
- Device issues: use `devices=-1` for CPU checks; use GPU only after `torch.cuda.is_available()` and a real backend smoke pass.
- Pipeline issues: `input_key` reads an existing `Document` field, `output_key` stores a result, and saved pipelines need importable callable paths.
