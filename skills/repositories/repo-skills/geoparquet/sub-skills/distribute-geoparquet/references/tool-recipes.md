# Distribution tool recipes

These are the repository's documented starting recipes, preserved with their
version caveats. They are examples, not proof that a tool is installed or that
an invocation will work in the user's environment. Before using any recipe,
probe the executable, package, extension, backend, and exact version; consult
that version's help/docs; install missing dependencies explicitly; and retain
the command output. Then route the resulting files to
[`../../validate-geoparquet/SKILL.md`](../../validate-geoparquet/SKILL.md).

Paths below are placeholders such as `in.geojson`, `input.parquet`, and
`output/`; replace them with the user's paths and do not copy private checkout
paths into a published skill or command log.

## GDAL/OGR

Baseline conversion:

```bash
ogr2ogr out.parquet in.geojson
```

The documented defaults are Snappy compression and a maximum row group size
of 65,536. GDAL 3.9 and later writes a `bbox` column by default, producing
GeoParquet 1.1. Defaults are not distribution recommendations.

If the source is already spatially ordered in a format with a spatial index
(such as FlatGeobuf or GeoPackage), set ZSTD and the row-group maximum:

```bash
ogr2ogr out.parquet -lco "COMPRESSION=ZSTD" -lco "MAX_ROW_GROUP_SIZE=100000" in.fgb
```

To force spatial ordering, use the documented temporary-GeoPackage route:

```bash
ogr2ogr out.parquet -lco SORT_BY_BBOX=YES -lco "COMPRESSION=ZSTD" in.geojson
```

`SORT_BY_BBOX=YES` is disabled by default because it can require substantial
temporary storage and computation. It uses a temporary GeoPackage and its
R-tree. If source ordering is already trustworthy, avoid the extra rewrite.

GDAL 3.12 and later adds `COMPRESSION_LEVEL` as a Parquet layer creation option
and documents this CLI example:

```bash
gdal vector convert vegetation.fgb vegetation.parquet --lco compression=zstd --lco compression_level=15
```

Native logical types require GDAL 3.12 or later built against libarrow 21 or
later. The option is `USE_PARQUET_GEO_TYPES=NO|YES|ONLY`:

```bash
ogr2ogr out.parquet -lco USE_PARQUET_GEO_TYPES=ONLY -lco "COMPRESSION=ZSTD" -lco "MAX_ROW_GROUP_SIZE=100000" in.fgb
```

Interpret the modes carefully:

- `NO` (default): GDAL writes its normal GeoParquet 1.1 style, including the
  bbox covering where applicable.
- `YES`: native geometry logical types plus GeoParquet 1.1 metadata and the
  redundant bbox covering; this is larger and still advertises 1.1.
- `ONLY`: native types without the `geo` metadata block and without bbox. It
  is readable by GeoParquet 2.0 readers but is **not conformant GeoParquet
  2.0**, because it lacks the version/metadata block. Use a future dedicated
  GDAL 2.0 mode when available rather than presenting `ONLY` as certification.

Partition on a precomputed spatial grouping field (administrative region,
geohash, or grid cell):

```bash
gdal vector partition in.parquet out_dir --field region --max-file-size 1GB
```

GDAL does not calculate a spatial partition scheme itself and does not write
STAC metadata. Use `gdal vector sort` or an upstream ordering step before
partitioning when appropriate, and generate STAC separately.

## DuckDB

Core DuckDB 1.5 includes the `GEOMETRY` type and GeoParquet read/write,
conversion, recompression, and repartitioning; the spatial extension is not
needed merely for those operations. The spatial extension is still required
for `ST_*` functions, including reprojection and `ST_Hilbert`. DuckDB's
out-of-the-box documented defaults are Snappy, 122,880 rows per row group,
GeoParquet 1.0.0, and no spatial ordering. DuckDB 1.5 and later preserves CRS
on a read/write round trip; earlier versions may drop it and need CRS repair
with GDAL or QGIS.

Write native GeoParquet 2.0:

```sql
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2');
```

Recommended compression, level, and row count:

```sql
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd', COMPRESSION_LEVEL 15, ROW_GROUP_SIZE '100000');
```

A byte target can better handle variable geometry sizes:

```sql
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd', ROW_GROUP_SIZE_BYTES '128mb');
```

The documented caveat is that `ROW_GROUP_SIZE_BYTES` may require
`SET preserve_insertion_order = false;`; confirm the exact version's behavior
and whether the chosen execution preserves the intended spatial order.

Order globally by Hilbert value. Load the spatial extension and pass the
bounds of the entire dataset to `ST_Hilbert`:

```sql
LOAD spatial;
COPY (
    WITH bbox AS (
        SELECT ST_Extent(ST_Extent_Agg(geometry))::BOX_2D AS b
        FROM   geo_table
    )
    SELECT   t.*
    FROM     geo_table AS t
            CROSS JOIN bbox
    ORDER BY ST_Hilbert(t.geometry, bbox.b)
) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd', ROW_GROUP_SIZE '100000');
```

Spatial partitioning uses `COPY ... PARTITION_BY` over a computed cell. The
repository documents the community `a5` extension example:

```sql
INSTALL a5 FROM community; LOAD a5;
INSTALL spatial; LOAD spatial;
COPY (
    SELECT *, a5_u64_to_hex(a5_lonlat_to_cell(ST_X(geometry), ST_Y(geometry), 3)) AS a5_cell
    FROM   geo_table
) TO 'partitioned' (FORMAT 'parquet', PARTITION_BY a5_cell, GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd');
```

Choose resolution for a useful feature count per file. For non-points, derive
the cell from a representative point such as `ST_Centroid(geometry)` and
document the assignment policy. The recipe does not sort within partitions;
add an ordering stage if tight row-group bounds are required. DuckDB does not
write STAC metadata, so publish STAC separately.

## geoparquet-io (`gpio`)

The package is `geoparquet-io` and the command is `gpio`:

```bash
pipx install geoparquet-io   # or: pip install geoparquet-io
```

A plain conversion applies the distribution defaults—ZSTD level 15, Hilbert
spatial ordering, bbox covering, 100,000-row groups—and validates the result
according to the tool's own behavior:

```bash
gpio convert geoparquet input.gpkg output.parquet
```

The documented default is GeoParquet 1.1. It auto-detects from input,
preserves the input version, and upgrades native geo types to 2.0. Request
2.0 explicitly:

```bash
gpio convert geoparquet input.gpkg output.parquet --geoparquet-version 2.0
```

Partition with the default KD-tree, which targets approximately 120,000 rows
per file and adds a partition column if needed:

```bash
gpio partition kdtree input.parquet output/
gpio partition kdtree input.parquet output/ --partitions 32
```

Other documented partition schemes include quadkey, S2, H3, A5, and admin.
`gpio add` can add only a partitioning column, for example `gpio add h3` or
`gpio add admin-divisions`. Probe the installed release for exact subcommands
and options; do not assume the current defaults are stable.

Generate STAC for one file or a partitioned directory:

```bash
# Single file -> STAC Item
gpio publish stac input.parquet item.json --bucket s3://my-bucket/roads/

# Partitioned dataset -> Collection + per-file Items
gpio publish stac partitions/ . --bucket s3://my-bucket/roads/
```

The tool can upload data and STAC with `gpio publish upload`, and can run its
own whole-file check with `gpio check all`. Treat that as tool-specific
observational evidence, and still route concrete GeoParquet validation to the
validation sub-skill. Confirm bucket permissions and URL layout before upload.

## Apache Sedona

Sedona is documented here for Spark-based spatial partitioning. Exact Spark
and Sedona JAR/Python compatibility is environment-specific; prepare the
Spark/JAR setup, probe versions, and follow the installed Sedona setup guide
before running. The `SedonaContext` configuration below is the documented
starting point:

```python
import glob

from sedona.spark import SedonaContext, GridType
from sedona.utils.structured_adapter import StructuredAdapter
from sedona.sql.st_functions import ST_GeoHash

config = (
    SedonaContext.builder()
    .config("spark.executor.memory", "6G")
    .config("spark.driver.memory", "6G")
    .getOrCreate()
)

sedona = SedonaContext.create(config)

df = sedona.read.format("geoparquet").load("input.parquet")

rdd = StructuredAdapter.toSpatialRdd(df, "geometry")
rdd.analyze()
rdd.spatialPartitioningWithoutDuplicates(GridType.KDBTREE, num_partitions=8)
rdd.getPartitioner().getGrids()
df_partitioned = StructuredAdapter.toSpatialPartitionedDf(rdd, sedona)

df_partitioned = (
    df_partitioned.withColumn("geohash", ST_GeoHash(df_partitioned.geometry, 12))
    .sortWithinPartitions("geohash")
    .drop("geohash")
)

df_partitioned.write.format("geoparquet").mode("overwrite").option("compression", "zstd").save(
    "buildings_partitioned"
)

files = glob.glob("buildings_partitioned/*.parquet")
len(files)
```

`KDBTREE` is described as balancing partitions with approximately equal
feature counts; `num_partitions` is a suggestion and the actual count may
differ. `spatialPartitioningWithoutDuplicates` avoids introducing duplicate
features. Sorting by geohash within partitions is optional and tightens
row-group bounds. Spark's output names are executor-generated and may need a
separate publication layout step. The repository documents partitioning here,
not every compression, row-group, or GeoParquet-version option; probe the
installed Sedona writer before asserting that those options are supported.
STAC generation is separate.

## Other source/example evidence

The repository's R example uses `geoarrow`/`sf` to write and read a file:

```r
library(geoarrow)
library(ggplot2)
nc <- sf::read_sf(system.file("shape/nc.shp", package = "sf"))
write_geoparquet(nc, "nc.parquet")
nc_pq <- read_geoparquet("nc.parquet")
```

This is a minimal interoperability example, not a distribution recipe: it
does not establish ZSTD level, ordering, row-group size, partitioning, STAC,
or a specific GeoParquet version. Probe the installed `geoarrow` version and
validate its output before publication.
