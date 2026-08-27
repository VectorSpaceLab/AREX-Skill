#!/usr/bin/env node

import { existsSync, lstatSync, readdirSync, readFileSync } from "node:fs";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { parse } from "yaml";

function collectSkillFiles(root, errors) {
	const files = [];
	for (const entry of readdirSync(root, { withFileTypes: true })) {
		if (entry.isSymbolicLink()) {
			errors.push(`${join(root, entry.name)}: symbolic links are not allowed in a portable meta skill`);
			continue;
		}
		const path = join(root, entry.name);
		if (entry.isDirectory() && entry.name === "agents") {
			errors.push(`${path}: agents directories are target-specific manifests and are not allowed in a DisCo meta skill`);
		} else if (entry.isDirectory()) files.push(...collectSkillFiles(path, errors));
		else if (entry.isFile() && entry.name === "SKILL.md") files.push(path);
	}
	return files.sort();
}

function parseSkill(filePath) {
	const content = readFileSync(filePath, "utf8");
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match?.[1]) throw new Error("missing or unterminated YAML frontmatter");
	const frontmatter = parse(match[1]);
	if (typeof frontmatter !== "object" || frontmatter === null || Array.isArray(frontmatter)) {
		throw new Error("frontmatter must be a mapping");
	}
	return { content, body: content.slice(match[0].length), frontmatter };
}

function validateLinks(root, filePath, body, errors) {
	const linkPattern = /\[[^\]]+\]\(([^)]+)\)/g;
	for (const match of body.matchAll(linkPattern)) {
		const target = match[1]?.split("#", 1)[0];
		if (!target || /^(?:https?:|mailto:)/.test(target)) continue;
		const resolvedTarget = resolve(dirname(filePath), decodeURIComponent(target));
		const relativeTarget = relative(root, resolvedTarget);
		if (relativeTarget === ".." || relativeTarget.startsWith(`..${sep}`) || isAbsolute(relativeTarget)) {
			errors.push(`${filePath}: relative link escapes the meta skill directory: ${target}`);
			continue;
		}
		if (!existsSync(resolvedTarget)) errors.push(`${filePath}: broken relative link ${target}`);
	}
}

function main() {
	const args = process.argv.slice(2);
	const json = args.includes("--json");
	const positional = args.filter((arg) => arg !== "--json");
	if (positional.length !== 1) throw new Error("Usage: validate_meta_skill.mjs <meta-skill-dir> [--json]");
	const root = resolve(positional[0]);
	if (!existsSync(root)) throw new Error(`Meta skill directory does not exist: ${root}`);
	if (lstatSync(root).isSymbolicLink() || !lstatSync(root).isDirectory()) {
		throw new Error(`Meta skill path must be a real directory, not a file or symbolic link: ${root}`);
	}

	const errors = [];
	const warnings = [];
	const files = collectSkillFiles(root, errors);
	if (files.length === 0) errors.push(`${root}: no SKILL.md files found`);

	for (const filePath of files) {
		let parsed;
		try {
			parsed = parseSkill(filePath);
		} catch (error) {
			errors.push(`${filePath}: ${error instanceof Error ? error.message : String(error)}`);
			continue;
		}
		const { frontmatter, body, content } = parsed;
		const name = frontmatter.name;
		if (typeof name !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name) || name.length > 64) {
			errors.push(`${filePath}: invalid or missing lowercase-hyphen name`);
		}
		if (typeof name === "string" && name !== basename(dirname(filePath))) {
			errors.push(`${filePath}: frontmatter name must match its directory basename`);
		}
		if (typeof frontmatter.description !== "string" || frontmatter.description.trim().length < 20) {
			errors.push(`${filePath}: description must be a specific triggering description`);
		}
		const metadata = frontmatter.metadata;
		const role =
			typeof metadata === "object" && metadata !== null && !Array.isArray(metadata)
				? metadata["disco-role"]
				: undefined;
		if (role !== "meta") errors.push(`${filePath}: metadata.disco-role must be meta`);
		if (/\/root\/github-repos\/Auto-ML-Skills|(?:conda|venv)[-_ ]?(?:prefix|path):\s*\//i.test(content)) {
			errors.push(`${filePath}: contains a construction-machine source or environment path`);
		}
		if (/\b(?:TODO|TBD)\b/.test(content)) errors.push(`${filePath}: contains TODO/TBD`);
		validateLinks(root, filePath, body, errors);
	}

	const rootSkill = files.find((file) => dirname(file) === root);
	if (!rootSkill) {
		errors.push(`${root}: root SKILL.md is required`);
	} else {
		const body = parseSkill(rootSkill).body;
		const lowerBody = body.toLowerCase();
		for (const required of ["source", "operating", "verification", "failure", "approval", "handoff"]) {
			if (!lowerBody.includes(required)) {
				warnings.push(`${relative(root, rootSkill) || "SKILL.md"}: contract does not mention ${required}`);
			}
		}
		if (!body.includes("metadata.disco-role: operating")) {
			errors.push(`${rootSkill}: must require generated operating skills to declare their role`);
		}
		for (const [required, description] of [
			["reusability", "a generated operating-graph reusability assessment"],
			["project", "project deployment scope"],
			["managed", "managed deployment scope"],
			["approval", "operating-graph import approval"],
			["handoff", "a Researcher handoff after operating import"],
			["overwrite", "separate overwrite handling"],
		]) {
			if (!lowerBody.includes(required)) errors.push(`${rootSkill}: must define ${description}`);
		}
		if (!body.includes(".agents/skills")) {
			errors.push(`${rootSkill}: must define the project operating-skill target under .agents/skills`);
		}
		if (!body.includes("~/.disco/agent/skills")) {
			errors.push(`${rootSkill}: must define the managed operating-skill target under ~/.disco/agent/skills`);
		}
	}

	const result = { valid: errors.length === 0, root, files: files.length, errors, warnings };
	if (json) console.log(JSON.stringify(result, null, 2));
	else {
		for (const warning of warnings) console.warn(`warning: ${warning}`);
		for (const error of errors) console.error(`error: ${error}`);
		console.log(result.valid ? `Valid meta skill (${files.length} SKILL.md file(s))` : "Meta skill validation failed");
	}
	if (!result.valid) process.exitCode = 1;
}

try {
	main();
} catch (error) {
	console.error(error instanceof Error ? error.message : String(error));
	process.exitCode = 1;
}
