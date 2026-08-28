#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { inspectRepoSkillLicenses } from "./license-validation.mjs";
import { applyRepoLicense } from "./apply_repo_license.mjs";
import { resolveRepoLicense } from "./resolve_repo_license.mjs";

export function syncRepoLicense({ repository, sourceCommit, skillRoot, reportPath, env = process.env }) {
	const previous = inspectRepoSkillLicenses(skillRoot);
	const resolution = resolveRepoLicense(repository, sourceCommit, env);
	const applied = applyRepoLicense(skillRoot, resolution.value);
	const final = inspectRepoSkillLicenses(skillRoot);
	if (!final.valid) {
		throw new Error(`license sync produced an invalid runtime tree: ${final.errors.join("; ")}`);
	}
	const report = {
		schema: "disco.repo-license-resolution.v1",
		repository: resolution.repository,
		source_commit: resolution.source_commit,
		source: resolution.source,
		previous_value: previous.value,
		previous_status: previous.status,
		value: resolution.value,
		status: resolution.status,
		reason: resolution.reason ?? null,
		runtime_files_updated: applied.files,
		final_validation: {
			valid: final.valid,
			files: final.files,
			value: final.value,
		},
		warning:
			resolution.value === "NO_LICENSE"
				? "NO_LICENSE means that GitHub CLI did not provide a usable result for this source commit; it is not a legal conclusion."
			: null,
	};
	if (reportPath) {
		fs.mkdirSync(path.dirname(reportPath), { recursive: true });
		fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
	}
	return report;
}

function main(argv) {
	const valueFor = (option) => {
		const index = argv.indexOf(option);
		return index >= 0 ? argv[index + 1] : undefined;
	};
	const repository = valueFor("--repository");
	const sourceCommit = valueFor("--source-commit");
	const skillDir = valueFor("--skill-dir");
	const reportPath = valueFor("--report");
	const allowed = new Set(["--repository", "--source-commit", "--skill-dir", "--report"]);
	if (
		!repository ||
		!sourceCommit ||
		!skillDir ||
		argv.some((item, index) =>
			item.startsWith("--") &&
			(!allowed.has(item) || ((item !== "--report") && !argv[index + 1])),
		)
	) {
		console.error("Usage: node sync_repo_license.mjs --repository owner/repository --source-commit <40-hex-commit> --skill-dir RUNTIME_SKILL_DIR [--report REPORT.json]");
		return 2;
	}
	try {
		const report = syncRepoLicense({
			repository,
			sourceCommit,
			skillRoot: path.resolve(skillDir),
			reportPath: reportPath ? path.resolve(reportPath) : undefined,
		});
		console.log(JSON.stringify(report, null, 2));
		return 0;
	} catch (error) {
		console.error(`sync_repo_license.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return 2;
	}
}

if (process.argv[1] && process.argv[1].endsWith("sync_repo_license.mjs")) process.exitCode = main(process.argv.slice(2));
