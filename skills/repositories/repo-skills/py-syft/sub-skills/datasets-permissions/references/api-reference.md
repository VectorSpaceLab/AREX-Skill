# Dataset API reference

| API | Verified shape | Notes |
| --- | --- | --- |
| `SyftRDSClient.create_dataset` | `create_dataset(name, mock_path, private_path, summary=None, readme_path=None, location=None, tags=None, users=None, upload_private=False, sync=True)` | DO only. |
| `client.datasets.get` | `get(name, datasite=None)` | Reads dataset metadata; DS sees mock files. |
| `client.datasets.get_all` | list API | Lists visible datasets. |
| `syft_client.resolve_dataset_file_path` | dataset-name resolver | Mock outside jobs with `client`; private inside jobs. |
| `syft_client.load_dataset_code` | load Python from resolved dataset | Useful when datasets ship code modules. |
