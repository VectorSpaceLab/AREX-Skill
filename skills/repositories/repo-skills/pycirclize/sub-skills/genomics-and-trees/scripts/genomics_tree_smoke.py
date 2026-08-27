#!/usr/bin/env python3
"""Run a deterministic, no-network pyCirclize genomics/tree smoke check."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from pycirclize import Circos
from pycirclize.parser import Bed, Genbank, Gff

GENBANK_TEXT = """LOCUS       chr1                      32 bp    DNA     linear   SYN 01-JAN-2000
DEFINITION  tiny synthetic record one.
ACCESSION   chr1
FEATURES             Location/Qualifiers
     source          1..32
                     /organism=\"synthetic\"
     CDS             1..12
                     /gene=\"alpha\"
                     /product=\"toy protein alpha\"
                     /translation=\"MKT\"
     tRNA            complement(17..24)
                     /gene=\"trna1\"
ORIGIN
        1 atgcgcga atgcgcga atgcgcga atgcgcga
//
LOCUS       chr2                      24 bp    DNA     linear   SYN 01-JAN-2000
DEFINITION  tiny synthetic record two.
ACCESSION   chr2
FEATURES             Location/Qualifiers
     source          1..24
                     /organism=\"synthetic\"
     CDS             complement(5..18)
                     /gene=\"beta\"
                     /product=\"toy protein beta\"
                     /translation=\"MNN\"
ORIGIN
        1 gcatgcat gcatgcat gcatgcat
//
"""

GFF_TEXT = """##gff-version 3
##sequence-region chr1 1 32
##sequence-region chr2 1 24
chr1\tsynthetic\tgene\t3\t10\t.\t+\t.\tID=g1;Name=gene1
chr1\tsynthetic\tCDS\t5\t16\t.\t-\t0\tID=cds1;Parent=g1;product=toy-gff
chr2\tsynthetic\tCDS\t2\t9\t.\t+\t0\tID=cds2;product=toy-gff-2
"""

CHROMOSOME_BED = """# chromosome BED: zero-based, half-open
chr1\t0\t32
chr2\t0\t24
"""

CYTOBAND_BED = """# chromosome start end band score
chr1\t0\t8\tp1\tgneg
chr1\t8\t20\tp2\tgpos100
chr1\t20\t32\tq1\tgvar
chr2\t0\t12\tp1\tgneg
chr2\t12\t24\tq1\tacen
"""

TREE_TEXT = "((A:1,B:1)90:1,(C:1,D:1)80:1)100;"


def _write_fixture(directory: Path, name: str, text: str) -> Path:
    """Write one embedded fixture into a fresh temporary directory."""
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def _build_genomics_plot(
    genbank_file: Path,
    gff_file: Path,
    chromosome_file: Path,
    cytoband_file: Path,
    ax,
) -> tuple[dict[str, int], int, int]:
    """Parse local fixtures and draw feature, cytoband, and GC tracks."""
    gbk = Genbank(genbank_file)
    gff = Gff(gff_file)
    bed = Bed(chromosome_file)

    seqid2size = gbk.get_seqid2size()
    if seqid2size != {record.chr: record.size for record in bed.records}:
        raise AssertionError("BED and GenBank sector sizes do not match")
    if gff.get_seqid2size() != seqid2size:
        raise AssertionError("GFF and GenBank seqid sizes do not match")

    # Exercise both parser bridges before drawing.
    gbk_features = gbk.get_seqid2features(feature_type=["CDS", "tRNA"])
    gff_features = gff.get_seqid2features(feature_type="CDS")
    if not gbk_features["chr1"] or not gff_features["chr2"]:
        raise AssertionError("embedded feature fixtures were not extracted")

    circos = Circos.initialize_from_bed(chromosome_file, space=3)
    circos.add_cytoband_tracks(
        (95, 100),
        cytoband_file,
        cytoband_cmap={
            "gneg": "white",
            "gpos100": "black",
            "gvar": "#aaaaaa",
            "acen": "#cc6666",
        },
    )

    gc_points = 0
    skew_points = 0
    for sector in circos.sectors:
        gbk_track = sector.add_track((88, 94))
        gff_track = sector.add_track((81, 87))
        gc_track = sector.add_track((70, 78))
        skew_track = sector.add_track((60, 68))
        gbk_track.axis(ec="none")
        gff_track.axis(ec="none")

        for feature in gbk_features[sector.name]:
            color = "tomato" if feature.location.strand == 1 else "skyblue"
            gbk_track.genomic_features(feature, plotstyle="arrow", fc=color, lw=0.4)
        for feature in gff_features[sector.name]:
            gff_track.genomic_features(feature, plotstyle="box", fc="orchid", lw=0.4)

        sequence = gbk.get_seqid2seq()[sector.name]
        positions, gc_content = gbk.calc_gc_content(
            seq=sequence, window_size=8, step_size=4
        )
        _, gc_skew = gbk.calc_gc_skew(seq=sequence, window_size=8, step_size=4)
        gc_track.fill_between(
            positions, gc_content, 0, vmin=0, vmax=100, color="darkgreen", alpha=0.6
        )
        skew_track.fill_between(
            positions, gc_skew, 0, vmin=-1, vmax=1, color="purple", alpha=0.6
        )
        gc_points += len(positions)
        skew_points += len(gc_skew)

    circos.plotfig(ax=ax)
    return seqid2size, gc_points, skew_points


def _build_tree_plot(ax) -> int:
    """Draw and annotate an embedded Newick tree."""
    circos, tv = Circos.initialize_from_tree(
        TREE_TEXT,
        r_lim=(35, 94),
        leaf_label_size=8,
        line_kws={"color": "grey", "lw": 0.8},
    )
    expected = {"A", "B", "C", "D"}
    if not expected.issubset(tv.leaf_labels):
        raise AssertionError("embedded Newick leaves were not loaded")
    tv.highlight(["A", "B"], color="gold", alpha=0.35)
    tv.marker("C", marker="D", size=7, color="navy", descendent=False)
    tv.set_node_line_props(["C", "D"], color="royalblue", apply_label_color=True)
    tv.show_confidence(size=6, color="black")
    circos.plotfig(ax=ax)
    return tv.leaf_num


def run(output: Path) -> dict[str, object]:
    """Run all local parser and plotting checks and write one new PNG."""
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pycirclize-genomics-tree-") as temp:
        fixture_dir = Path(temp)
        genbank_file = _write_fixture(fixture_dir, "tiny.gbk", GENBANK_TEXT)
        gff_file = _write_fixture(fixture_dir, "tiny.gff", GFF_TEXT)
        chromosome_file = _write_fixture(fixture_dir, "chromosomes.bed", CHROMOSOME_BED)
        cytoband_file = _write_fixture(fixture_dir, "cytoband.tsv", CYTOBAND_BED)

        figure = plt.figure(figsize=(6, 3), dpi=100)
        axes = figure.subplots(1, 2, subplot_kw={"polar": True})
        seqid2size, gc_points, skew_points = _build_genomics_plot(
            genbank_file, gff_file, chromosome_file, cytoband_file, axes[0]
        )
        leaf_num = _build_tree_plot(axes[1])
        figure.savefig(output, format="png", dpi=100, bbox_inches="tight")
        plt.close(figure)

    size = output.stat().st_size
    if size <= 0:
        raise AssertionError("PNG export is empty")
    return {
        "output": str(output),
        "bytes": size,
        "seqid2size": seqid2size,
        "gc_points": gc_points,
        "skew_points": skew_points,
        "tree_leaves": leaf_num,
        "network": False,
        "backend": matplotlib.get_backend(),
    }


def main() -> int:
    """Parse arguments, run the smoke check, and print concise results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="new PNG path; defaults to a temporary path that is removed after the run",
    )
    args = parser.parse_args()

    if args.output is not None:
        result = run(args.output)
        print(result)
        return 0

    with tempfile.TemporaryDirectory(prefix="pycirclize-genomics-tree-output-") as temp:
        result = run(Path(temp) / "genomics_tree_smoke.png")
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
