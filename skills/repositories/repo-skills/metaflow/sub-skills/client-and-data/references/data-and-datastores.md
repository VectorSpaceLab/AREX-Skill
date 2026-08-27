# Data and Datastores

## Datastore types

Metaflow supports local, spin, S3, Azure Blob Storage, and Google Cloud Storage datastore plugins. Metadata provider and datastore are related but distinct: metadata tracks runs and tasks, while datastore stores artifacts, logs, cards, code packages, and data blobs.

Common flow-script top-level flags:

```bash
python flow.py --datastore=local run
python flow.py --datastore=s3 --metadata=service run
```

Remote compute decorators usually require a cloud datastore; see deployment orchestration.

## S3 datatools

`from metaflow import S3` provides a context-manager client for S3 objects:

```python
from metaflow import S3

with S3(s3root="s3://bucket/prefix") as s3:
    obj = s3.get("data.json", return_missing=True)
    if obj.exists:
        print(obj.text)
```

S3 workflows require `boto3`, network access, and credentials. Access-denied and missing-root errors are service/configuration problems, not proof that the Client API is broken.

## IncludeFile data

`IncludeFile` stores a local file's contents as a parameter/artifact. It uses the active datastore to persist content. Direct cloud URI references are rejected by the current `IncludeFile` converter; pass a local file path or a small pointer parameter instead.
