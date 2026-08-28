import { chmod, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { applyRepoLicense } from "./skills/verify-repo-skill/scripts/apply_repo_license.mjs";
import { inspectRepoSkillLicenses } from "./skills/verify-repo-skill/scripts/license-validation.mjs";
import { resolveRepoLicense } from "./skills/verify-repo-skill/scripts/resolve_repo_license.mjs";
import { syncRepoLicense } from "./skills/verify-repo-skill/scripts/sync_repo_license.mjs";

const cleanup: string[] = [];
const sourceCommit = "a".repeat(40);

async function writeSkillTree(root: string, rootFrontmatter: string, childFrontmatter: string): Promise<void> {
	await mkdir(path.join(root, "sub-skills", "setup"), { recursive: true });
	await writeFile(path.join(root, "SKILL.md"), `---\n${rootFrontmatter}\n---\n\n# Root\n`, "utf8");
	await writeFile(
		path.join(root, "sub-skills", "setup", "SKILL.md"),
		`---\n${childFrontmatter}\n---\n\n# Setup\n`,
		"utf8",
	);
}

async function fakeGh(root: string, output: string, exitCode = 0, stderr = ""): Promise<Record<string, string>> {
	const bin = path.join(root, "bin");
	await mkdir(bin, { recursive: true });
	const script = path.join(bin, "gh");
	await writeFile(
		script,
		[
			"#!/bin/sh",
			`printf '%b' ${JSON.stringify(output)}`,
			stderr ? `printf '%b' ${JSON.stringify(stderr)} >&2` : "",
			`exit ${exitCode}`,
			"",
		].filter(Boolean).join("\n"),
		"utf8",
	);
	await chmod(script, 0o755);
	return { ...process.env, PATH: `${bin}:${process.env.PATH ?? ""}` };
}

describe("repo skill license contract", () => {
	afterEach(async () => {
		for (const root of cleanup.splice(0)) await rm(root, { recursive: true, force: true });
	});

	it("resolves a usable GitHub SPDX value against the exact source commit", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-gh-"));
		cleanup.push(root);
		const env = await fakeGh(root, "MIT\n");
		const report = resolveRepoLicense("owner/repository", sourceCommit, env);

		expect(report).toMatchObject({
			repository: "owner/repository",
			source_commit: sourceCommit,
			value: "MIT",
			status: "resolved",
		});
	});

	it("preserves GitHub NOASSERTION as an accepted source license value", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-gh-"));
		cleanup.push(root);
		const env = await fakeGh(root, "NOASSERTION\n");
		const report = resolveRepoLicense("owner/repository", sourceCommit, env);

		expect(report).toMatchObject({ value: "NOASSERTION", status: "resolved" });
		expect(report.reason).toBeUndefined();
	});

	it("normalizes an empty GitHub value to NO_LICENSE", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-gh-"));
		cleanup.push(root);
		const env = await fakeGh(root, "");
		const report = resolveRepoLicense("owner/repository", sourceCommit, env);

		expect(report.value).toBe("NO_LICENSE");
		expect(report.status).toBe("unavailable");
		expect(report.reason).toBe("GitHub returned no usable SPDX license value");
	});

	it.each([
		["authentication failed", "GitHub CLI is not authenticated"],
		["HTTP 404: not found", "GitHub license endpoint returned 404 or the repository/license was not found"],
		["request failed", "GitHub license query failed with exit code 1"],
	])("normalizes GitHub CLI failures to NO_LICENSE: %j", async (stderr, reason) => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-gh-"));
		cleanup.push(root);
		const env = await fakeGh(root, "", 1, stderr);
		const report = resolveRepoLicense("owner/repository", sourceCommit, env);

		expect(report.value).toBe("NO_LICENSE");
		expect(report.status).toBe("unavailable");
		expect(report.reason).toBe(reason);
	});

	it("reports an unavailable result when gh is not installed", () => {
		const report = resolveRepoLicense("owner/repository", sourceCommit, { ...process.env, PATH: "" });

		expect(report.value).toBe("NO_LICENSE");
		expect(report.reason).toBe("GitHub CLI (gh) is not installed");
	});

	it("rejects an invalid repository identity or source commit without invoking gh", () => {
		expect(resolveRepoLicense("owner", sourceCommit).reason).toBe("canonical owner/repository identity is unavailable");
		expect(resolveRepoLicense("owner/repository", "short").reason).toBe("source commit is unavailable or is not a 40-hex revision");
	});

	it("recursively applies one license value to the root and every sub-skill", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-tree-"));
		cleanup.push(root);
		await writeSkillTree(
			root,
			'name: example\ndescription: "Root skill."',
			'name: setup\ndescription: "Setup skill."',
		);

		const applied = applyRepoLicense(root, "MIT");
		const report = inspectRepoSkillLicenses(root);

		expect(applied).toEqual({ files: 2, value: "MIT" });
		expect(report).toMatchObject({ valid: true, files: 2, value: "MIT", status: "resolved" });
		expect(await readFile(path.join(root, "SKILL.md"), "utf8")).toContain("license: MIT");
		expect(await readFile(path.join(root, "sub-skills", "setup", "SKILL.md"), "utf8")).toContain("license: MIT");
	});

	it("accepts NO_LICENSE as a valid, reportable tree value", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-tree-"));
		cleanup.push(root);
		await writeSkillTree(
			root,
			'name: example\ndescription: "Root skill."\nlicense: NO_LICENSE',
			'name: setup\ndescription: "Setup skill."\nlicense: NO_LICENSE',
		);

		expect(inspectRepoSkillLicenses(root)).toMatchObject({ valid: true, value: "NO_LICENSE", status: "unavailable" });
	});

	it("allows the injector to write NOASSERTION", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-tree-"));
		cleanup.push(root);
		await writeSkillTree(
			root,
			'name: example\ndescription: "Root skill."',
			'name: setup\ndescription: "Setup skill."',
		);

		expect(applyRepoLicense(root, "NOASSERTION")).toEqual({ files: 2, value: "NOASSERTION" });
		expect(inspectRepoSkillLicenses(root)).toMatchObject({ valid: true, value: "NOASSERTION", status: "resolved" });
	});

	it.each([
		[
			'name: example\ndescription: "Root skill."',
			'name: setup\ndescription: "Setup skill."\nlicense: MIT',
			"frontmatter must contain a top-level license",
		],
		[
			'name: example\ndescription: "Root skill."\nlicense: ""',
			'name: setup\ndescription: "Setup skill."\nlicense: MIT',
			"license must be a non-empty string",
		],
		[
			'name: example\ndescription: "Root skill."\nlicense: MIT\nlicense: Apache-2.0',
			'name: setup\ndescription: "Setup skill."\nlicense: MIT',
			"Map keys must be unique",
		],
		[
			'name: example\ndescription: "Root skill."\nlicense: MIT',
			'name: setup\ndescription: "Setup skill."\nlicense: Apache-2.0',
			"one repository-level license value",
		],
	])("rejects an invalid license tree: %s", async (rootFrontmatter, childFrontmatter, expected) => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-tree-"));
		cleanup.push(root);
		await writeSkillTree(root, rootFrontmatter, childFrontmatter);

		const report = inspectRepoSkillLicenses(root);
		expect(report.valid).toBe(false);
		expect(report.errors.join("\n")).toContain(expected);
	});

	it("syncs the tree and writes a complete resolution report", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-license-sync-"));
		cleanup.push(root);
		const env = await fakeGh(root, "Apache-2.0\n");
		await writeSkillTree(
			root,
			'name: example\ndescription: "Root skill."\nlicense: MIT',
			'name: setup\ndescription: "Setup skill."\nlicense: MIT',
		);

		const report = syncRepoLicense({
			repository: "owner/repository",
			sourceCommit,
			skillRoot: root,
			env,
		});

		expect(report).toMatchObject({
			repository: "owner/repository",
			source_commit: sourceCommit,
			previous_value: "MIT",
			value: "Apache-2.0",
			status: "resolved",
			runtime_files_updated: 2,
			final_validation: { valid: true, files: 2, value: "Apache-2.0" },
		});
		expect(report.warning).toBeNull();
	});
});
