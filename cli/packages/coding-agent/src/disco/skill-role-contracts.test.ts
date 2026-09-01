import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative, sep } from "node:path";
import { describe, expect, it } from "vitest";
import { parse } from "yaml";
import { getModelVisibleSkills, loadSkills } from "../core/skills.ts";

const skillsRoot = join(process.cwd(), "packages", "coding-agent", "src", "disco", "skills");
const metaSkillIds = [
	"analyze-paper-recovery",
	"create-paper-module-skill",
	"create-paper-skills",
	"create-repo-skill",
	"design-meta-skill",
	"distill-ml-knowledge",
	"extend-repo-skill",
	"import-repo-skills-to-agent",
	"paper-skills-distiller",
	"plan-paper-skill-modules",
	"prepare-paper-recovery-env",
	"prepare-repo-skill-env",
	"recover-paper-result",
	"refresh-repo-skill",
	"verify-repo-skill",
] as const;
const operatingSkillIds = ["repo-skills-router"] as const;
const sharedSkillIds = ["workflow-authoring"] as const;

function collectSkillFiles(root: string): string[] {
	const files: string[] = [];
	for (const entry of readdirSync(root, { withFileTypes: true })) {
		if (entry.isSymbolicLink()) continue;
		const path = join(root, entry.name);
		if (entry.isDirectory()) files.push(...collectSkillFiles(path));
		else if (entry.isFile() && entry.name === "SKILL.md") files.push(path);
	}
	return files.sort();
}

function collectAgentsDirectories(root: string): string[] {
	const directories: string[] = [];
	for (const entry of readdirSync(root, { withFileTypes: true })) {
		if (!entry.isDirectory() || entry.isSymbolicLink()) continue;
		const path = join(root, entry.name);
		if (entry.name === "agents") directories.push(path);
		else directories.push(...collectAgentsDirectories(path));
	}
	return directories.sort();
}

function parseFrontmatter(filePath: string): Record<string, unknown> {
	const content = readFileSync(filePath, "utf8");
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	expect(match, `${filePath} must contain YAML frontmatter`).toBeTruthy();
	const frontmatter = parse(match?.[1] ?? "");
	expect(frontmatter, `${filePath} frontmatter must be a mapping`).toBeTypeOf("object");
	return frontmatter as Record<string, unknown>;
}

function readDiscoRole(filePath: string): unknown {
	const metadata = parseFrontmatter(filePath).metadata;
	return typeof metadata === "object" && metadata !== null && !Array.isArray(metadata)
		? (metadata as Record<string, unknown>)["disco-role"]
		: undefined;
}

function runPython(scriptPath: string, args: string[]) {
	return spawnSync(process.env.PYTHON ?? "python3", [scriptPath, ...args], { encoding: "utf8" });
}

describe("DisCo-owned skill role contracts", () => {
	it("classifies every bundled SKILL.md explicitly and consistently", () => {
		const expectedTopLevelIds = [...metaSkillIds, ...operatingSkillIds, ...sharedSkillIds].sort();
		const actualTopLevelIds = readdirSync(skillsRoot, { withFileTypes: true })
			.filter((entry) => entry.isDirectory() && !entry.isSymbolicLink())
			.map((entry) => entry.name)
			.filter((skillId) => collectSkillFiles(join(skillsRoot, skillId)).length > 0)
			.sort();
		expect(actualTopLevelIds).toEqual(expectedTopLevelIds);

		const metaIds = new Set<string>(metaSkillIds);
		const operatingIds = new Set<string>(operatingSkillIds);
		const sharedIds = new Set<string>(sharedSkillIds);
		const files = collectSkillFiles(skillsRoot);
		expect(files.length).toBeGreaterThan(0);

		for (const filePath of files) {
			const relativePath = relative(skillsRoot, filePath);
			const topLevelId = relativePath.split(sep)[0];
			const expectedRole = metaIds.has(topLevelId)
				? "meta"
				: operatingIds.has(topLevelId)
					? "operating"
					: sharedIds.has(topLevelId)
						? "shared"
						: undefined;
			expect(expectedRole, `${relativePath} belongs to an unclassified bundled skill`).toBeDefined();
			expect(readDiscoRole(filePath), relativePath).toBe(expectedRole);
		}
	});

	it("keeps design-meta-skill aligned with its validator contract", () => {
		const skillDir = join(skillsRoot, "design-meta-skill");
		const validator = join(skillDir, "scripts", "validate_meta_skill.mjs");
		const result = spawnSync(process.execPath, [validator, skillDir, "--json"], { encoding: "utf8" });

		expect(result.status, result.stderr).toBe(0);
		const report = JSON.parse(result.stdout) as {
			valid: boolean;
			files: number;
			errors: string[];
		};
		expect(report.valid).toBe(true);
		expect(report.files).toBeGreaterThan(0);
		expect(report.errors).toEqual([]);
	});

	it("keeps distill-ml-knowledge and design-meta-skill model-visible", () => {
		const loaded = loadSkills({
			cwd: process.cwd(),
			agentDir: join(tmpdir(), "disco-role-contracts-agent"),
			skillPaths: [join(skillsRoot, "design-meta-skill"), join(skillsRoot, "distill-ml-knowledge")],
			includeDefaults: false,
			discoMode: "creator",
		});
		const modelVisibleSkills = getModelVisibleSkills(loaded.skills);

		expect(modelVisibleSkills.some((skill) => skill.name === "distill-ml-knowledge")).toBe(true);
		expect(modelVisibleSkills.some((skill) => skill.name === "design-meta-skill")).toBe(true);
	});

	it("keeps canonical routing ownership in distill-ml-knowledge", () => {
		const distillDir = join(skillsRoot, "distill-ml-knowledge");
		const designDir = join(skillsRoot, "design-meta-skill");
		const distill = readFileSync(join(distillDir, "SKILL.md"), "utf8");
		const contract = readFileSync(
			join(distillDir, "references", "task-and-construction-contract.md"),
			"utf8",
		);
		const selection = readFileSync(join(distillDir, "references", "construction-strategy-and-adequacy.md"), "utf8");
		const direct = readFileSync(join(distillDir, "references", "direct-construction-and-handoff.md"), "utf8");
		const design = readFileSync(join(designDir, "SKILL.md"), "utf8");
		const reusableBundle = readFileSync(
			join(designDir, "references", "reusable-bundle-specification.md"),
			"utf8",
		);

		expect(distill).toContain("task-and-construction-contract.md");
		expect(distill).toContain("construction-strategy-and-adequacy.md");
		expect(contract).toContain("tau = (q, D, E, g)");
		expect(contract).toContain("anchor `z`");
		expect(contract).toContain("scoped capabilities `Q`");
		expect(contract).toContain("grounded evidence `X`");
		expect(contract).toContain("candidate graph `G_tilde`");
		expect(contract).toContain("accepted graph `G`");
		expect(contract).toContain("construction record `R`");
		expect(contract).toContain("construction strategy: direct | reuse-existing | design-reusable");
		expect(contract).toContain("## Clarification Gate");
		expect(contract).toContain("Approval of a record containing a blocking unknown");
		expect(contract).toContain("does not resolve that unknown");
		expect(contract).toContain("explicit, reversible assumptions");
		expect(selection).toContain("reuse mode: single");
		expect(selection).toContain("reuse mode: compose");
		expect(direct).toContain("construction strategy: direct");
		expect(direct).toContain("assumption-safe unknowns");
		expect(direct).not.toContain("tau = (x, E, B, J)");
		expect(selection).toContain("construction strategy: direct | reuse-existing | design-reusable");
		expect(design).toContain("design-reusable` is a Creator");
		expect(design).toContain("exact missing blocking fields");
		expect(design).toContain("stop before use");
		expect(design).toMatch(/Do not\s+start another reuse, composition, or\s+gap decision here/);
		expect(design).not.toContain("adequacy-and-capability-matrix.md");
		expect(reusableBundle).toMatch(/Do not use this specification to select a strategy/);
		expect(reusableBundle).toMatch(/exact missing fields or changed evidence/);
		expect(reusableBundle).toContain("tau = (q, D, E, g)");
		expect(reusableBundle).toContain("Future Anchor Contract");
		expect(existsSync(join(designDir, "references", "adequacy-and-capability-matrix.md"))).toBe(false);
		expect(existsSync(join(designDir, "references", "construction-specification.md"))).toBe(false);
	});

	it("keeps every bundled meta skill free of target-specific agents manifests", () => {
		const agentsDirectories = metaSkillIds.flatMap((skillId) => collectAgentsDirectories(join(skillsRoot, skillId)));

		expect(agentsDirectories).toEqual([]);
	});

	it("keeps repository-skill export explicitly available as a Creator meta operation", () => {
		const importSkill = readFileSync(
			join(skillsRoot, "import-repo-skills-to-agent", "SKILL.md"),
			"utf8",
		);

		expect(importSkill).toContain("This is a Creator-mode meta workflow");
		expect(importSkill).toContain("not downstream research");
		expect(importSkill).toContain("Creator may inspect them as export inputs without using");
		expect(importSkill).toContain("them as operating context or asking the user to switch to Researcher");
		expect(importSkill).toContain("explicit exception to the operating-context visibility");
		expect(importSkill).toContain("boundary: inspect them only to resolve and validate the export");
		expect(importSkill).toContain("never to");
		expect(importSkill).toContain("invoke their instructions or perform their downstream workflows");
	});

	it("keeps prepare-repo-skill-env transparent and command-driven", () => {
		const skillDir = join(skillsRoot, "prepare-repo-skill-env");
		const skill = readFileSync(join(skillDir, "SKILL.md"), "utf8");
		const installPlanning = readFileSync(join(skillDir, "references", "install-planning.md"), "utf8");
		const verification = readFileSync(
			join(skillDir, "references", "verification-and-failure-report.md"),
			"utf8",
		);
		const caller = readFileSync(join(skillsRoot, "create-repo-skill", "SKILL.md"), "utf8");
		const callerInputs = readFileSync(
			join(skillsRoot, "create-repo-skill", "references", "input-output-and-structure.md"),
			"utf8",
		);
		const skillsReadme = readFileSync(join(skillsRoot, "README.md"), "utf8");
		const environmentDocs = [skill, installPlanning, verification, caller, callerInputs, skillsReadme].join("\n");

		expect(existsSync(join(skillDir, "scripts"))).toBe(false);
		expect(skill).toContain('conda create --yes --prefix "/absolute/path/to/inspection-env"');
		expect(skill).toContain('python3.11 -m venv "/absolute/path/to/inspection-env"');
		expect(skill).toContain('conda run --prefix "/absolute/path/to/inspection-env" python -m pip check');
		expect(skill).toContain("Never install into or mutate Conda `base`");
		expect(skill).toContain("Never mutate a user-provided environment");
		expect(skill).toContain("repo_env_report.json");
		expect(environmentDocs).not.toContain("setup_repo_conda_env.py");
		expect(environmentDocs).not.toContain("bootstrap_python.mjs");
		expect(environmentDocs).not.toContain("bootstrap a private host Python");
	});

	it("keeps the Creator workflow authoring and prepared-environment handoff contracts aligned", () => {
		const creatorDir = join(skillsRoot, "create-repo-skill");
		const creator = readFileSync(join(creatorDir, "SKILL.md"), "utf8");
		const planning = readFileSync(join(creatorDir, "references", "planning-and-writing.md"), "utf8");
		const authoring = readFileSync(join(skillsRoot, "workflow-authoring", "SKILL.md"), "utf8");
		const prepareReport = readFileSync(
			join(skillsRoot, "prepare-repo-skill-env", "references", "verification-and-failure-report.md"),
			"utf8",
		);

		expect(creator).toContain("../workflow-authoring/SKILL.md");
		expect(creator).toMatch(/before the first `workflow` call[\s\S]*workflow-authoring\/SKILL\.md/i);
		expect(planning).toMatch(/before the first `workflow` call[\s\S]*workflow-authoring\/SKILL\.md/i);
		for (const content of [creator, planning, authoring, prepareReport]) {
			expect(content).toContain("executable");
			expect(content).toContain("package");
			expect(content).toContain("version");
		}
		expect(prepareReport).toContain('"workflowEnvironment"');
		expect(prepareReport).toContain('"pythonExecutable"');
		expect(prepareReport).toMatch(/pythonExecutable[\s\S]*not[\s\S]*directly[\s\S]*agent\(\)/i);
		expect(authoring).toContain("metadata:\n  disco-role: shared");
	});

	it("requires backend-aware repo-skill environments, native verification, and import gates", () => {
		const creator = readFileSync(join(skillsRoot, "create-repo-skill", "SKILL.md"), "utf8");
		const repoEvidence = readFileSync(
			join(skillsRoot, "create-repo-skill", "references", "repository-evidence.md"),
			"utf8",
		);
		const prepare = readFileSync(join(skillsRoot, "prepare-repo-skill-env", "SKILL.md"), "utf8");
		const prepareHardware = readFileSync(
			join(skillsRoot, "prepare-repo-skill-env", "references", "hardware-and-backends.md"),
			"utf8",
		);
		const verifier = readFileSync(join(skillsRoot, "verify-repo-skill", "SKILL.md"), "utf8");
		const verifierHandoff = readFileSync(
			join(skillsRoot, "verify-repo-skill", "references", "evaluation-verification-and-handoff.md"),
			"utf8",
		);

		expect(repoEvidence).toContain("Backend criticality");
		expect(repoEvidence).toContain("CPU substitute");
		expect(repoEvidence).toContain("backend verification plan");
		expect(creator).toContain("minimum environment set that satisfies every required backend");
		expect(prepare).toContain("smallest environment set that covers every required backend");
		expect(prepare).toContain('"schemaVersion": 2');
		expect(prepare).toContain('Use `status: "partial"` only after explicit user acceptance');
		expect(prepareHardware).toContain("Do not silently use CPU");
		expect(verifier).toContain("BLOCKED_REQUIRED_BACKEND");
		expect(verifier).toContain("required-backend block disables auto-import");
		expect(verifierHandoff).toContain("Synthetic assertions, source inspection, docs, and");
		expect(verifierHandoff).toContain("override `auto-import` to a manual");
	});

	it("marks unavailable required accelerator native cases as import blockers", () => {
		const runner = join(skillsRoot, "verify-repo-skill", "scripts", "run_native_cases.py");
		const tempRoot = mkdtempSync(join(tmpdir(), "disco-native-backend-contract-"));
		const manifestPath = join(tempRoot, "candidates.json");
		const reportPath = join(tempRoot, "report.json");

		try {
			writeFileSync(
				manifestPath,
				`${JSON.stringify(
					{
						cases: [
							{
								id: "required-cuda",
								safety_class: "skip-gpu-or-hardware",
								backend_requirement: "cuda",
								backend_criticality: "required",
								cpu_substitute: "none",
								skip_reason: "no compatible GPU is visible",
							},
							{
								id: "optional-cuda",
								safety_class: "skip-gpu-or-hardware",
								backend_requirement: "cuda",
								backend_criticality: "optional",
								cpu_substitute: "none",
								skip_reason: "optional GPU coverage is unavailable",
							},
						],
					},
					null,
					2,
				)}\n`,
				"utf8",
			);

			const result = runPython(runner, [
				"--repo-root",
				tempRoot,
				"--manifest",
				manifestPath,
				"--out",
				reportPath,
			]);
			expect(result.status, result.stderr).toBe(1);
			const report = JSON.parse(readFileSync(reportPath, "utf8")) as {
				schema: string;
				summary: Record<string, number>;
				results: Array<{ id: string; status: string; backend_requirement: string }>;
			};
			expect(report.schema).toBe("disco.native-verification-report.v2");
			expect(report.summary).toEqual({ BLOCKED_REQUIRED_BACKEND: 1, SKIP_UNSAFE: 1 });
			expect(report.results).toEqual(
				expect.arrayContaining([
					expect.objectContaining({
						id: "required-cuda",
						status: "BLOCKED_REQUIRED_BACKEND",
						backend_requirement: "cuda",
					}),
					expect.objectContaining({ id: "optional-cuda", status: "SKIP_UNSAFE" }),
				]),
			);
		} finally {
			rmSync(tempRoot, { recursive: true, force: true });
		}
	});

	it("generates operating paper skills and rejects missing or incorrect roles", () => {
		const skillRoot = join(skillsRoot, "create-paper-module-skill");
		const generator = join(skillRoot, "scripts", "create_skill_skeleton.py");
		const validator = join(skillRoot, "scripts", "validate_skill_tree.py");
		const tempRoot = mkdtempSync(join(tmpdir(), "disco-paper-skill-role-"));
		const generatedDir = join(tempRoot, "generated-module");

		try {
			const generated = runPython(generator, [
				generatedDir,
				"--name",
				"Generated Module",
				"--description",
				"Use this generated module for reproducible paper method execution and verification.",
			]);
			expect(generated.status, generated.stderr).toBe(0);
			const skillPath = join(generatedDir, "SKILL.md");
			expect(readDiscoRole(skillPath)).toBe("operating");
			expect(parseFrontmatter(skillPath).name).toBe("generated-module");

			const valid = runPython(validator, [generatedDir]);
			expect(valid.status, valid.stderr).toBe(0);
			expect((JSON.parse(valid.stdout) as { ok: boolean }).ok).toBe(true);

			const importer = join(skillsRoot, "distill-ml-knowledge", "scripts", "import_operating_skill_graph.mjs");
			const agentDir = join(tempRoot, "agent");
			const imported = spawnSync(
				process.execPath,
				[importer, "--scope", "managed", "--agent-dir", agentDir, generatedDir],
				{ encoding: "utf8" },
			);
			expect(imported.status, imported.stderr).toBe(0);
			expect(existsSync(join(agentDir, "skills", "generated-module", "SKILL.md"))).toBe(true);

			const original = readFileSync(skillPath, "utf8");
			writeFileSync(skillPath, original.replace("disco-role: operating", "disco-role: meta"), "utf8");
			const wrongRole = runPython(validator, [generatedDir]);
			expect(wrongRole.status).toBe(2);
			expect((JSON.parse(wrongRole.stdout) as { errors: string[] }).errors).toContain(
				"frontmatter metadata.disco-role must be operating",
			);

			writeFileSync(skillPath, original.replace("disco-role: operating", "disco-role: shared"), "utf8");
			const sharedRole = runPython(validator, [generatedDir]);
			expect(sharedRole.status).toBe(2);
			expect((JSON.parse(sharedRole.stdout) as { errors: string[] }).errors).toContain(
				"frontmatter metadata.disco-role must be operating",
			);

			writeFileSync(skillPath, original.replace("metadata:\n  disco-role: operating\n", ""), "utf8");
			const missingRole = runPython(validator, [generatedDir]);
			expect(missingRole.status).toBe(2);
			expect((JSON.parse(missingRole.stdout) as { errors: string[] }).errors).toContain(
				"frontmatter metadata.disco-role must be operating",
			);
		} finally {
			rmSync(tempRoot, { recursive: true, force: true });
		}
	});

	it("requires import-compatible paper module skill names", () => {
		const validator = join(skillsRoot, "plan-paper-skill-modules", "scripts", "validate_module_plan.py");
		const tempRoot = mkdtempSync(join(tmpdir(), "disco-paper-module-plan-"));
		const planPath = join(tempRoot, "module_plan.json");
		const plan = {
			schema_version: 1,
			paper_id: "paper",
			title: "Paper",
			modules: [
				{
					id: "core_module",
					name: "Core Module",
					skill_name: "core-module",
					summary: "Core method module with deterministic behavior.",
					inputs: ["input"],
					outputs: ["output"],
					insight: "The module preserves the paper's central reusable method.",
					test_strategy: "Run a deterministic smoke test for the generated skill.",
					evidence: ["paper section"],
				},
			],
		};

		try {
			writeFileSync(planPath, `${JSON.stringify(plan, null, 2)}\n`, "utf8");
			const valid = runPython(validator, [planPath]);
			expect(valid.status, valid.stderr).toBe(0);

			plan.modules[0].skill_name = "core_module";
			writeFileSync(planPath, `${JSON.stringify(plan, null, 2)}\n`, "utf8");
			const invalid = runPython(validator, [planPath]);
			expect(invalid.status).toBe(2);
			expect((JSON.parse(invalid.stdout) as { errors: string[] }).errors).toContain(
				"modules[0].skill_name must be a canonical lowercase-hyphen skill id of at most 64 characters",
			);
		} finally {
			rmSync(tempRoot, { recursive: true, force: true });
		}
	});
});
