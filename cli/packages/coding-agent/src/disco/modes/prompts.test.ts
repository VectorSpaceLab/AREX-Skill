import { describe, expect, it } from "vitest";
import { buildSystemPrompt } from "../../core/system-prompt.ts";
import { getDiscoModePrompt } from "./prompts.ts";

describe("DisCo mode prompts", () => {
	it("keeps Creator focused on ML knowledge distillation", () => {
		const prompt = getDiscoModePrompt("creator");

		expect(prompt).toContain("Mode: Creator");
		expect(prompt).toContain("ML knowledge distillation agent");
		expect(prompt).toContain("verified, task-related operating-knowledge skill graph");
		expect(prompt).toContain("Only visible meta and shared skills are eligible");
		expect(prompt).toContain("distill-ml-knowledge");
		expect(prompt).toContain("Detailed source routing, direct versus reusable construction");
		expect(prompt).toContain("source anchor, intended use, verification target");
		expect(prompt).toContain("construction record");
		expect(prompt).toContain("If asked to perform the downstream task, state the mode mismatch");
		expect(prompt).toContain("restart with --agent-mode researcher");
		expect(prompt).not.toContain("path preference: direct | reusable | auto");
		expect(prompt).not.toContain("repo-to-skills output as a high-reuse managed special case");
		expect(prompt).not.toContain("Mode: Researcher");
		expect(prompt).not.toContain("skill-powered research agent");
		expect(prompt.length).toBeLessThan(2_000);
	});

	it("keeps Researcher focused on task execution and gap handoff", () => {
		const prompt = getDiscoModePrompt("researcher");

		expect(prompt).toContain("Mode: Researcher");
		expect(prompt).toContain("skill-powered research agent");
		expect(prompt).toContain("fixed coding-agent harness");
		expect(prompt).toContain("task-relevant operating skills as operating context");
		expect(prompt).toContain("Only visible operating and shared skills are eligible");
		expect(prompt).toContain("investigation, implementation, experiments, and verification");
		expect(prompt).toContain("current task, environment, constraints, and evaluator");
		expect(prompt).toContain("Follow progressive disclosure");
		expect(prompt).toContain("do not preload the full skill graph");
		expect(prompt).toContain("concrete capability gap");
		expect(prompt).toContain("restart with --agent-mode creator");
		expect(prompt).not.toContain("Mode: Creator");
		expect(prompt).not.toContain("ML knowledge distillation agent");
		expect(prompt).not.toContain("distill-ml-knowledge");
		expect(prompt.length).toBeLessThan(2_000);
	});

	it("retains an appended mode contract with a custom core prompt", () => {
		const prompt = buildSystemPrompt({
			cwd: "/workspace",
			customPrompt: "Custom harness contract.",
			selectedTools: ["read"],
			appendSystemPrompt: getDiscoModePrompt("creator"),
		});

		expect(prompt).toContain("Custom harness contract.");
		expect(prompt).toContain("Mode: Creator");
		expect(prompt).toContain("Current working directory: /workspace");
	});
});
