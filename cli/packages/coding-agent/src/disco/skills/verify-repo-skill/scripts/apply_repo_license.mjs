#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { parseDocument } from "yaml";

function normalizeLicenseValue(value) {
	if (typeof value !== "string" || !value.trim() || /\r|\n/.test(value)) {
		throw new Error("license must be a non-empty single-line string");
	}
	return value.trim();
}

function collectSkillFiles(root, files = []) {
	const stat = fs.lstatSync(root);
	if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`repo skill must be a real directory: ${root}`);
	for (const entry of fs.readdirSync(root, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
		const entryPath = path.join(root, entry.name);
		if (entry.isSymbolicLink()) throw new Error(`repo skill contains a symbolic link: ${entryPath}`);
		if (entry.isDirectory()) collectSkillFiles(entryPath, files);
		else if (entry.isFile() && entry.name === "SKILL.md") files.push(entryPath);
	}
	return files;
}

function applyToFile(filePath, value) {
	const content = fs.readFileSync(filePath, "utf8");
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match) throw new Error(`${filePath} is missing YAML frontmatter`);
	const document = parseDocument(match[1], { uniqueKeys: true });
	if (document.errors.length > 0) throw new Error(`${filePath} has invalid YAML frontmatter: ${document.errors[0].message}`);
	const frontmatter = document.toJS();
	if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) throw new Error(`${filePath} frontmatter must be a mapping`);
	document.set("license", value);
	fs.writeFileSync(filePath, `---\n${document.toString()}---\n${content.slice(match[0].length)}`, "utf8");
}

export function applyRepoLicense(skillRoot, value) {
	value = normalizeLicenseValue(value);
	const files = collectSkillFiles(skillRoot);
	// Parse every file before writing so one malformed child cannot leave a
	// partially updated staged tree.
	for (const filePath of files) {
		const content = fs.readFileSync(filePath, "utf8");
		const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
		if (!match) throw new Error(`${filePath} is missing YAML frontmatter`);
		const document = parseDocument(match[1], { uniqueKeys: true });
		if (document.errors.length > 0) throw new Error(`${filePath} has invalid YAML frontmatter: ${document.errors[0].message}`);
		const frontmatter = document.toJS();
		if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) throw new Error(`${filePath} frontmatter must be a mapping`);
	}
	for (const filePath of files) applyToFile(filePath, value);
	return { files: files.length, value };
}

function main(argv) {
	const rootIndex = argv.indexOf("--skill-dir");
	const licenseIndex = argv.indexOf("--license");
	const resolutionReportIndex = argv.indexOf("--resolution-report");
	const reportIndex = argv.indexOf("--report");
	const root = rootIndex >= 0 ? argv[rootIndex + 1] : undefined;
	const resolutionReport = resolutionReportIndex >= 0 ? argv[resolutionReportIndex + 1] : undefined;
	const reportPath = reportIndex >= 0 ? argv[reportIndex + 1] : undefined;
	let value = licenseIndex >= 0 ? argv[licenseIndex + 1] : undefined;
	if (!value && resolutionReport) {
		try {
			const resolution = JSON.parse(fs.readFileSync(path.resolve(resolutionReport), "utf8"));
			value = resolution.value;
		} catch (error) {
			console.error(`apply_repo_license.mjs: cannot read resolution report: ${error instanceof Error ? error.message : String(error)}`);
			return 2;
		}
	}
	const allowed = new Set(["--skill-dir", "--license", "--resolution-report", "--report"]);
	if (!root || !value || argv.some((item, index) => item.startsWith("--") && (!allowed.has(item) || ((item !== "--report") && !argv[index + 1])))) {
		console.error("Usage: node apply_repo_license.mjs --skill-dir RUNTIME_SKILL_DIR (--license LICENSE_VALUE | --resolution-report REPORT.json) [--report REPORT.json]");
		return 2;
	}
	try {
		const report = applyRepoLicense(path.resolve(root), value);
		if (reportPath) {
			const absoluteReportPath = path.resolve(reportPath);
			const existing = fs.existsSync(absoluteReportPath)
				? JSON.parse(fs.readFileSync(absoluteReportPath, "utf8"))
				: {};
			fs.mkdirSync(path.dirname(absoluteReportPath), { recursive: true });
			fs.writeFileSync(absoluteReportPath, `${JSON.stringify({ ...existing, runtime_files_updated: report.files, applied_value: report.value }, null, 2)}\n`, "utf8");
		}
		console.log(JSON.stringify(report, null, 2));
		return 0;
	} catch (error) {
		console.error(`apply_repo_license.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return 2;
	}
}

if (process.argv[1] && process.argv[1].endsWith("apply_repo_license.mjs")) process.exitCode = main(process.argv.slice(2));
