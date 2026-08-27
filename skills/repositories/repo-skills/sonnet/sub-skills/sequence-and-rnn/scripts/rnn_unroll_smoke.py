#!/usr/bin/env python3
"""No-download Sonnet recurrent core unroll smoke check."""
from __future__ import annotations
import argparse, json
import tensorflow as tf
import sonnet as snt

def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--time", type=int, default=4)
  parser.add_argument("--batch", type=int, default=3)
  parser.add_argument("--features", type=int, default=5)
  parser.add_argument("--hidden", type=int, default=6)
  parser.add_argument("--json", action="store_true")
  args = parser.parse_args()
  sequence = tf.ones([args.time, args.batch, args.features])
  lstm = snt.LSTM(args.hidden)
  lstm_out, lstm_state = snt.dynamic_unroll(lstm, sequence, lstm.initial_state(args.batch))
  gru = snt.GRU(args.hidden)
  gru_out, gru_state = snt.dynamic_unroll(gru, sequence, gru.initial_state(args.batch))
  assert lstm_out.shape.as_list() == [args.time, args.batch, args.hidden]
  assert lstm_state.hidden.shape.as_list() == [args.batch, args.hidden]
  assert gru_out.shape.as_list() == [args.time, args.batch, args.hidden]
  assert gru_state.shape.as_list() == [args.batch, args.hidden]
  out = {"status":"ok","lstm_output_shape":lstm_out.shape.as_list(),"lstm_state_shapes":{"hidden":lstm_state.hidden.shape.as_list(),"cell":lstm_state.cell.shape.as_list()},"gru_output_shape":gru_out.shape.as_list()}
  print(json.dumps(out, indent=None if args.json else 2, sort_keys=args.json))
  return 0
if __name__ == "__main__":
  raise SystemExit(main())
