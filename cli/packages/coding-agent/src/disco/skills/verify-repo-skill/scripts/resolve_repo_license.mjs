#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const NO_LICENSE = "NO_LICENSE";
const REPOSITORY = /^[^/\s]+\/[^/\s]+$/;
const COMMIT = /^[0-9a-f]{40}$/i;

function unavailable(repository, sourceCommit, reason) {
	return {
		repository: repository ?? null,
		source_commit: typeof sourceCommit === "string" ? sourceCommit.toLowerCase() : null,
		source: "GitHub CLI (gh api)",
		value: NO_LICENSE,
		status: "unavailable",
		reason,
	};
}

export function resolveRepoLicense(repository, sourceCommit, env = process.env) {
	if (!REPOSITORY.test(repository ?? "")) {
		return unavailable(repository, sourceCommit, "canonical owner/repository identity is unavailable");
	}
	if (!COMMIT.test(sourceCommit ?? "")) {
		return unavailable(repository, sourceCommit, "source commit is unavailable or is not a 40-hex revision");
	}

	const result = spawnSync(
		"gh",
		["api", `repos/${repository}/license?ref=${sourceCommit}`, "--jq", ".license.spdx_id // empty"],
		{ encoding: "utf8", env },
	);
	if (result.error?.code === "ENOENT") {
		return unavailable(repository, sourceCommit, "GitHub CLI (gh) is not installed");
	}
	if (result.error) return unavailable(repository, sourceCommit, "GitHub CLI could not be executed");
	if (result.status !== 0) {
		const stderr = String(result.stderr ?? "").toLowerCase();
		if (stderr.includes("not logged in") || stderr.includes("authentication") || stderr.includes("auth login")) {
			return unavailable(repository, sourceCommit, "GitHub CLI is not authenticated");
		}
		if (stderr.includes("404") || stderr.includes("not found")) {
			return unavailable(repository, sourceCommit, "GitHub license endpoint returned 404 or the repository/license was not found");
		}
		return unavailable(repository, sourceCommit, `GitHub license query failed with exit code ${result.status ?? 1}`);
	}

	const value = String(result.stdout ?? "").trim();
	if (!value) return unavailable(repository, sourceCommit, "GitHub returned no usable SPDX license value");
	if (/\r|\n/.test(value)) return unavailable(repository, sourceCommit, "GitHub returned a multi-line license value");
	return {
		repository,
		source_commit: sourceCommit.toLowerCase(),
		source: "GitHub CLI (gh api)",
		value,
		status: "resolved",
	};
}

function main(argv) {
	const repositoryIndex = argv.indexOf("--repository");
	const commitIndex = argv.indexOf("--source-commit");
	const repository = repositoryIndex >= 0 ? argv[repositoryIndex + 1] : undefined;
	const sourceCommit = commitIndex >= 0 ? argv[commitIndex + 1] : undefined;
	const json = argv.includes("--json");
	const reportIndex = argv.indexOf("--report");
	const reportPath = reportIndex >= 0 ? argv[reportIndex + 1] : undefined;
	const allowed = new Set(["--repository", "--source-commit", "--json", "--report"]);
	if (
		!repository ||
		!sourceCommit ||
		argv.some((value, index) =>
			value.startsWith("--") &&
			(!allowed.has(value) ||
				((value === "--repository" || value === "--source-commit" || value === "--report") && !argv[index + 1])),
		)
	) {
		console.error("Usage: node resolve_repo_license.mjs --repository owner/repository --source-commit <40-hex-commit> [--json]");
		return 2;
	}
	const report = resolveRepoLicense(repository, sourceCommit);
	if (reportPath) {
		fs.mkdirSync(path.dirname(path.resolve(reportPath)), { recursive: true });
		fs.writeFileSync(path.resolve(reportPath), `${JSON.stringify(report, null, 2)}\n`, "utf8");
	}
	if (json) console.log(JSON.stringify(report, null, 2));
	else {
		console.log(report.value);
		if (report.status === "unavailable") console.error(`license unavailable: ${report.reason}`);
	}
	return 0;
}

if (process.argv[1] && process.argv[1].endsWith("resolve_repo_license.mjs")) {
	process.exitCode = main(process.argv.slice(2));
}
