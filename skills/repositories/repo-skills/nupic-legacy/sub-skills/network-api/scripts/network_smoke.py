#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Deterministic smoke helper for NuPIC legacy Network API.

Safe by default: this script imports nupic.engine.Network, constructs an empty
Network unless --skip-construct is passed, and never reads source checkout data
files or runs a native example. It is intended for Python 2.7-compatible NuPIC
legacy environments, but keeps syntax Python 3-compatible so --help remains
usable in modern shells.
"""
from __future__ import print_function

import argparse
import sys
import textwrap


DEFAULT_REGION_TYPES = (
    "py.RecordSensor",
    "py.SPRegion",
    "py.TMRegion",
    "py.SDRClassifierRegion",
)


PIPELINE_TEMPLATE = r'''
# Safe next-step template; fill data/model params from your project.
import json
from nupic.engine import Network
from nupic.data.file_record_stream import FileRecordStream
from nupic.encoders import MultiEncoder

network = Network()
network.addRegion("sensor", "py.RecordSensor", "{}")

sensor = network.regions["sensor"].getSelf()
sensor.encoder = MultiEncoder()
sensor.encoder.addMultipleEncoders(modelParams["sensorParams"]["encoders"])
sensor.dataSource = FileRecordStream(streamID="data.csv")

spParams = dict(modelParams["spParams"])
spParams["inputWidth"] = sensor.encoder.getWidth()
network.addRegion("SP", "py.SPRegion", json.dumps(spParams))
network.addRegion("TM", "py.TMRegion", json.dumps(modelParams["tmParams"]))

clParams = dict(modelParams["clParams"])
regionName = clParams.pop("regionName", "SDRClassifierRegion")
network.addRegion("classifier", "py.%s" % regionName, json.dumps(clParams))

network.link("sensor", "SP", "UniformLink", "",
             srcOutput="dataOut", destInput="bottomUpIn")
network.link("SP", "TM", "UniformLink", "",
             srcOutput="bottomUpOut", destInput="bottomUpIn")
network.link("TM", "classifier", "UniformLink", "",
             srcOutput="bottomUpOut", destInput="bottomUpIn")
network.link("sensor", "classifier", "UniformLink", "",
             srcOutput="bucketIdxOut", destInput="bucketIdxIn")
network.link("sensor", "classifier", "UniformLink", "",
             srcOutput="actValueOut", destInput="actValueIn")
network.link("sensor", "classifier", "UniformLink", "",
             srcOutput="categoryOut", destInput="categoryIn")

network.regions["sensor"].setParameter("predictedField", "consumption")
for name in ("SP", "TM", "classifier"):
  network.regions[name].setParameter("learningMode", 1)
  network.regions[name].setParameter("inferenceMode", 1)

network.initialize()
network.run(1)
actualValues = network.regions["classifier"].getOutputData("actualValues")
probabilities = network.regions["classifier"].getOutputData("probabilities")
'''


def _print_error(message):
  print(message, file=sys.stderr)


def _collection_names(collection):
  """Return names from a NuPIC CollectionWrapper-like object."""
  names = []
  if hasattr(collection, "getCount") and hasattr(collection, "getByIndex"):
    for i in range(collection.getCount()):
      item = collection.getByIndex(i)
      if isinstance(item, tuple) and item:
        names.append(item[0])
      elif hasattr(item, "name"):
        names.append(item.name)
      else:
        names.append(str(item))
    return names

  try:
    for item in collection:
      if isinstance(item, tuple) and item:
        names.append(item[0])
      elif hasattr(item, "name"):
        names.append(item.name)
      else:
        names.append(str(item))
  except TypeError:
    names.append(str(collection))
  return names


def _inspect_region_types(region_types):
  from nupic.engine import Region

  for region_type in region_types:
    print("region type: {0}".format(region_type))
    try:
      spec = Region.getSpecFromType(region_type)
      print("  inputs:  {0}".format(", ".join(_collection_names(spec.inputs))))
      print("  outputs: {0}".format(", ".join(_collection_names(spec.outputs))))
    except Exception as exc:
      print("  ERROR: could not inspect spec: {0}".format(exc))


def parse_args(argv):
  parser = argparse.ArgumentParser(
      description="Import and smoke-check the NuPIC legacy Network API safely.",
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent("""
      Examples:
        python scripts/network_smoke.py
        python scripts/network_smoke.py --inspect-region-types
        python scripts/network_smoke.py --print-template
        python scripts/network_smoke.py --skip-construct --inspect-region-types --region-type py.RecordSensor
      """))
  parser.add_argument(
      "--skip-construct", action="store_true",
      help="only import Network; do not instantiate an empty Network")
  parser.add_argument(
      "--inspect-region-types", action="store_true",
      help="print input/output names for common built-in region specs")
  parser.add_argument(
      "--region-type", action="append", dest="region_types",
      help="region type to inspect; may be passed multiple times; defaults to common Network API regions")
  parser.add_argument(
      "--print-template", action="store_true",
      help="print a self-contained sensor->SP->TM->classifier construction template")
  return parser.parse_args(argv)


def main(argv=None):
  args = parse_args(sys.argv[1:] if argv is None else argv)

  try:
    from nupic.engine import Network
  except ImportError as exc:
    _print_error("ERROR: could not import nupic.engine.Network: {0}".format(exc))
    _print_error("NuPIC legacy Network API usually requires Python 2.7, nupic.bindings, numpy 1.12.x-compatible packages, and compiled runtime dependencies.")
    _print_error("Fix the package/runtime import first, then rerun this smoke helper.")
    return 2
  except Exception as exc:
    _print_error("ERROR: importing nupic.engine.Network raised {0}: {1}".format(type(exc).__name__, exc))
    return 2

  print("OK: imported nupic.engine.Network")

  if not args.skip_construct:
    try:
      network = Network()
      # Do not add regions or touch data. Empty construction is enough to prove
      # the engine wrapper is available without requiring source checkout files.
      del network
      print("OK: constructed an empty Network()")
    except Exception as exc:
      _print_error("ERROR: Network() construction failed with {0}: {1}".format(type(exc).__name__, exc))
      return 3

  if args.inspect_region_types:
    region_types = args.region_types or DEFAULT_REGION_TYPES
    try:
      _inspect_region_types(region_types)
    except ImportError as exc:
      _print_error("ERROR: region spec inspection import failed: {0}".format(exc))
      return 4
    except Exception as exc:
      _print_error("ERROR: region spec inspection failed with {0}: {1}".format(type(exc).__name__, exc))
      return 4

  if args.print_template:
    print(PIPELINE_TEMPLATE.strip())

  return 0


if __name__ == "__main__":
  sys.exit(main())
