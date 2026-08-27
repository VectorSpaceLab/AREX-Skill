#!/usr/bin/env python3
"""Self-contained Metaflow starter flow.

Examples:
  USERNAME=disco python hello_flow.py --no-pylint check
  USERNAME=disco python hello_flow.py run --count 2 --items '["x", "yz"]' --max-workers 1
"""
from metaflow import FlowSpec, JSONType, Parameter, step


class SkillHelloFlow(FlowSpec):
    count = Parameter("count", default=3, type=int, help="Number of generated integer items when --items is empty.")
    items = Parameter("items", default=[], type=JSONType, help="Optional JSON list of items to process.")

    @step
    def start(self):
        source = self.items or list(range(self.count))
        if not isinstance(source, list):
            raise ValueError("--items must be a JSON list when provided")
        self.work_items = source
        self.next(self.measure, foreach="work_items")

    @step
    def measure(self):
        self.item_repr = repr(self.input)
        self.item_length = len(str(self.input))
        self.next(self.join)

    @step
    def join(self, inputs):
        self.summary = [(task.item_repr, task.item_length) for task in inputs]
        self.next(self.end)

    @step
    def end(self):
        print("SkillHelloFlow summary:", self.summary)


if __name__ == "__main__":
    SkillHelloFlow()
