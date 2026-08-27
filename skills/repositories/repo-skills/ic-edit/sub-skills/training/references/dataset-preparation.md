# Dataset preparation

## What the repo ships

The original repo ships a bulk download helper that uses `wget -c` to fetch many parquet shards from Hugging Face into the training parquet directory.
The file list spans the `OmniEdit-mini` and `OmniEdit-Filtered-1.2M` datasets.

## How the training code consumes data

The current `edit_with_omini` path loads the parquet side with:

```python
load_dataset("parquet", data_files=os.path.abspath(training_config["dataset"]["path"]), split="train")
```

That means the config must point at a real parquet glob or directory of parquet files from the training working root.
If the glob resolves to nothing, the run will fail before training starts.

The same branch also loads `osunlp/MagicBrush` from the Hub, so network access or a populated local cache may still be required.

## Manual provisioning rule

Treat `prepare.sh` as a deliberate data-provisioning step, not as something the training helper should run automatically.
It is appropriate when you explicitly want to download the OmniEdit shards ahead of time and can absorb the network and disk cost.

## Practical checks

- Confirm the parquet glob resolves before launching a GPU run.
- Confirm you really want the MagicBrush hub access path.
- If you need task filtering, remember that `OminiDataset` supports `specific_task`, but the current launcher does not surface it from YAML.
