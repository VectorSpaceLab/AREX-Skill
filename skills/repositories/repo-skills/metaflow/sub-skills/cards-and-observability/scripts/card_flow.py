#!/usr/bin/env python3
"""Tiny Metaflow card demo.

Examples:
  USERNAME=disco python card_flow.py --no-pylint check
  USERNAME=disco python card_flow.py run --max-workers 1
"""
from metaflow import FlowSpec, card, current, step
from metaflow.cards import Markdown


class SkillCardFlow(FlowSpec):
    @card(type="default", id="summary", customize=True)
    @step
    def start(self):
        self.message = "hello-card"
        current.card.append(Markdown("# SkillCardFlow\nThis card was created from step code."))
        self.next(self.end)

    @step
    def end(self):
        print(self.message)


if __name__ == "__main__":
    SkillCardFlow()
