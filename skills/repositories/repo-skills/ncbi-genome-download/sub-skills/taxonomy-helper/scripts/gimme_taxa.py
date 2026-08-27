#!/usr/bin/env python3
"""Resolve taxon names/TaxIDs with ETE3 and emit descendant TaxIDs.

This is a self-contained adaptation of the optional contributed gimme_taxa
workflow. It preserves the public command-line flags and output formats while
keeping the ETE3 import lazy: ``--help`` is safe without ETE3 or a taxonomy
database. A real query may create/download or update a local ETE3 database.
"""

from __future__ import print_function

import argparse
import sys


DESCRIPTION = "Perform queries against the NCBI Taxa database"
EPILOG = """DESCRIPTION:
    This experimental helper finds TaxIDs to pass to ncbi-genome-download and
    writes a one-item-per-line file when --just-taxids is selected. It uses the
    ETE3 toolkit and a local NCBI taxonomy database.

    Inputs are a comma-separated list of TaxIDs and/or taxon names. The main
    operation returns descendant taxa; --taxon-info reports the supplied taxa.

    WARNING: This script is still somewhat experimental. A real query may
    create/download or update a local taxonomy database.
"""


def get_args(argv=None):
    """Parse command-line arguments without importing ETE3."""
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "taxid",
        metavar="taxid",
        type=str,
        help="A comma-separated list of TaxIDs and/or taxon names. (e.g. 561,2172)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Verbose behaviour. Supports 3 levels at present: Off = 0, "
            "Info = 1, Verbose = 2. (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "-d",
        "--database",
        type=str,
        default=None,
        help=(
            'NCBI taxonomy database file path. If "None", it will be '
            "downloaded (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        default=False,
        help=(
            "Update the local taxon database before querying. Recommended if "
            "not used for a while. (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "-j",
        "--just-taxids",
        action="store_true",
        default=False,
        help=(
            "Just write out a list of taxids and no other information "
            "(default: %(default)s)"
        ),
    )
    parser.add_argument(
        "-i",
        "--taxon-info",
        action="store_true",
        default=False,
        help=(
            "Just write out rank & lineage info on the provided taxids "
            "(default: %(default)s)"
        ),
    )
    parser.add_argument(
        "-o",
        "--outfile",
        action="store",
        help="Output file to store the descendent TaxIDs for the query.",
    )
    return parser.parse_args(argv)


def _load_ncbi_taxa():
    """Import ETE3 only for a real query and explain setup failures."""
    try:
        from ete3 import NCBITaxa
    except ImportError as exc:
        message = (
            "The optional ETE3 runtime could not be imported for this Python "
            "environment. Install ete3, six, and numpy with:\n"
            "  python -m pip install ete3 six numpy\n"
            "Then retry the command.\n"
            "Exception: {}"
        ).format(exc)
        raise RuntimeError(message)
    try:
        import six  # noqa: F401
        import numpy  # noqa: F401
    except ImportError as exc:
        message = (
            "The optional ETE3 runtime is incomplete: six and numpy are "
            "required with ete3. Install them with:\n"
            "  python -m pip install ete3 six numpy\n"
            "Then retry the command.\n"
            "Exception: {}"
        ).format(exc)
        raise RuntimeError(message)
    return NCBITaxa


def desc_taxa(taxid, ncbi, out_fh, just_taxids=False):
    """Write descendants of *taxid* in the source-compatible format."""
    descendant_taxa = ncbi.get_descendant_taxa(taxid)
    descendant_names = ncbi.translate_to_names(descendant_taxa)

    if just_taxids:
        for descendant_taxid in descendant_taxa:
            out_fh.write(str(descendant_taxid) + "\n")
    else:
        for descendant_name, descendant_taxid in zip(
            descendant_names, descendant_taxa
        ):
            row = [str(value) for value in (taxid, descendant_taxid, descendant_name)]
            out_fh.write("\t".join(row) + "\n")


def taxon_info(taxid, ncbi, out_fh):
    """Write name, TaxID, rank, and lineage for a supplied TaxID."""
    taxid = int(taxid)
    tax_name = ncbi.get_taxid_translator([taxid])[taxid]
    rank = list(ncbi.get_rank([taxid]).values())[0]
    lineage = ncbi.get_taxid_translator(ncbi.get_lineage(taxid))
    lineage = ";".join("{}:{}".format(key, value) for key, value in lineage.items())
    row = [str(value) for value in (tax_name, taxid, rank, lineage)]
    out_fh.write("\t".join(row) + "\n")


def name2taxid(taxids, ncbi):
    """Translate names, retaining integer input when name lookup misses."""
    new_taxids = []
    for taxid in taxids:
        try:
            new_taxids.append(ncbi.get_name_translator([taxid])[taxid][0])
        except KeyError:
            try:
                new_taxids.append(int(taxid))
            except ValueError:
                raise ValueError("Error: cannot convert to taxid: {}".format(taxid))
    return new_taxids


def _open_output(path):
    if path is None:
        return sys.stdout, False
    return open(path, "w"), True


def main(argv=None):
    """Run a deliberate ETE3 taxonomy query."""
    args = get_args(argv)
    ncbi = _load_ncbi_taxa()(dbfile=args.database)

    if args.verbose > 1:
        sys.stderr.write("Taxa database is stored at {}\n".format(ncbi.dbfile))

    if args.update:
        if args.verbose > 1:
            sys.stderr.write(
                "Updating the taxonomy database. This may take several minutes...\n"
            )
        ncbi.update_taxonomy_database()

    taxids = args.taxid.replace('"', "").replace("'", "").split(",")
    taxids = name2taxid(taxids, ncbi)

    out_fh, should_close = _open_output(args.outfile)
    try:
        if args.taxon_info:
            out_fh.write("\t".join(["name", "taxid", "rank", "lineage"]) + "\n")
        elif not args.just_taxids:
            out_fh.write(
                "\t".join(
                    ["parent_taxid", "descendent_taxid", "descendent_name"]
                )
                + "\n"
            )

        for taxid in taxids:
            if args.taxon_info:
                taxon_info(taxid, ncbi, out_fh)
            else:
                desc_taxa(taxid, ncbi, out_fh, args.just_taxids)
    finally:
        if should_close:
            out_fh.close()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
