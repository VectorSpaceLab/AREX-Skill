#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Deterministic NuPIC legacy direct-algorithm smoke check.

This helper imports the installed ``nupic`` package and runs a tiny
encoder -> SpatialPooler -> TemporalMemory -> SDRClassifier/anomaly loop.
It does not read the original repository checkout or any external data file.
"""
from __future__ import print_function

import argparse
import datetime
import sys


class SmokeFailure(Exception):
  """Expected smoke-check failure with a user-facing message."""



def _stderr(message):
  print(message, file=sys.stderr)



def _fail(message):
  raise SmokeFailure(message)



def _check_python_version(allow_python3):
  if sys.version_info[0] != 2:
    message = (
      "NuPIC legacy normally requires Python 2.7. This interpreter is %s. "
      "Use a Python 2.7 environment with installed nupic/nupic.bindings, or "
      "pass --allow-python3 only if you are intentionally testing imports in "
      "a ported environment." % sys.version.split()[0])
    if allow_python3:
      _stderr("WARNING: " + message)
    else:
      _fail(message)



def _import_components():
  try:
    import numpy
  except ImportError:
    _fail("Cannot import numpy. NuPIC legacy commonly uses numpy 1.12.x under Python 2.7.")

  try:
    import nupic  # noqa: F401
  except ImportError:
    _fail("Cannot import nupic. Install the legacy nupic package in the active Python 2.7 environment.")

  try:
    import nupic.bindings  # noqa: F401
  except ImportError as exc:
    _fail("Cannot import nupic.bindings (%s). SpatialPooler/TemporalMemory require the matching compiled NuPIC bindings." % exc)

  try:
    from nupic.encoders.date import DateEncoder
    from nupic.encoders.scalar import ScalarEncoder
    from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder
    from nupic.algorithms.spatial_pooler import SpatialPooler
    from nupic.algorithms.temporal_memory import TemporalMemory
    from nupic.algorithms.sdr_classifier import SDRClassifier
    from nupic.algorithms.anomaly import computeRawAnomalyScore
    from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood
  except ImportError as exc:
    text = str(exc)
    if "bindings" in text:
      _fail("NuPIC import failed because compiled bindings are missing or incompatible: %s" % exc)
    if "capnp" in text:
      _fail("NuPIC import failed while loading capnp/pycapnp: %s. Basic compute may not need serialization, but this install imports it early." % exc)
    _fail("NuPIC algorithm import failed: %s" % exc)

  try:
    import capnp  # noqa: F401
    capnp_available = True
  except ImportError:
    capnp_available = False

  return {
    "numpy": numpy,
    "DateEncoder": DateEncoder,
    "ScalarEncoder": ScalarEncoder,
    "RandomDistributedScalarEncoder": RandomDistributedScalarEncoder,
    "SpatialPooler": SpatialPooler,
    "TemporalMemory": TemporalMemory,
    "SDRClassifier": SDRClassifier,
    "computeRawAnomalyScore": computeRawAnomalyScore,
    "AnomalyLikelihood": AnomalyLikelihood,
    "capnp_available": capnp_available,
  }



def _build_encoders(components, encoder_kind):
  DateEncoder = components["DateEncoder"]
  ScalarEncoder = components["ScalarEncoder"]
  RandomDistributedScalarEncoder = components["RandomDistributedScalarEncoder"]

  time_encoder = DateEncoder(timeOfDay=(21, 9.5), weekend=21)
  if encoder_kind == "rds":
    value_encoder = RandomDistributedScalarEncoder(resolution=1.0, w=21, n=400,
                                                   seed=42, name="value")
  else:
    value_encoder = ScalarEncoder(w=21, minval=0.0, maxval=100.0,
                                  resolution=1.0, name="value",
                                  clipInput=True)
  return time_encoder, value_encoder



def _encode_row(numpy, time_encoder, value_encoder, timestamp, value):
  time_bits = numpy.zeros(time_encoder.getWidth(), dtype="uint32")
  value_bits = numpy.zeros(value_encoder.getWidth(), dtype="uint32")
  time_encoder.encodeIntoArray(timestamp, time_bits)
  value_encoder.encodeIntoArray(value, value_bits)
  encoding = numpy.concatenate([time_bits, value_bits]).astype("uint32")
  expected_width = time_encoder.getWidth() + value_encoder.getWidth()
  if len(encoding) != expected_width:
    _fail("Encoder width mismatch: expected %d bits but built %d bits." %
          (expected_width, len(encoding)))
  if int(encoding.sum()) <= 0:
    _fail("Encoded row has no active bits; check encoder parameters and input values.")
  return encoding



def _make_rows(record_count):
  base = datetime.datetime(2020, 1, 1, 0, 0)
  rows = []
  for i in range(record_count):
    timestamp = base + datetime.timedelta(hours=i)
    # Deterministic repeating pattern with one bounded jump near the end.
    value = 20.0 + float((i % 6) * 3)
    if i == record_count - 1:
      value = 70.0
    rows.append((timestamp, value))
  return rows



def _new_algorithm_objects(components, encoding_width, column_count):
  SpatialPooler = components["SpatialPooler"]
  TemporalMemory = components["TemporalMemory"]
  SDRClassifier = components["SDRClassifier"]
  AnomalyLikelihood = components["AnomalyLikelihood"]

  sp = SpatialPooler(inputDimensions=(encoding_width,),
                     columnDimensions=(column_count,),
                     potentialRadius=encoding_width,
                     potentialPct=0.8,
                     globalInhibition=True,
                     numActiveColumnsPerInhArea=10,
                     synPermActiveInc=0.03,
                     synPermInactiveDec=0.008,
                     synPermConnected=0.1,
                     seed=42)
  tm = TemporalMemory(columnDimensions=(column_count,),
                      cellsPerColumn=4,
                      activationThreshold=4,
                      initialPermanence=0.21,
                      connectedPermanence=0.5,
                      minThreshold=3,
                      maxNewSynapseCount=8,
                      permanenceIncrement=0.1,
                      permanenceDecrement=0.0,
                      predictedSegmentDecrement=0.0,
                      seed=42)
  classifier = SDRClassifier(steps=[1], alpha=0.1, actValueAlpha=0.1,
                             verbosity=0)
  likelihood = AnomalyLikelihood(learningPeriod=5, estimationSamples=5,
                                 historicWindowSize=100,
                                 reestimationPeriod=5)
  return sp, tm, classifier, likelihood



def _cells_to_columns(tm, cells):
  return sorted(set([int(tm.columnForCell(c)) for c in cells]))



def _run_pipeline(args, components):
  numpy = components["numpy"]
  computeRawAnomalyScore = components["computeRawAnomalyScore"]
  time_encoder, value_encoder = _build_encoders(components, args.encoder)

  rows = _make_rows(args.records)
  first_encoding = _encode_row(numpy, time_encoder, value_encoder,
                               rows[0][0], rows[0][1])
  encoding_width = len(first_encoding)

  if args.mode == "encoders":
    return {
      "records": args.records,
      "encoding_width": encoding_width,
      "time_width": time_encoder.getWidth(),
      "value_width": value_encoder.getWidth(),
      "active_columns_last": None,
      "active_cells_last": None,
      "prediction": None,
      "prediction_probability": None,
      "raw_anomaly_last": None,
      "likelihood_last": None,
    }

  sp, tm, classifier, likelihood = _new_algorithm_objects(
    components, encoding_width, args.columns)

  previous_predicted_columns = []
  last_active_columns = []
  last_active_cells = []
  last_result = None
  last_raw_anomaly = None
  last_likelihood = None

  for count, (timestamp, value) in enumerate(rows):
    encoding = first_encoding if count == 0 else _encode_row(
      numpy, time_encoder, value_encoder, timestamp, value)

    active_array = numpy.zeros(args.columns, dtype="uint32")
    sp.compute(encoding, True, active_array)
    if len(active_array) != args.columns:
      _fail("SpatialPooler activeArray length changed from %d to %d." %
            (args.columns, len(active_array)))
    active_columns = [int(i) for i in numpy.nonzero(active_array)[0]]
    if not active_columns:
      _fail("SpatialPooler produced no active columns; check SP parameters and encoder output.")

    raw_anomaly = computeRawAnomalyScore(active_columns,
                                         previous_predicted_columns)
    if raw_anomaly < 0.0 or raw_anomaly > 1.0:
      _fail("Raw anomaly score out of range: %r" % (raw_anomaly,))

    tm.compute(active_columns, learn=True)
    active_cells = list(tm.getActiveCells())
    if not active_cells:
      _fail("TemporalMemory produced no active cells; check activeColumns and TM dimensions.")

    previous_predicted_columns = _cells_to_columns(tm, tm.getPredictiveCells())
    last_likelihood = likelihood.anomalyProbability(value, raw_anomaly,
                                                    timestamp)
    if last_likelihood < 0.0 or last_likelihood > 1.0:
      _fail("Anomaly likelihood out of range: %r" % (last_likelihood,))

    if args.mode in ("classifier", "all"):
      bucket_idx = value_encoder.getBucketIndices(value)[0]
      last_result = classifier.compute(
        recordNum=count,
        patternNZ=active_cells,
        classification={"bucketIdx": bucket_idx, "actValue": value},
        learn=True,
        infer=True)
      if "actualValues" not in last_result or 1 not in last_result:
        _fail("SDRClassifier result keys were %r; expected 'actualValues' and 1." %
              (sorted(last_result.keys()),))

    last_active_columns = active_columns
    last_active_cells = active_cells
    last_raw_anomaly = raw_anomaly

  prediction = None
  prediction_probability = None
  if last_result is not None:
    best = sorted(zip(last_result[1], last_result["actualValues"]),
                  reverse=True)[0]
    prediction_probability = float(best[0])
    prediction = best[1]

  return {
    "records": args.records,
    "encoding_width": encoding_width,
    "time_width": time_encoder.getWidth(),
    "value_width": value_encoder.getWidth(),
    "active_columns_last": len(last_active_columns),
    "active_cells_last": len(last_active_cells),
    "prediction": prediction,
    "prediction_probability": prediction_probability,
    "raw_anomaly_last": float(last_raw_anomaly),
    "likelihood_last": float(last_likelihood),
  }



def _parse_args(argv):
  parser = argparse.ArgumentParser(
    description=("Run a deterministic NuPIC legacy direct algorithm smoke "
                 "check without reading the original repository checkout."))
  parser.add_argument("--mode", default="all",
                      choices=["encoders", "sp_tm", "classifier", "anomaly", "all"],
                      help="Subset to validate. 'sp_tm' and 'anomaly' run the SP/TM/anomaly loop without classifier assertions.")
  parser.add_argument("--records", type=int, default=20,
                      help="Number of deterministic stream records to process; minimum 3. Default: 20.")
  parser.add_argument("--columns", type=int, default=128,
                      help="SpatialPooler/TemporalMemory column count. Default: 128.")
  parser.add_argument("--encoder", default="scalar", choices=["scalar", "rds"],
                      help="Scalar encoder implementation: bounded ScalarEncoder or RandomDistributedScalarEncoder. Default: scalar.")
  parser.add_argument("--allow-python3", action="store_true",
                      help="Do not stop solely because the interpreter is Python 3. NuPIC legacy imports are still expected to fail unless ported.")
  return parser.parse_args(argv)



def main(argv=None):
  args = _parse_args(argv if argv is not None else sys.argv[1:])
  if args.records < 3:
    _fail("--records must be at least 3 so classifier/anomaly checks see a short stream.")
  if args.columns < 16:
    _fail("--columns must be at least 16 for a meaningful tiny SP/TM smoke check.")

  _check_python_version(args.allow_python3)
  components = _import_components()
  summary = _run_pipeline(args, components)

  print("PASS NuPIC legacy direct algorithm smoke")
  print("python=%s" % sys.version.split()[0])
  print("capnp_available=%s" % components["capnp_available"])
  print("records=%d mode=%s encoder=%s columns=%d" %
        (summary["records"], args.mode, args.encoder, args.columns))
  print("widths: time=%d value=%d total=%d" %
        (summary["time_width"], summary["value_width"],
         summary["encoding_width"]))
  if summary["active_columns_last"] is not None:
    print("last_active_columns=%d last_active_cells=%d" %
          (summary["active_columns_last"], summary["active_cells_last"]))
  if summary["prediction"] is not None:
    print("last_1step_prediction=%r probability=%.6f" %
          (summary["prediction"], summary["prediction_probability"]))
  if summary["raw_anomaly_last"] is not None:
    print("last_raw_anomaly=%.6f likelihood=%.6f" %
          (summary["raw_anomaly_last"], summary["likelihood_last"]))
  return 0



if __name__ == "__main__":
  try:
    sys.exit(main())
  except SmokeFailure as exc:
    _stderr("FAIL: %s" % exc)
    sys.exit(2)
  except Exception as exc:
    _stderr("FAIL: unexpected error: %s: %s" %
            (exc.__class__.__name__, exc))
    sys.exit(1)
