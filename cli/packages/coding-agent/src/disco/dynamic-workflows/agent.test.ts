import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { DefaultPackageManager } from "../../core/package-manager.ts";
import type { SettingsManager } from "../../core/settings-manager.ts";
import { formatSkillsForPrompt, getModelVisibleSkills, loadSkills } from "../../core/skills.ts";
import { buildSystemPrompt } from "../../core/system-prompt.ts";
import { getDiscoModePrompt } from "../modes/prompts.ts";
import { WorkflowAgent } from "./agent.ts";
import { createWorkflowTool } from "./workflow-tool.ts";

function createSettingsManagerStub(
	globalSettings: Record<string, unknown> = {},
	projectSettings: Record<string, unknown> = {},
	projectTrusted = false,
): SettingsManager {
	return {
		getGlobalSettings: () => globalSettings,
		getProjectSettings: () => projectSettings,
		isProjectTrusted: () => projectTrusted,
		setProjectTrusted: () => {},
	} as unknown as SettingsManager;
}

describe("WorkflowAgent sub-skill prompting", () => {
	it("tells sub-skill agents to write files directly instead of returning draft bodies", () => {
		const agent = new WorkflowAgent({ cwd: process.cwd(), discoMode: "creator", tools: [] });
		const prompt = (
			agent as unknown as {
				buildPrompt(task: string, options: { label: string; subSkill: string }, structured: boolean): string;
			}
		).buildPrompt("Draft the assigned sub-skill.", { label: "draft data", subSkill: "data-indexing" }, false);

		expect(prompt).toContain("Assigned sub-skill: data-indexing.");
		expect(prompt).toContain("write the runtime files directly in the planned output subtree before returning");
		expect(prompt).toContain("propose one or two difficult synthetic usability cases for this sub-skill");
		expect(prompt).toContain("Concrete cases belong under the artifact root's `test-cases/`");
		expect(prompt).toContain("Do not return full Markdown or script bodies for the parent/main agent to write later");
	});

	it("keeps structured output as a handoff manifest after file creation", () => {
		const agent = new WorkflowAgent({ cwd: process.cwd(), discoMode: "creator", tools: [] });
		const prompt = (
			agent as unknown as {
				buildPrompt(task: string, options: { label: string; subSkill: string }, structured: boolean): string;
			}
		).buildPrompt(
			"Draft the assigned sub-skill and return a manifest.",
			{ label: "draft data", subSkill: "data-indexing" },
			true,
		);

		expect(prompt).toContain("Your final action MUST be a structured_output tool call.");
		expect(prompt).toContain("write those files with the available file tools before structured_output");
		expect(prompt).toContain("not contain drafts for a parent agent to write later");
	});

	it("keeps Creator sub-skill drafting instructions out of Researcher prompts", () => {
		const agent = new WorkflowAgent({ cwd: process.cwd(), discoMode: "researcher", tools: [] });
		const prompt = (
			agent as unknown as {
				buildPrompt(task: string, options: { label: string; subSkill: string }, structured: boolean): string;
			}
		).buildPrompt("Investigate the benchmark failure.", { label: "inspect metrics", subSkill: "metrics" }, false);

		expect(prompt).toContain("Task label: inspect metrics");
		expect(prompt).toContain("Investigate the benchmark failure.");
		expect(prompt).not.toContain("DisCo sub-skill file contract");
		expect(prompt).not.toContain("write the runtime files directly");
		expect(prompt).not.toContain("difficult synthetic usability cases");
	});
});

describe("workflow tool prompt boundaries", () => {
	it("keeps generic orchestration guidance out of the global system prompt", () => {
		const tool = createWorkflowTool({ cwd: process.cwd() });
		const guidelines = tool.promptGuidelines?.join("\n") ?? "";

		expect(guidelines).toContain("coordinated subagents materially help");
		expect(guidelines).toContain("workflow tool schema");
		expect(guidelines).toContain("focused task and a concise label");
		expect(guidelines).not.toContain("repo-skill generation");
		expect(guidelines).not.toContain("Paper2Skills");
		expect(guidelines).not.toContain("source-script import/adaptation plan");
		expect(guidelines.length).toBeLessThan(1_500);
	});

	it("does not leak Creator construction policy into a rendered Researcher prompt", () => {
		const tool = createWorkflowTool({ cwd: process.cwd() });
		const prompt = buildSystemPrompt({
			cwd: "/workspace",
			selectedTools: [tool.name],
			toolSnippets: { [tool.name]: tool.promptSnippet },
			promptGuidelines: tool.promptGuidelines,
			appendSystemPrompt: getDiscoModePrompt("researcher"),
		});

		expect(prompt).toContain("Mode: Researcher");
		expect(prompt).toContain("skill-powered research agent");
		expect(prompt).not.toContain("ML knowledge distillation agent");
		expect(prompt).not.toContain("Paper2Skills");
		expect(prompt).not.toContain("repo-skill generation");
		expect(prompt).not.toContain("source-script import/adaptation plan");
		expect(prompt.length).toBeLessThan(5_000);
	});
});

describe("DisCo agent positioning", () => {
	it("separates the common harness from Creator and Researcher responsibilities", () => {
		const corePrompt = buildSystemPrompt({ cwd: process.cwd(), selectedTools: [] });
		const researcherPrompt = buildSystemPrompt({
			cwd: process.cwd(),
			selectedTools: [],
			appendSystemPrompt: getDiscoModePrompt("researcher"),
		});
		const creatorPrompt = buildSystemPrompt({
			cwd: process.cwd(),
			selectedTools: [],
			appendSystemPrompt: getDiscoModePrompt("creator"),
		});

		expect(corePrompt).toContain("operating inside a coding-agent harness");
		expect(corePrompt).toContain("active <disco_mode> contract appended below defines your current role");
		expect(corePrompt).not.toContain("Mode: Creator");
		expect(corePrompt).not.toContain("Mode: Researcher");

		expect(researcherPrompt).toContain("skill-powered research agent");
		expect(researcherPrompt).toContain("fixed coding-agent harness");
		expect(researcherPrompt).toContain("task-relevant operating skills as operating context");
		expect(researcherPrompt).toContain("Follow progressive disclosure");
		expect(researcherPrompt).not.toContain("distill-ml-knowledge");

		expect(creatorPrompt).toContain("ML knowledge distillation agent");
		expect(creatorPrompt).toContain("verified, task-related operating-knowledge skill graph");
		expect(creatorPrompt).toContain("distill-ml-knowledge");
		expect(creatorPrompt).not.toContain("skill-powered research agent");
		expect(creatorPrompt).not.toContain("path preference: direct | reusable | auto");
	});

	it("registers managed skills, hides opted-out skills from context, and prefers the live router", async () => {
		const tempRoot = mkdtempSync(join(tmpdir(), "disco-test-"));
		try {
			const agentDir = join(tempRoot, "agent");
			const userSkillDir = join(agentDir, "skills", "managed-user-skill");
			const liveRouterDir = join(agentDir, "skills", "repo-skills-router");
			mkdirSync(userSkillDir, { recursive: true });
			mkdirSync(liveRouterDir, { recursive: true });
			writeFileSync(
				join(userSkillDir, "SKILL.md"),
				[
					"---",
					"name: managed-user-skill",
					"description: Hidden managed runtime guidance.",
					"disable-model-invocation: true",
					"---",
					"",
					"# Managed User Skill",
				].join("\n"),
			);
			writeFileSync(
				join(liveRouterDir, "SKILL.md"),
				["---", "name: repo-skills-router", "description: Live managed router.", "---", "", "# Live Router"].join(
					"\n",
				),
			);

			const manager = new DefaultPackageManager({
				cwd: tempRoot,
				agentDir,
				settingsManager: createSettingsManagerStub(),
			});
			const resolved = await manager.resolve(async () => "skip");
			const enabledSkillPaths = resolved.skills.filter((entry) => entry.enabled).map((entry) => entry.path);
			const routerPaths = enabledSkillPaths.filter((path) => path.includes("repo-skills-router"));
			const loaded = loadSkills({
				cwd: tempRoot,
				agentDir,
				skillPaths: enabledSkillPaths,
				includeDefaults: false,
			});
			const hiddenSkill = loaded.skills.find((skill) => skill.name === "managed-user-skill");
			const modelVisibleSkills = getModelVisibleSkills(loaded.skills);
			const promptSkills = formatSkillsForPrompt(loaded.skills);

			expect(enabledSkillPaths.some((path) => path.includes("managed-user-skill"))).toBe(true);
			expect(enabledSkillPaths.some((path) => path.includes("create-repo-skill"))).toBe(true);
			expect(enabledSkillPaths.some((path) => path.includes("create-paper-skills"))).toBe(true);
			expect(routerPaths).toEqual([join(liveRouterDir, "SKILL.md")]);
			expect(hiddenSkill?.disableModelInvocation).toBe(true);
			expect(loaded.skills.some((skill) => skill.name === "repo-skills-router")).toBe(true);
			expect(modelVisibleSkills.some((skill) => skill.name === "repo-skills-router")).toBe(true);
			expect(modelVisibleSkills.some((skill) => skill.name === "managed-user-skill")).toBe(false);
			expect(promptSkills).toContain("repo-skills-router");
			expect(promptSkills).toContain("Live managed router.");
			expect(promptSkills).not.toContain("managed-user-skill");
			expect(promptSkills).not.toContain("Hidden managed runtime guidance.");

			writeFileSync(
				join(liveRouterDir, "SKILL.md"),
				[
					"---",
					"name: repo-skills-router",
					"description: Live managed router.",
					"disable-model-invocation: true",
					"---",
					"",
					"# Live Router",
				].join("\n"),
			);
			const disabledLoaded = loadSkills({
				cwd: tempRoot,
				agentDir,
				skillPaths: enabledSkillPaths,
				includeDefaults: false,
			});
			expect(disabledLoaded.skills.some((skill) => skill.name === "repo-skills-router")).toBe(true);
			expect(getModelVisibleSkills(disabledLoaded.skills).some((skill) => skill.name === "repo-skills-router")).toBe(
				false,
			);
			expect(formatSkillsForPrompt(disabledLoaded.skills)).not.toContain("repo-skills-router");
		} finally {
			rmSync(tempRoot, { recursive: true, force: true });
		}
	});

	it("loads the bundled router as a fallback when no live router exists", async () => {
		const tempRoot = mkdtempSync(join(tmpdir(), "disco-test-"));
		try {
			const agentDir = join(tempRoot, "agent");
			const manager = new DefaultPackageManager({
				cwd: tempRoot,
				agentDir,
				settingsManager: createSettingsManagerStub(),
			});
			const resolved = await manager.resolve(async () => "skip");
			const routerPaths = resolved.skills
				.filter((entry) => entry.enabled && entry.path.includes("repo-skills-router"))
				.map((entry) => entry.path);

			expect(routerPaths).toHaveLength(1);
			expect(routerPaths[0]).toContain("src/disco/skills/repo-skills-router/SKILL.md");
		} finally {
			rmSync(tempRoot, { recursive: true, force: true });
		}
	});

	it("loads project-local DisCo skills only for trusted projects", async () => {
		const tempRoot = mkdtempSync(join(tmpdir(), "disco-test-"));
		try {
			const agentDir = join(tempRoot, "agent");
			const projectSkillDir = join(tempRoot, ".disco", "skills", "project-runtime-skill");
			mkdirSync(projectSkillDir, { recursive: true });
			writeFileSync(
				join(projectSkillDir, "SKILL.md"),
				"---\nname: project-runtime-skill\ndescription: Trusted project guidance.\n---\n",
			);

			const untrustedManager = new DefaultPackageManager({
				cwd: tempRoot,
				agentDir,
				settingsManager: createSettingsManagerStub({}, {}, false),
			});
			const trustedManager = new DefaultPackageManager({
				cwd: tempRoot,
				agentDir,
				settingsManager: createSettingsManagerStub({}, {}, true),
			});
			const untrusted = await untrustedManager.resolve(async () => "skip");
			const trusted = await trustedManager.resolve(async () => "skip");

			expect(untrusted.skills.some((entry) => entry.path.includes("project-runtime-skill"))).toBe(false);
			expect(trusted.skills.some((entry) => entry.enabled && entry.path.includes("project-runtime-skill"))).toBe(
				true,
			);
		} finally {
			rmSync(tempRoot, { recursive: true, force: true });
		}
	});

	it("still honors explicitly configured skill paths", async () => {
		const tempRoot = mkdtempSync(join(tmpdir(), "disco-test-"));
		try {
			const agentDir = join(tempRoot, "agent");
			const explicitSkillDir = join(tempRoot, "explicit-skill");
			mkdirSync(explicitSkillDir, { recursive: true });
			writeFileSync(
				join(explicitSkillDir, "SKILL.md"),
				[
					"---",
					"name: explicit-skill",
					"description: This explicitly configured skill should load.",
					"---",
					"",
					"# Explicit Skill",
				].join("\n"),
			);

			const manager = new DefaultPackageManager({
				cwd: tempRoot,
				agentDir,
				settingsManager: createSettingsManagerStub({ skills: [explicitSkillDir] }),
			});
			const resolved = await manager.resolve(async () => "skip");
			const resolvedSkillPaths = resolved.skills.map((entry) => entry.path);

			expect(resolvedSkillPaths.some((path) => path.includes("explicit-skill"))).toBe(true);
		} finally {
			rmSync(tempRoot, { recursive: true, force: true });
		}
	});
});

describe("create-repo-skill authoring constraints", () => {
	function readSkillReference(relativePath: string): string {
		return readFileSync(join(process.cwd(), "packages/coding-agent/src/disco/skills/create-repo-skill", relativePath), "utf-8");
	}

	it("requires useful repo scripts to be imported, adapted, wrapped, or explicitly excluded", () => {
		const skill = readSkillReference("SKILL.md");
		const evidence = readSkillReference("references/repository-evidence.md");
		const planning = readSkillReference("references/planning-and-writing.md");

		expect(skill).toContain("source script inventory");
		expect(skill).toContain("Do not replace a useful, safe, repo-maintained script with prose-only Markdown");
		expect(evidence).toContain("Build a separate source script inventory");
		expect(evidence).toContain("Do not use `reference-only` merely because prose is easier");
		expect(planning).toContain("source script import map");
		expect(planning).toContain("Script import failure");
	});

	it("requires troubleshooting coverage maps and actionable troubleshooting references", () => {
		const skill = readSkillReference("SKILL.md");
		const planning = readSkillReference("references/planning-and-writing.md");

		expect(skill).toContain("Every generated package repo skill should include troubleshooting guidance");
		expect(skill).toContain("references/repo-routing-metadata.json");
		expect(skill).toContain("import_repo_skill.mjs");
		expect(skill).toContain("repo-skills-router");
		expect(skill).toContain("import_repo_skill.mjs");
		expect(planning).toContain("troubleshooting coverage map");
		expect(planning).toContain("Troubleshooting references should be actionable");
		expect(planning).toContain("Troubleshooting failure");
	});

	it("positions DisCo Researcher as the primary repo-skill consumer", () => {
		const skill = readSkillReference("SKILL.md");

		expect(skill).toContain("operating Agent Skill for DisCo Researcher");
		expect(skill).toContain("export is not required for DisCo to use it");
		expect(skill).toContain("DisCo Researcher can use in a new session without any cross-agent export");
		expect(skill).not.toContain("after the managed library is explicitly exported to a target agent");
	});

	it("separates test cases from reports in the review artifact tree", () => {
		const skill = readSkillReference("SKILL.md");
		const structure = readSkillReference("references/input-output-and-structure.md");
		const planning = readSkillReference("references/planning-and-writing.md");

		expect(skill).toContain("with concrete cases in `test-cases/` and reports or review documents in `reports/`");
		expect(structure).toContain("<artifact-root>/");
		expect(structure).toContain("test-cases/              # concrete usability/native-backed/synthetic cases");
		expect(structure).toContain("reports/                 # review, verification, and final handoff documents");
		expect(structure).toContain("The artifact root should not contain loose case directories or a catch-all");
		expect(planning).toContain("reports/integration/coverage-depth-matrix.md");
		expect(planning).toContain("reports/integration/difficult-case-plan.md");
	});

	it("requires difficult synthetic cases per sub-skill and integrated hard cases", () => {
		const skill = readSkillReference("SKILL.md");
		const planning = readSkillReference("references/planning-and-writing.md");

		expect(skill).toContain("plan one or two integrated difficult usability cases");
		expect(skill).toContain("prefer adapting real repo tests/examples from the native candidate map");
		expect(planning).toContain("One or two new difficult synthetic usability case ideas for that sub-skill");
		expect(planning).toContain("Every sub-skill has one or two planned difficult synthetic cases");
		expect(planning).toContain("The whole-skill plan includes one or two integrated difficult cases");
	});
});

describe("verify-repo-skill artifact constraints", () => {
	function readVerifyReference(relativePath: string): string {
		return readFileSync(join(process.cwd(), "packages/coding-agent/src/disco/skills/verify-repo-skill", relativePath), "utf-8");
	}

	it("writes concrete cases under test-cases and review deliverables under reports", () => {
		const skill = readVerifyReference("SKILL.md");
		const cases = readVerifyReference("references/usability-test-cases.md");
		const handoff = readVerifyReference("references/evaluation-verification-and-handoff.md");
		const runner = readVerifyReference("scripts/run_native_cases.py");

		expect(skill).toContain("Write concrete test cases under `test-cases/` and reports or review");
		expect(skill).toContain("scripts/update_repo_skills_router.mjs");
		expect(skill).toContain("scripts/import_repo_skill.mjs");
		expect(skill).toContain("restores both the previous skill and router on failure");
		expect(skill).toContain("Do not hand-edit router Markdown as the import mechanism");
		expect(cases).toContain("<repository-path>/skills/tests/<chosen-skill-id>/test-cases/");
		expect(cases).toContain("sub-skills/<sub-skill-id>/<scenario-slug>/");
		expect(cases).toContain("integration/<scenario-slug>/");
		expect(handoff).toContain("reports/verification/native-verification-report.json");
		expect(handoff).toContain("reports/final/final-skill-report.md");
		expect(runner).toContain("--manifest reports/verification/native-ground-truth-candidates.json");
	});

	it("requires per-sub-skill difficult cases plus integrated difficult cases", () => {
		const skill = readVerifyReference("SKILL.md");
		const cases = readVerifyReference("references/usability-test-cases.md");
		const handoff = readVerifyReference("references/evaluation-verification-and-handoff.md");

		expect(skill).toContain("For every generated");
		expect(skill).toContain("create one or two new difficult synthetic cases");
		expect(skill).toContain("create one or two integrated difficult cases");
		expect(cases).toContain("For every generated sub-skill, create one or two new difficult synthetic case");
		expect(cases).toContain("After all sub-skills are integrated, create one or two integrated difficult");
		expect(handoff).toContain("Every generated sub-skill has one or two new difficult synthetic cases");
		expect(handoff).toContain("The complete integrated skill has one or two difficult integration cases");
	});
});

describe("extend-repo-skill managed import constraints", () => {
	function readExtendReference(relativePath: string): string {
		return readFileSync(join(process.cwd(), "packages/coding-agent/src/disco/skills/extend-repo-skill", relativePath), "utf-8");
	}

	it("edits live managed skills through an external working copy and the dedicated importer", () => {
		const skill = readExtendReference("SKILL.md");
		const editing = readExtendReference("references/editing-and-versioning.md");
		const handoff = readExtendReference("references/verification-and-handoff.md");

		expect(skill).toContain("never edit the live managed copy in place");
		expect(skill).toContain("verify-repo-skill/scripts/import_repo_skill.mjs");
		expect(skill).toContain("DisCo Researcher can use the extended skill in a new session");
		expect(skill).not.toContain("Edit the existing skill in place");
		expect(editing).toContain("leave the live tree unchanged until the dedicated importer replaces it");
		expect(handoff).toContain("restores both the prior skill and router on failure");
		expect(handoff).toContain("available to DisCo Researcher");
		expect(handoff).toContain("without cross-agent export");
	});
});

describe("repo skills router and export workflow-skill constraints", () => {
	function readRepoRouter(relativePath: string): string {
		return readFileSync(join(process.cwd(), "packages/coding-agent/src/disco/skills/repo-skills-router", relativePath), "utf-8");
	}

	function readImportSkill(relativePath: string): string {
		return readFileSync(join(process.cwd(), "packages/coding-agent/src/disco/skills/import-repo-skills-to-agent", relativePath), "utf-8");
	}

	it("defines repo-skills-router as a fixed area/family progressive-disclosure router", () => {
		const skill = readRepoRouter("SKILL.md");
		const maintenance = readRepoRouter("references/maintenance.md");

		expect(skill).toContain("name: repo-skills-router");
		expect(skill).toContain("progressive disclosure");
		expect(skill).toContain("area pages");
		expect(skill).toContain("family page");
		expect(skill).toContain("../repo-skills/<skill-id>/SKILL.md");
		expect(skill).toContain("no exact family fits");
		expect(skill).toContain("DisCo Researcher");
		expect(skill).toContain("export is not required for DisCo");
		expect(skill).not.toContain("Usage Scenario Quick Map");
		expect(skill).not.toContain("references/scenarios/");
		expect(maintenance).toContain("scripts/update_repo_skills_router.mjs");
		expect(maintenance).toContain("scripts/import_repo_skill.mjs");
		expect(maintenance).toContain("restores both the previous skill and router");
		expect(maintenance).toContain("references/repo-routing-metadata.json");
		expect(maintenance).toContain("exact taxonomy");
		expect(maintenance).toContain("Do not hand-edit router Markdown as the import mechanism");
	});

	it("defines import-repo-skills-to-agent overwrite prompts and router merge behavior", () => {
		const skill = readImportSkill("SKILL.md");

		expect(skill).toContain("Use this workflow skill to copy DisCo's managed skill library into another");
		expect(skill).toContain("agent tool");
		expect(skill).toContain("DisCo already uses");
		expect(skill).toContain("at runtime through");
		expect(skill).toContain("explicit `/skill:<name>` invocation");
		expect(skill).toContain("If the path basename is `skills`, treat it as the exact target skills root");
		expect(skill).toContain("default to the current standard user-level");
		expect(skill).toContain("`~/.agents/skills/`");
		expect(skill).toContain("do not choose `~/.codex/skills` by default");
		expect(skill).toContain("<target-skills-root>/repositories/repo-skills/<skill-id>/");
		expect(skill).toContain("<target-skills-root>/repositories/repo-skills-router/");
		expect(skill).toContain("Ask the user whether to overwrite the target copy");
		expect(skill).toContain("Never silently overwrite a non-router skill");
		expect(skill).toContain("If the target already");
		expect(skill).toContain("has `repo-skills-router`, merge the filtered");
		expect(skill).toContain("must be a filtered router for the selected import set");
		expect(skill).toContain("--include-skill <selected-skill-id>");
		expect(skill).toContain("--output-router-dir <temp-dir>/repo-skills-router");
		expect(skill).toContain("Do not copy");
		expect(skill).toContain("directly for a subset import");
		expect(skill).toContain("preserving unrelated target skills and their exact assignments");
		expect(skill).toContain("the target router does not gain entries for unselected DisCo source");
		expect(skill).toContain("generated area/family index");
		expect(skill).toContain("Treat the target as Codex");
		expect(skill).toContain("scripts/apply_codex_openai_policy.py");
		expect(skill).toContain("policy.allow_implicit_invocation: false");
		expect(skill).toContain("preserve unrelated");
		expect(skill).toContain("do not rely on `disable-model-invocation: true` alone");
		expect(skill).toContain("for Codex targets, number of `agents/openai.yaml` policy files written");
	});

	it("provides a Codex policy helper that preserves existing OpenAI metadata", () => {
		const tempRoot = mkdtempSync(join(tmpdir(), "disco-codex-policy-"));
		try {
			const skillDir = join(tempRoot, "repo-skills", "target-skill");
			const nestedSkillDir = join(skillDir, "sub-skills", "first", "sub-skills", "second");
			const routerDir = join(tempRoot, "repo-skills-router");
			mkdirSync(join(skillDir, "agents"), { recursive: true });
			mkdirSync(nestedSkillDir, { recursive: true });
			mkdirSync(routerDir, { recursive: true });

			writeFileSync(join(skillDir, "SKILL.md"), '---\nname: target-skill\ndescription: "Target"\n---\n');
			writeFileSync(join(nestedSkillDir, "SKILL.md"), '---\nname: second\ndescription: "Nested"\n---\n');
			writeFileSync(join(routerDir, "SKILL.md"), '---\nname: repo-skills-router\ndescription: "Router"\n---\n');
			writeFileSync(
				join(skillDir, "agents", "openai.yaml"),
				[
					"interface:",
					'  display_name: "Target Skill"',
					"policy:",
					"  allow_implicit_invocation: true",
					"dependencies:",
					"  tools: []",
					"",
				].join("\n"),
			);

			execFileSync("python3", [
				join(process.cwd(), "packages/coding-agent/src/disco/skills/import-repo-skills-to-agent/scripts/apply_codex_openai_policy.py"),
				skillDir,
				routerDir,
			]);

			const rootPolicy = readFileSync(join(skillDir, "agents", "openai.yaml"), "utf-8");
			const nestedPolicyPath = join(nestedSkillDir, "agents", "openai.yaml");

			expect(rootPolicy).toContain("interface:");
			expect(rootPolicy).toContain('display_name: "Target Skill"');
			expect(rootPolicy).toContain("dependencies:");
			expect(rootPolicy).toContain("allow_implicit_invocation: false");
			expect(existsSync(nestedPolicyPath)).toBe(true);
			expect(readFileSync(nestedPolicyPath, "utf-8")).toBe("policy:\n  allow_implicit_invocation: false\n");
			expect(existsSync(join(routerDir, "agents", "openai.yaml"))).toBe(false);
		} finally {
			rmSync(tempRoot, { recursive: true, force: true });
		}
	});
});
