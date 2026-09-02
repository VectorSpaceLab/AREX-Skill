from dataclasses import dataclass, asdict
@dataclass
class PromptParts:
    context: str; query: str; prefix: str = ""; task: str = "generic"; separator: str = "\n"
    def validate(self):
        if not isinstance(self.context, str) or not self.context.strip(): raise ValueError("context must be non-empty")
        if not isinstance(self.query, str) or not self.query.strip(): raise ValueError("query must be non-empty")
        if not isinstance(self.prefix, str): raise ValueError("prefix must be a string")
        return self
    def full_prompt(self): self.validate(); return f"{self.context}{self.separator}{self.query}{self.prefix}"
    def prior_prompt(self): self.validate(); return f"{self.query}{self.prefix}"
    def to_record(self):
        full=self.full_prompt(); prior=self.prior_prompt()
        return {**asdict(self), "full_prompt":full, "prior_prompt":prior, "context_in_full":self.context in full, "context_absent_from_prior":self.context not in prior}
def build_prompt_record(context, query, prefix="", task="generic", separator="\n"):
    return PromptParts(context, query, prefix, task, separator).to_record()
