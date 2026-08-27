# Virtual files and cloud sessions

## Local virtual paths

Fiona recognizes URI/VSI schemes such as `zip`, `tar`, `gzip`, `http`, `https`,
`s3`, and `gs` when the linked GDAL build supports them. Local archive paths
are the safest deterministic use:

```python
with fiona.open("zip://layer.shp!/data/archive.zip") as src:
    print(src.schema)
```

Exact archive URI syntax is driver and GDAL-version sensitive; validate with a
small local fixture and use `fiona.vfs.parse_paths` for parsing behavior. Do not
assume an HTTP or cloud URI is local: it may download data or require a signed
request.

## Opener and fsspec

`fiona.open(..., opener=...)` can integrate a file-like opener or a compatible
filesystem object. The object must provide the methods Fiona's opener contract
expects, including read/seek/tell/close for file-like data, or filesystem
methods such as `isdir`, `isfile`, `ls`, `mtime`, `open`, and `size`. One opener
is allowed per path/mode pair. Keep this boundary explicit and test with bytes
before involving a remote service.

## AWS sessions

`AWSSession` uses boto3 and can select a profile, unsigned access, requester
pays, or explicit session construction. `DummySession` is the no-credentials
fallback. The CLI exposes `--aws-profile`, `--aws-no-sign-requests`, and
`--aws-requester-pays`. Public unsigned access may still incur network/data
transfer effects; credentialed or requester-pays access requires explicit
authorization and appropriate credentials. Never print credentials in logs.

For a remote task, first classify: public and approved network, signed/private
resource, requester-pays, or offline/local. If it is not explicitly approved,
stop and provide the required inputs rather than attempting the request.
