# Dataset workflows

DO publishes a dataset:

```python
do.create_dataset(
    name="census",
    mock_path="mock.csv",
    private_path="private.csv",
    users=["scientist@example.com"],
)
do.sync()
```

DS discovers mock data:

```python
ds.sync()
dataset = ds.datasets.get("census", datasite="owner@example.com")
```

Inside a job, private data resolution is implicit:

```python
import syft_client as sc
path = sc.resolve_dataset_file_path("census")
```

Outside jobs, pass `client=client` to test against mock files, and remove the argument before submission. `users="any"` means all approved peers should receive mock collections; peers approved later may require sync/callback re-sharing.
