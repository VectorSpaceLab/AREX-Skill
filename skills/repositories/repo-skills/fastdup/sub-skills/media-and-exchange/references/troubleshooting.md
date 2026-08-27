# Media and exchange troubleshooting

- If video workflows fail, confirm `ffmpeg` and codec support before blaming fastdup.
- The maintained docs only explicitly call out mp4 and avi as supported video formats; treat other codecs as experimental until proven in your environment.
- If archive workflows fail, check whether the input source is readable locally or through the selected cloud tool.
- If `s3://` or `minio://` paths fail, confirm credentials, `FASTDUP_S3_ENDPOINT_URL`, or `FASTDUP_MC_PATH` outside the skill.
- If remote sync behaves oddly, check whether `delete_tar`, `delete_img`, or `sync_s3_to_local` was set the way you intended.
- If a stored-feature workflow cannot resume, check for `features.dat`, `features.dat.csv`, and `nnf.index` in the same work directory.
- If a webdataset merge or filter path fails, inspect the extracted tar layout and the work directory before assuming the model run failed.
