# Install-build script contract

`check_tvm_install.py` is a read-only diagnostic. Run `python
scripts/check_tvm_install.py --help` for options. It must remain independent
of a particular checkout unless `--repo-root` is supplied and must not download,
modify, or build anything.