#!/usr/bin/env python3
"""Print self-contained mcp-agent workflow pattern skeletons."""

from __future__ import annotations

import argparse
import sys
import textwrap

SKELETONS: dict[str, str] = {
    "router": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.factory import AgentSpec, RequestParams, create_router_llm

        app = MCPApp(name="router_app")

        def fallback(request: str) -> str:
            """Use only when no specialized agent is appropriate."""
            return f"Fallback for: {request}"

        async def main():
            async with app.run() as running_app:
                router = await create_router_llm(
                    name="task_router",
                    agents=[
                        AgentSpec(
                            name="reader",
                            instruction="Read and summarize requested source material.",
                            server_names=["filesystem"],
                        ),
                        AgentSpec(
                            name="writer",
                            instruction="Draft polished user-facing text.",
                        ),
                    ],
                    functions=[fallback],
                    routing_instruction="Prefer the most specific capable destination; fallback only when unsupported.",
                    provider="openai",
                    request_params=RequestParams(temperature=0),
                    context=running_app.context,
                )

                choices = await router.route_to_agent("Summarize README.md", top_k=1)
                if not choices or choices[0].confidence != "high":
                    return "No high-confidence route. Ask a clarifying question."

                selected = choices[0].result
                async with selected:
                    return await selected.generate_str("Summarize README.md")
    ''',
    "embedding-router": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.factory import AgentSpec, create_router_embedding

        app = MCPApp(name="embedding_router_app")

        async def main():
            async with app.run() as running_app:
                router = await create_router_embedding(
                    provider="openai",  # or "cohere"
                    agents=[
                        AgentSpec(name="billing", instruction="Handle invoices, plans, payments, and refunds."),
                        AgentSpec(name="support", instruction="Handle troubleshooting, setup, and usage questions."),
                    ],
                    context=running_app.context,
                )

                results = await router.route_to_agent("Why was my card charged twice?", top_k=2)
                if not results or (results[0].p_score is not None and results[0].p_score < 0.55):
                    return "Low-confidence embedding route. Ask a clarifying question."
                return results[0]
    ''',
    "intent-classifier": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.factory import RequestParams, create_intent_classifier_llm
        from mcp_agent.workflows.intent_classifier.intent_classifier_base import Intent

        app = MCPApp(name="intent_app")

        INTENTS = [
            Intent(
                name="file_lookup",
                description="Open, read, or summarize a file.",
                examples=["show README", "open pyproject", "summarize this file"],
            ),
            Intent(
                name="general_question",
                description="Answer a conceptual question without tool use.",
                examples=["what is MCP", "explain router patterns"],
            ),
        ]

        async def main():
            async with app.run() as running_app:
                classifier = await create_intent_classifier_llm(
                    intents=INTENTS,
                    provider="openai",
                    classification_instruction="Return one intent unless multiple are explicitly requested.",
                    request_params=RequestParams(temperature=0, strict=True),
                    context=running_app.context,
                )
                results = await classifier.classify("Can you open README.md?", top_k=2)
                return results[0] if results else None
    ''',
    "parallel": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.factory import AgentSpec, RequestParams, create_parallel_llm

        app = MCPApp(name="parallel_app")

        async def main():
            async with app.run() as running_app:
                parallel = create_parallel_llm(
                    name="review_parallel",
                    fan_in=AgentSpec(
                        name="aggregator",
                        instruction="Merge named reviewer outputs, flag disagreements, and provide a final verdict.",
                    ),
                    fan_out=[
                        AgentSpec(name="security", instruction="Find security risks."),
                        AgentSpec(name="correctness", instruction="Find correctness issues."),
                        AgentSpec(name="maintainability", instruction="Find maintainability risks."),
                    ],
                    provider="openai",
                    request_params=RequestParams(maxTokens=2000, temperature=0.2),
                    context=running_app.context,
                )
                return await parallel.generate_str("Review this implementation plan.")
    ''',
    "parallel-function-fanin": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.factory import AgentSpec, create_parallel_llm
        from mcp_agent.workflows.parallel.fan_in import FanInInput

        app = MCPApp(name="parallel_function_fanin_app")

        def aggregate_as_markdown(messages: FanInInput) -> str:
            blocks = []
            for source, outputs in messages.items():
                text = "\n".join(str(item) for item in outputs)
                blocks.append(f"## {source}\n{text}")
            return "\n\n".join(blocks)

        async def main():
            async with app.run() as running_app:
                parallel = create_parallel_llm(
                    fan_in=aggregate_as_markdown,
                    fan_out=[
                        AgentSpec(name="pro", instruction="Argue for the proposal."),
                        AgentSpec(name="con", instruction="Argue against the proposal."),
                    ],
                    context=running_app.context,
                )
                return await parallel.generate_str("Evaluate this product idea.")
    ''',
    "orchestrator": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.factory import AgentSpec, OrchestratorOverrides, create_orchestrator

        app = MCPApp(name="orchestrator_app")

        async def main():
            async with app.run() as running_app:
                orchestrator = create_orchestrator(
                    available_agents=[
                        AgentSpec(name="researcher", instruction="Gather evidence from available sources.", server_names=["fetch"]),
                        AgentSpec(name="analyst", instruction="Analyze evidence and identify trade-offs."),
                        AgentSpec(name="writer", instruction="Produce concise Markdown output."),
                    ],
                    plan_type="iterative",
                    overrides=OrchestratorOverrides(
                        planner_instruction="Create short, verifiable steps and assign the best worker.",
                        synthesizer_instruction="Return decisions, evidence, and open risks.",
                    ),
                    provider="openai",
                    context=running_app.context,
                )
                return await orchestrator.generate_str("Research the topic and draft a recommendation.")
    ''',
    "deep-orchestrator": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.factory import AgentSpec, create_deep_orchestrator
        from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig

        app = MCPApp(name="deep_orchestrator_app")

        async def main():
            async with app.run() as running_app:
                config = DeepOrchestratorConfig.from_simple(
                    name="deep_research",
                    max_iterations=10,
                    max_tokens=50_000,
                    max_cost=1.00,
                    enable_parallel=True,
                ).with_strict_budget(max_tokens=40_000, max_cost=0.75, max_time_minutes=10)

                deep = create_deep_orchestrator(
                    available_agents=[
                        AgentSpec(name="researcher", instruction="Find verifiable facts."),
                        AgentSpec(name="writer", instruction="Synthesize accumulated knowledge."),
                    ],
                    config=config,
                    provider="openai",
                    context=running_app.context,
                )
                return await deep.generate_str("Investigate this long-horizon question.")
    ''',
    "evaluator-optimizer": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.factory import AgentSpec, RequestParams, create_evaluator_optimizer_llm
        from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer import QualityRating

        app = MCPApp(name="eval_opt_app")

        async def main():
            async with app.run() as running_app:
                checked_writer = create_evaluator_optimizer_llm(
                    optimizer=AgentSpec(name="writer", instruction="Draft a complete answer."),
                    evaluator="Require factual accuracy, concise structure, and no unsupported claims.",
                    min_rating=QualityRating.GOOD,
                    max_refinements=2,
                    provider="openai",
                    request_params=RequestParams(temperature=0.2),
                    context=running_app.context,
                )
                return await checked_writer.generate_str("Draft a release note.")
    ''',
    "swarm": r'''
        from mcp_agent.app import MCPApp
        from mcp_agent.workflows.swarm.swarm import AgentFunctionResult, DoneAgent, SwarmAgent
        from mcp_agent.workflows.swarm.swarm_openai import OpenAISwarm

        app = MCPApp(name="swarm_app")

        billing_agent = None
        support_agent = None

        def transfer_to_billing():
            return billing_agent

        def transfer_to_support():
            return support_agent

        def resolve_case():
            return DoneAgent()

        def update_context():
            return AgentFunctionResult(value="Updated case context.", context_variables={"case_status": "triaged"})

        async def main():
            global billing_agent, support_agent
            async with app.run() as running_app:
                billing_agent = SwarmAgent(
                    name="billing",
                    instruction="Handle billing issues. Resolve with resolve_case when done.",
                    functions=[resolve_case],
                    context=running_app.context,
                )
                support_agent = SwarmAgent(
                    name="support",
                    instruction="Handle technical support issues. Resolve with resolve_case when done.",
                    functions=[resolve_case],
                    context=running_app.context,
                )
                triage = SwarmAgent(
                    name="triage",
                    instruction=lambda ctx: f"Triage the customer. Current status: {ctx.get('case_status', 'new')}",
                    functions=[transfer_to_billing, transfer_to_support, update_context],
                    context=running_app.context,
                )
                swarm = OpenAISwarm(agent=triage, context_variables={"case_status": "new"})
                return await swarm.generate_str("I was charged twice and need help.")
    ''',
    "structured-output": r'''
        from pydantic import BaseModel, Field
        from mcp_agent.workflows.factory import RequestParams

        class Decision(BaseModel):
            action: str = Field(description="next action to take")
            confidence: float = Field(ge=0, le=1)
            reasons: list[str] = Field(default_factory=list)

        async def run_structured(workflow):
            return await workflow.generate_structured(
                "Decide the next action for this support request.",
                response_model=Decision,
                request_params=RequestParams(strict=True, temperature=0),
            )
    ''',
}

ALIASES = {
    "map-reduce": "parallel",
    "fan-out": "parallel",
    "fan-in": "parallel",
    "planner": "orchestrator",
    "router-embedding": "embedding-router",
    "intent": "intent-classifier",
    "eval-opt": "evaluator-optimizer",
    "structured": "structured-output",
}


def normalize_pattern(name: str) -> str:
    key = name.strip().lower().replace("_", "-")
    return ALIASES.get(key, key)


def list_patterns() -> None:
    for name in sorted(SKELETONS):
        print(name)


def print_skeleton(name: str) -> int:
    key = normalize_pattern(name)
    skeleton = SKELETONS.get(key)
    if skeleton is None:
        print(f"unknown pattern: {name}", file=sys.stderr)
        print("available patterns:", file=sys.stderr)
        for pattern in sorted(SKELETONS):
            print(f"- {pattern}", file=sys.stderr)
        return 2
    print(textwrap.dedent(skeleton).strip())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print mcp-agent workflow pattern skeletons.")
    parser.add_argument(
        "--list",
        action="store_true",
        help="list available skeleton names",
    )
    parser.add_argument(
        "--pattern",
        help="pattern name to print, such as router, parallel, orchestrator, or structured-output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        list_patterns()
        return 0
    if args.pattern:
        return print_skeleton(args.pattern)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
