# Installation and First Use

## Safe install

```bash
pip install tabpfn
python -c "import tabpfn; print(tabpfn.__version__)"
```

If you need plotting helpers or experiment logging, install the matching extra
for that workflow after the base package.

## First-use model access

TabPFN downloads model weights on first use unless a local checkpoint is already
available. That first access may require browser-based license acceptance or a
cached token.

### Headless or non-interactive environments

- Set `TABPFN_TOKEN` to a valid API token before calling `fit()`.
- If browser login should be disabled, set `TABPFN_NO_BROWSER=1` and provide a
token instead.

### Offline or cached use

- Point `TABPFN_MODEL_CACHE_DIR` at the directory you want to use for model
  files.
- Use the model-management sub-skill for cache, download, and checkpoint
  workflows.

## Safe smoke check

Run the root environment helper to verify the install and inspect the active
settings without downloading any models.
