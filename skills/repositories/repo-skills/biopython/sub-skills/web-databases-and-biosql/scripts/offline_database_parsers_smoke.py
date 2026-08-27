#!/usr/bin/env python3
"""Offline smoke test for Biopython web-database parser modules.

This script intentionally uses only in-memory data and import checks. It does
not contact Entrez, UniProt, ExPASy, KEGG, BLAST, or any database server.
"""

from __future__ import annotations

from io import BytesIO, StringIO
import warnings

warnings.filterwarnings(
    "ignore",
    message="You may be importing Biopython from inside the source tree.*",
)


def _blocked_network(*_args, **_kwargs):
    raise AssertionError("offline smoke test attempted a network call")


def _patch_network_entry_points() -> None:
    from Bio import Entrez
    import Bio.Entrez.Parser as entrez_parser
    from Bio import ExPASy, UniProt
    from Bio.KEGG import REST as kegg_rest

    Entrez.urlopen = _blocked_network
    entrez_parser.urlopen = _blocked_network
    ExPASy.urlopen = _blocked_network
    UniProt.urlopen = _blocked_network
    kegg_rest.urlopen = _blocked_network

    try:
        from Bio import Blast
    except ImportError:
        return
    if hasattr(Blast, "urlopen"):
        Blast.urlopen = _blocked_network


def _check_entrez_xml_parser() -> None:
    from Bio import Entrez

    xml = b'''<?xml version="1.0"?>
<!DOCTYPE eInfoResult PUBLIC "-//NLM//DTD eInfoResult, 11 May 2002//EN" "https://www.ncbi.nlm.nih.gov/entrez/query/DTD/eInfo_020511.dtd">
<eInfoResult><DbList><DbName>pubmed</DbName><DbName>nuccore</DbName></DbList></eInfoResult>
'''
    record = Entrez.read(BytesIO(xml))
    assert record["DbList"] == ["pubmed", "nuccore"]


def _check_medline_parser() -> None:
    from Bio import Medline

    text = """PMID- 1
TI  - A tiny offline MEDLINE record.
AU  - Doe J
AB  - Parser smoke.

"""
    record = Medline.read(StringIO(text))
    assert record["PMID"] == "1"
    assert record["AU"] == ["Doe J"]
    assert "offline" in record["TI"]


def _check_swissprot_parser() -> None:
    from Bio import SwissProt

    text = """ID   TINY_TEST Reviewed; 4 AA.
AC   P00000;
DT   01-JAN-2000, integrated into UniProtKB/Swiss-Prot.
DT   01-JAN-2000, sequence version 1.
DT   01-JAN-2000, entry version 1.
DE   RecName: Full=Tiny test protein;
OS   Synthetic construct.
OC   other sequences.
OX   NCBI_TaxID=32630;
SQ   SEQUENCE   4 AA;  477 MW;  ABCDEF1234567890 CRC64;
     MAAA
//
"""
    record = SwissProt.read(StringIO(text))
    assert record.entry_name == "TINY_TEST"
    assert record.accessions == ["P00000"]
    assert record.sequence == "MAAA"


def _check_kegg_parser() -> None:
    from Bio.KEGG import Enzyme

    text = """ENTRY       EC 5.4.2.2                 Enzyme
NAME        Phosphoglucomutase
CLASS       Isomerases;
            Intramolecular transferases;
            Phosphotransferases (phosphomutases)
SYSNAME     alpha-D-glucose 1,6-phosphomutase
///
"""
    record = Enzyme.read(StringIO(text))
    assert record.entry == "5.4.2.2"
    assert record.name == ["Phosphoglucomutase"]
    assert "Isomerases;" in record.classname


def _check_import_surface() -> None:
    from Bio import Blast, Entrez, ExPASy, GenBank, Medline, SwissProt, UniProt
    from Bio.KEGG import REST
    from BioSQL import BioSeqDatabase

    assert callable(Entrez.read)
    assert callable(Entrez.parse)
    assert callable(Medline.parse)
    assert callable(GenBank.parse)
    assert callable(SwissProt.parse)
    assert callable(UniProt.search)
    assert callable(ExPASy.get_sprot_raw)
    assert callable(REST.kegg_get)
    assert callable(Blast.qblast)
    assert callable(BioSeqDatabase.open_database)


def main() -> None:
    _patch_network_entry_points()
    _check_import_surface()
    _check_entrez_xml_parser()
    _check_medline_parser()
    _check_swissprot_parser()
    _check_kegg_parser()
    print("PASS")


if __name__ == "__main__":
    main()
