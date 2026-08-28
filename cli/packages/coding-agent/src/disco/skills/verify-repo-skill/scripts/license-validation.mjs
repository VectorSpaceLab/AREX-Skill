#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { parseDocument } from "yaml";

export const NO_LICENSE = "NO_LICENSE";

function collectSkillFiles(root, files = []) {
	const stat = fs.lstatSync(root);
	if (!stat.isDirectory() || stat.isSymbolicLink()) {
		throw new Error(`repo skill must be a real directory: ${root}`);
	}
	for (const entry of fs.readdirSync(root, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
		const entryPath = path.join(root, entry.name);
		if (entry.isSymbolicLink()) throw new Error(`repo skill contains a symbolic link: ${entryPath}`);
		if (entry.isDirectory()) collectSkillFiles(entryPath, files);
		else if (entry.isFile() && entry.name === "SKILL.md") files.push(entryPath);
	}
	return files;
}

function readFrontmatter(filePath) {
	const content = fs.readFileSync(filePath, "utf8");
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match) return { errors: ["missing YAML frontmatter"] };
	const document = parseDocument(match[1], { uniqueKeys: true });
	if (document.errors.length > 0) {
		return { errors: document.errors.map((error) => error.message) };
	}
	const frontmatter = document.toJS();
	if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) {
		return { errors: ["frontmatter must be a mapping"] };
	}
	return { frontmatter };
}

export function inspectRepoSkillLicenses(skillRoot) {
	const errors = [];
	const values = [];
	let files;
	try {
		files = collectSkillFiles(skillRoot);
	} catch (error) {
		return { valid: false, files: 0, value: null, status: "invalid", errors: [error instanceof Error ? error.message : String(error)] };
	}

	for (const filePath of files) {
		const relativePath = path.relative(skillRoot, filePath) || "SKILL.md";
		const parsed = readFrontmatter(filePath);
		if (parsed.errors) {
			for (const error of parsed.errors) errors.push(`${relativePath}: ${error}`);
			continue;
		}
		const frontmatter = parsed.frontmatter;
		if (!Object.prototype.hasOwnProperty.call(frontmatter, "license")) {
			errors.push(`${relativePath}: frontmatter must contain a top-level license`);
			continue;
		}
		const value = frontmatter.license;
		if (typeof value !== "string" || !value.trim()) {
			errors.push(`${relativePath}: license must be a non-empty string`);
			continue;
		}
		if (/\r|\n/.test(value)) {
			errors.push(`${relativePath}: license must be a single-line scalar`);
			continue;
		}
		values.push(value.trim());
	}

	const distinctValues = [...new Set(values)];
	if (distinctValues.length > 1) {
		errors.push(`repo skill tree must use one repository-level license value; found ${distinctValues.join(", ")}`);
	}
	const value = distinctValues[0] ?? null;
	return {
		valid: errors.length === 0 && files.length > 0,
		files: files.length,
		value,
		status: value === NO_LICENSE ? "unavailable" : value ? "resolved" : "invalid",
		errors,
	};
}

export function assertRepoSkillLicenses(skillRoot) {
	const report = inspectRepoSkillLicenses(skillRoot);
	if (!report.valid) {
		throw new Error(`repo skill license gate failed:\n${report.errors.map((error) => `- ${error}`).join("\n")}`);
	}
	return report;
}

function main(argv) {
	const json = argv.includes("--json");
	const root = argv.find((value) => !value.startsWith("-"));
	if (!root || argv.some((value) => value.startsWith("-") && value !== "--json")) {
		console.error("Usage: node license-validation.mjs [--json] RUNTIME_SKILL_DIR");
		return 2;
	}
	const report = inspectRepoSkillLicenses(path.resolve(root));
	if (json) console.log(JSON.stringify(report, null, 2));
	else {
		console.log(`license ${report.status}: ${report.value ?? "none"} (${report.files} SKILL.md files)`);
		for (const error of report.errors) console.error(`- ${error}`);
	}
	return report.valid ? 0 : 2;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
	process.exitCode = main(process.argv.slice(2));
}
