# Inspection Facts

## Purpose

Use this reference for sanitized package facts verified during skill creation. It omits private environment paths and machine-specific setup details.

## Package Metadata

| Fact | Value |
| --- | --- |
| Distribution name | `hail` |
| Public imports verified | `hail`, `hailtop`, `hailtop.batch` |
| Console entry point | `hailctl = hailtop.hailctl.__main__:main`; `python -m hailtop.hailctl` is a useful fallback |
| Python requirement | `>=3.10` |
| Hail version baseline | `0.2.138` from installed package metadata used for inspection |
| Spark/PySpark dependency | `pyspark>=3.5.0,<3.6` |
| Notable runtime dependencies | `numpy>=2,<3`, `pandas>=2,<3`, `scipy>1.13,<2`, `bokeh>3.8.2,<4`, `plotly>=5.18,<6`, `requests>=2.32.4,<3`, `avro>=1.10,<1.12`, and Hailtop cloud/client dependencies |
| Packaged command families | `hailctl version`, `curl`, `describe`, `auth`, `batch`, `config`, `dataproc`, `dev`, `hdinsight` |

## Verified Hail Query Signatures

```text
hl.init(sc=None, app_name=None, master=None, local=None, log=None, quiet=False, show_progress=None, append=False, min_block_size=None, branching_factor=50, tmp_dir=None, default_reference=None, idempotent=False, global_seed=None, spark_conf=None, skip_logging_configuration=False, local_tmpdir=None, *, backend=None, driver_cores=None, driver_memory=None, worker_cores=None, worker_memory=None, batch_id=None, max_read_parallelism=None, gcs_requester_pays_configuration=None, regions=None, gcs_bucket_allow_list=None, copy_spark_log_on_error=None, copy_log_on_error=None)
hl.init_local(log=None, quiet=False, append=False, branching_factor=50, tmpdir=None, default_reference='GRCh37', global_seed=None, skip_logging_configuration=False, jvm_heap_size=None, requester_pays_config=None, copy_log_on_error=None)
hl.init_spark(sc=None, app_name=None, master=None, local=None, log=None, quiet=False, append=False, show_progress=None, min_block_size=None, branching_factor=50, tmp_dir=None, default_reference='GRCh37', global_seed=None, spark_conf=None, skip_logging_configuration=False, local_tmpdir=None, requester_pays_config=None, copy_log_on_error=False)
hl.init_batch(*, billing_project=None, remote_tmpdir=None, log=None, quiet=False, append=False, tmpdir=None, default_reference='GRCh37', global_seed=None, show_progress=None, driver_cores=None, driver_memory=None, worker_cores=None, worker_memory=None, batch_id=None, name_prefix=None, token=None, requester_pays_config=None, regions=None, gcs_bucket_allow_list=None, branching_factor=None, max_read_parallelism=None)
hl.stop()
```

## Verified Table and MatrixTable Signatures

```text
hl.import_table(paths, key=None, min_partitions=None, impute=False, no_header=False, comment=(), delimiter='\t', missing='NA', types={}, quote=None, skip_blank_lines=False, force_bgz=False, filter=None, find_replace=None, force=False, source_file_field=None) -> Table
hl.read_table(path, *, _intervals=None, _filter_intervals=False, _n_partitions=None, _assert_type=None, _load_refs=True, _create_row_uids=False) -> Table
hl.import_vcf(path, force=False, force_bgz=False, header_file=None, min_partitions=None, drop_samples=False, call_fields=['PGT'], reference_genome='default', contig_recoding=None, array_elements_required=True, skip_invalid_loci=False, entry_float_type=float64, filter=None, find_replace=None, n_partitions=None, block_size=None, _create_row_uids=False, _create_col_uids=False) -> MatrixTable
hl.import_plink(bed, bim, fam, min_partitions=None, delimiter='\\s+', missing='NA', quant_pheno=False, a2_reference=True, reference_genome='default', contig_recoding=None, skip_invalid_loci=False, n_partitions=None, block_size=None) -> MatrixTable
hl.import_bgen(path, entry_fields, sample_file=None, n_partitions=None, block_size=None, index_file_map=None, variants=None, _row_fields=['varid', 'rsid']) -> MatrixTable
hl.export_vcf(dataset, output, append_to_header=None, parallel=None, metadata=None, *, tabix=False)
```

## Verified Genomics Method Signatures

```text
hl.variant_qc(mt, name='variant_qc') -> MatrixTable
hl.sample_qc(mt, name='sample_qc') -> MatrixTable
hl.split_multi_hts(ds, keep_star=False, left_aligned=False, vep_root='vep', *, permit_shuffle=False)
hl.linear_regression_rows(y, x, covariates, block_size=16, pass_through=(), *, weights=None) -> Table
hl.logistic_regression_rows(test, y, x, covariates, pass_through=(), *, max_iterations=None, tolerance=None) -> Table
hl.pca(entry_expr, k=10, compute_loadings=False)
hl.ld_prune(call_expr, r2=0.2, bp_window_size=1000000, memory_per_core=256, keep_higher_maf=True, block_size=None)
hl.vep(dataset, config=None, block_size=1000, name='vep', csq=False, tolerate_parse_error=False)
```

## Verified VDS Signatures

```text
hl.vds.read_vds(path, *, intervals=None, n_partitions=None, _assert_reference_type=None, _assert_variant_type=None, _warn_no_ref_block_max_length=True, _drop_end=False) -> VariantDataset
hl.vds.VariantDataset(reference_data, variant_data)
hl.vds.filter_samples(vds, samples, *, keep=True, remove_dead_alleles=False) -> VariantDataset
hl.vds.to_dense_mt(vds) -> MatrixTable
hl.vds.new_combiner(*, output_path, temp_path, save_path=None, gvcf_paths=None, vds_paths=None, intervals=None, import_interval_size=None, use_genome_default_intervals=False, use_exome_default_intervals=False, gvcf_external_header=None, gvcf_sample_names=None, gvcf_info_to_keep=None, gvcf_reference_entry_fields_to_keep=None, gvcf_save_filters=False, call_fields=['PGT'], branch_factor=100, target_records=24000, gvcf_batch_size=None, batch_size=None, reference_genome='default', contig_recoding=None, force=False)
```

## Verified Batch API and CLI Facts

```text
hailtop.batch.Batch(name=None, backend=None, attributes=None, requester_pays_project=None, default_image=None, default_memory=None, default_cpu=None, default_storage=None, default_regions=None, default_timeout=None, default_shell=None, default_python_image=None, default_spot=None, project=None, cancel_after_n_failures=None)
hailtop.batch.LocalBackend(tmp_dir='/tmp/', gsa_key_file=None, extra_docker_run_flags=None)
hailtop.batch.ServiceBackend(*args, billing_project=None, bucket=None, remote_tmpdir=None, google_project=None, token=None, regions=None, gcs_requester_pays_configuration=None, gcs_bucket_allow_list=None)
```

`hailctl batch --help` exposes `list`, `get`, `cancel`, `delete`, `log`, `attempts`, `wait`, `job`, `jobs`, `init`, `submit`, and `billing`.

`hailctl config --help` exposes `set`, `unset`, `get`, `config-location`, `list`, and `profile`.

`hailctl dataproc --help` exposes `start`, `stop`, `list`, `connect`, `submit`, `diagnose`, `modify`, and deprecated `describe`.

`hailctl describe --help` accepts a Hail Table or MatrixTable file and an optional requester-pays project flag.

## Inspection Caveats

- Run live package inspection from a neutral working directory. A raw source tree with a top-level `hail` directory can shadow the installed distribution and produce a partial namespace import.
- Some raw source checkouts omit generated `hail/version.py` and `hailtop/version.py` files. Packaged installs and build outputs should include version metadata.
- Full Hail backend execution depends on generated JAR/package assets, Java, Spark/PySpark, local or cloud temporary directories, and sometimes external credentials. Static import and CLI help checks are not the same as backend execution.
