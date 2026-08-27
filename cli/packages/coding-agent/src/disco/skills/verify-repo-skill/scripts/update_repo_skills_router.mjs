#!/usr/bin/env node

/**
 * Build the fixed area -> family repository-skills router.
 *
 * The taxonomy and the v2 per-skill routing fragments are authoritative. The
 * Markdown files in repo-skills-router are deterministic views of those data
 * files; they are never edited by hand as part of an import.
 */

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import { createHash } from "node:crypto";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const DEFAULT_TIMEOUT_SECONDS = 900;
const ROUTER_ID = "repo-skills-router";
const ROUTING_METADATA = path.join("references", "repo-routing-metadata.json");
const TAXONOMY_PATH = path.join("references", "index", "taxonomy.json");
const REPOSITORIES_PATH = path.join("references", "index", "repositories.jsonl");
const ASSIGNMENTS_PATH = path.join("references", "index", "assignments.jsonl");
const BUILD_METADATA_PATH = path.join("references", "index", "build-metadata.json");
const REPOSITORY_INDEX_PATH = "repository-index.jsonl";
const CANONICAL_SKILL_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const REPO_ID = /^[^/\s]+\/[^/\s]+$/;
const TAXONOMY_SHA256 = "f8c306386015711634ddbb43a5eb95d1f58909c3513ce2063ba42efdd583a431";
const REPOSITORY_INDEX_FIELDS = new Set([
	"schema_version", "repo_id", "legacy_repo_id", "repo_name", "skill_id", "source_url",
	"source_commit", "source_skill_root", "target_skill_root", "aliases", "content_sha256", "description",
]);
const ASSIGNMENT_INDEX_FIELDS = new Set(["repo_id", "legacy_repo_id", "skill_id", "area", "family", "confidence"]);
const ROUTER_DESCRIPTION = "Routes substantive ML, AI, data, scientific-computing, and software-engineering requests to the smallest useful set of managed repository skills. Invoke proactively when a request names or implies a package, framework, model family, dataset, modality, workflow, backend, deployment target, evaluation method, or implementation approach that may benefit from repository guidance, even if no repository is named. Narrow progressively from area to family to repository root: inspect only the one or two most likely area pages; compare candidates by capability, task surface, model/data format, training versus inference versus evaluation intent, runtime constraints, and root-skill description; then open only the selected root and relevant sub-skills, references, or scripts. Select multiple repositories only when each adds a distinct capability. Do not load the whole collection, treat dependencies or incidental integrations as capabilities, choose by name alone, or force a match when no exact taxonomy family applies.";
const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SCRIPT_DIR = path.dirname(SCRIPT_PATH);

class RouterError extends Error {
	constructor(message) {
		super(message);
		this.name = "RouterError";
	}
}

function defaultAgentDir() {
	return process.env.DISCO_CODING_AGENT_DIR || path.join(os.homedir(), ".disco", "agent");
}

function bundledRouterTemplateDir() {
	return path.resolve(SCRIPT_DIR, "../../repo-skills-router");
}

function withImportLockScript() {
	return path.join(SCRIPT_DIR, "with_import_lock.mjs");
}

function expandHome(value) {
	return value.replace(/^~(?=$|[\\/])/, os.homedir());
}

function isWithin(root, candidate) {
	const relative = path.relative(root, candidate);
	return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function isRelativePath(value) {
	if (typeof value !== "string" || !value.trim() || value.includes("\0") || path.isAbsolute(value)) return false;
	const normalized = value.replaceAll("\\", "/");
	return normalized !== "." && normalized !== ".." && !normalized.startsWith("../");
}

function exists(filePath) {
	try {
		fs.lstatSync(filePath);
		return true;
	} catch (error) {
		if (error?.code === "ENOENT") return false;
		throw error;
	}
}

function isRegularFile(filePath) {
	if (!exists(filePath)) return false;
	const stat = fs.lstatSync(filePath);
	return stat.isFile() && !stat.isSymbolicLink();
}

function isDirectory(filePath) {
	if (!exists(filePath)) return false;
	const stat = fs.lstatSync(filePath);
	return stat.isDirectory() && !stat.isSymbolicLink();
}

function validateEvidenceFile(sourceCheckout, evidencePath, lineStart, lineEnd, label) {
	const resolvedPath = path.resolve(sourceCheckout, evidencePath);
	if (!isWithin(sourceCheckout, resolvedPath) || !exists(resolvedPath)) {
		throw new RouterError(`${label} path does not exist in source checkout: ${evidencePath}`);
	}
	if (!isRegularFile(resolvedPath)) {
		throw new RouterError(`${label} path must be a regular file in source checkout: ${evidencePath}`);
	}
	if (lineStart === undefined && lineEnd === undefined) return;
	const content = readText(resolvedPath);
	const lineCount = content.length === 0 ? 0 : content.split(/\r?\n/).length - (content.endsWith("\n") ? 1 : 0);
	const highestLine = lineEnd ?? lineStart;
	if (highestLine > lineCount) {
		throw new RouterError(`${label} line range exceeds ${evidencePath} (${lineCount} lines)`);
	}
}

function readText(filePath) {
	return fs.readFileSync(filePath, "utf8");
}

function writeText(filePath, value) {
	fs.mkdirSync(path.dirname(filePath), { recursive: true });
	fs.writeFileSync(filePath, value, "utf8");
}

function stableJson(value) {
	return `${JSON.stringify(value, null, 2)}\n`;
}

function stableJsonValue(value) {
	if (Array.isArray(value)) return value.map(stableJsonValue);
	if (!value || typeof value !== "object") return value;
	return Object.fromEntries(Object.entries(value).sort(([left], [right]) => left.localeCompare(right)).map(([key, item]) => [key, stableJsonValue(item)]));
}

function loadJson(filePath) {
	try {
		return JSON.parse(readText(filePath));
	} catch (error) {
		throw new RouterError(`${filePath} is invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
	}
}

function readJsonLines(filePath) {
	if (!isRegularFile(filePath)) return [];
	return readText(filePath).split(/\r?\n/).filter(Boolean).map((line, index) => {
		try {
			return JSON.parse(line);
		} catch (error) {
			throw new RouterError(`${filePath}:${index + 1} is invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
		}
	});
}

function writeJsonLines(filePath, records) {
	writeText(filePath, records.map((record) => JSON.stringify(record)).join("\n") + (records.length ? "\n" : ""));
}

function normalizeGithubUrl(value) {
	if (typeof value !== "string") return undefined;
	const trimmed = value.trim().replace(/\.git\/?$/, "").replace(/\/$/, "");
	return /^https:\/\/github\.com\/[^/\s]+\/[^/\s]+$/i.test(trimmed) ? trimmed : undefined;
}

function normalizeDigest(value) {
	if (typeof value !== "string") return undefined;
	const trimmed = value.trim();
	if (/^sha256:[0-9a-f]{64}$/i.test(trimmed)) return trimmed.toLowerCase();
	if (/^[0-9a-f]{64}$/i.test(trimmed)) return `sha256:${trimmed.toLowerCase()}`;
	return undefined;
}

function treeDigest(root) {
	const hash = createHash("sha256");
	const files = [];
	const visit = (directory) => {
		for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
			const entryPath = path.join(directory, entry.name);
			if (entry.isSymbolicLink()) throw new RouterError(`repository skill contains a symbolic link: ${entryPath}`);
			if (entry.isDirectory()) visit(entryPath);
			else if (entry.isFile()) files.push(entryPath);
			else throw new RouterError(`repository skill contains a non-regular file: ${entryPath}`);
		}
	};
	visit(root);
	for (const filePath of files) {
		const relativePath = path.relative(root, filePath).split(path.sep).join("/");
		const content = fs.readFileSync(filePath);
		hash.update(`file\0${relativePath}\0${content.byteLength}\0`);
		hash.update(content);
		hash.update("\0");
	}
	return `sha256:${hash.digest("hex")}`;
}

function readProvenance(skillDir) {
	const provenanceFile = path.join(skillDir, "references", "repo-provenance.md");
	if (!isRegularFile(provenanceFile)) return undefined;
	const match = readText(provenanceFile).match(/```json\r?\n([\s\S]*?)\r?\n```/);
	if (!match) return undefined;
	try {
		const value = JSON.parse(match[1]);
		return value && typeof value === "object" ? value : undefined;
	} catch {
		return undefined;
	}
}

function parseFrontmatter(skillFile) {
	const content = readText(skillFile);
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match?.[1]) throw new RouterError(`${skillFile} is missing YAML frontmatter`);
	let frontmatter;
	try {
		frontmatter = parse(match[1]);
	} catch (error) {
		throw new RouterError(`${skillFile} has invalid YAML frontmatter: ${error instanceof Error ? error.message : String(error)}`);
	}
	if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) {
		throw new RouterError(`${skillFile} frontmatter must be a mapping`);
	}
	return frontmatter;
}

function markdownEscape(value) {
	return String(value).replaceAll("|", "\\|").replaceAll("\n", " ").trim();
}

function slug(value) {
	return String(value).normalize("NFKD").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "item";
}

function titleCase(value) {
	return String(value).replace(/[-_]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function frontmatterDescription(skillFile) {
	const frontmatter = parseFrontmatter(skillFile);
	if (typeof frontmatter.name !== "string" || !CANONICAL_SKILL_ID.test(frontmatter.name)) {
		throw new RouterError(`${skillFile} must declare a canonical lowercase-hyphen name`);
	}
	if (typeof frontmatter.description !== "string" || !frontmatter.description.trim()) {
		throw new RouterError(`${skillFile} must declare a non-empty description`);
	}
	return { id: frontmatter.name, description: frontmatter.description.trim(), frontmatter };
}

function normalizeTaxonomy(raw, sourcePath) {
	if (!raw || typeof raw !== "object" || Array.isArray(raw) || !Array.isArray(raw.areas)) {
		throw new RouterError(`${sourcePath} must contain an areas array`);
	}
	const areas = raw.areas.map((area, areaIndex) => {
		if (!area || typeof area !== "object" || typeof area.name !== "string" || typeof area.scope !== "string" || !Array.isArray(area.families)) {
			throw new RouterError(`${sourcePath}: area ${areaIndex} is invalid`);
		}
		const families = area.families.map((family, familyIndex) => {
			if (!family || typeof family !== "object" || typeof family.name !== "string" || typeof family.scope !== "string") {
				throw new RouterError(`${sourcePath}: family ${area.name}/${familyIndex} is invalid`);
			}
			if (family.id !== undefined && (typeof family.id !== "string" || !family.id.trim())) {
				throw new RouterError(`${sourcePath}: family ${area.name}/${familyIndex} has an invalid id`);
			}
			return family;
		});
		if (area.id !== undefined && (typeof area.id !== "string" || !area.id.trim())) {
			throw new RouterError(`${sourcePath}: area ${areaIndex} has an invalid id`);
		}
		area.families = families;
		return area;
	});
	const seen = new Set();
	for (const area of areas) {
		for (const family of area.families) {
			const key = `${area.name}\0${family.name}`;
			if (seen.has(key)) throw new RouterError(`taxonomy contains duplicate family ${area.name} -> ${family.name}`);
			seen.add(key);
		}
	}
	const taxonomy = raw;
	Object.defineProperty(taxonomy, "areas", { value: areas, enumerable: true, writable: false, configurable: false });
	return taxonomy;
}

function resolveTaxonomy(routerDir, templateDir) {
	const candidates = [
		process.env.DISCO_ROUTER_TAXONOMY_FILE ? path.resolve(expandHome(process.env.DISCO_ROUTER_TAXONOMY_FILE)) : undefined,
		path.join(templateDir, TAXONOMY_PATH),
		path.join(routerDir, TAXONOMY_PATH),
	];
	const mismatches = [];
	for (const candidate of candidates) {
		if (!candidate || !isRegularFile(candidate)) continue;
		const bytes = fs.readFileSync(candidate);
		const digest = createHash("sha256").update(bytes).digest("hex");
		if (digest !== TAXONOMY_SHA256 && process.env.DISCO_ROUTER_ALLOW_NONCANONICAL_TAXONOMY_FOR_TESTS !== "1") {
			mismatches.push(`${candidate} has sha256 ${digest}`);
			if (candidate === candidates[0]) throw new RouterError(`${candidate} does not match the canonical taxonomy hash ${TAXONOMY_SHA256}`);
			continue;
		}
		let value;
		try {
			value = JSON.parse(bytes.toString("utf8"));
		} catch (error) {
			throw new RouterError(`${candidate} is invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
		}
		return { taxonomy: normalizeTaxonomy(value, candidate), taxonomySha256: digest };
	}
	throw new RouterError(`could not find a canonical ${TAXONOMY_PATH}; ${mismatches.join("; ") || "no taxonomy file was found"}`);
}

function validateRoutingMetadata(metadataFile, skillId, taxonomy, taxonomySha256, expectedRepoId) {
	if (!isRegularFile(metadataFile)) throw new RouterError(`runtime repo skill is missing ${metadataFile}`);
	const data = loadJson(metadataFile);
	if (!data || typeof data !== "object" || Array.isArray(data)) throw new RouterError(`${metadataFile} must be a JSON object`);
	const allowed = new Set(["schema_version", "repo_id", "skill_id", "taxonomy_sha256", "routing_status", "assignments", "unclassified_reason"]);
	for (const key of Object.keys(data)) if (!allowed.has(key)) throw new RouterError(`${metadataFile} contains unknown field ${key}`);
	if (data.schema_version !== "2.0") throw new RouterError(`${metadataFile} must use schema_version \"2.0\"`);
	if (typeof data.repo_id !== "string" || !REPO_ID.test(data.repo_id)) throw new RouterError(`${metadataFile}.repo_id must use owner/repository form`);
	if (expectedRepoId && data.repo_id !== expectedRepoId) throw new RouterError(`${metadataFile}.repo_id does not match the repository index`);
	if (data.skill_id !== skillId) throw new RouterError(`${metadataFile}.skill_id must equal ${skillId}`);
	if (data.taxonomy_sha256 !== taxonomySha256) throw new RouterError(`${metadataFile}.taxonomy_sha256 must equal the current taxonomy hash`);
	if (!new Set(["classified", "unclassified"]).has(data.routing_status)) throw new RouterError(`${metadataFile}.routing_status must be classified or unclassified`);
	if (!Array.isArray(data.assignments)) throw new RouterError(`${metadataFile}.assignments must be an array`);
	const exact = new Set(taxonomy.areas.flatMap((area) => area.families.map((family) => `${area.name}\0${family.name}`)));
	const assignments = [];
	const seen = new Set();
	for (const [index, assignment] of data.assignments.entries()) {
		if (!assignment || typeof assignment !== "object" || Array.isArray(assignment)) throw new RouterError(`${metadataFile}.assignments[${index}] must be an object`);
		const keys = Object.keys(assignment);
		if (keys.some((key) => !["area", "family"].includes(key))) throw new RouterError(`${metadataFile}.assignments[${index}] contains unknown fields`);
		if (typeof assignment.area !== "string" || typeof assignment.family !== "string") throw new RouterError(`${metadataFile}.assignments[${index}] requires area and family strings`);
		const key = `${assignment.area}\0${assignment.family}`;
		if (!exact.has(key)) throw new RouterError(`${metadataFile} references an unknown taxonomy path: ${assignment.area} -> ${assignment.family}`);
		if (seen.has(key)) throw new RouterError(`${metadataFile} contains duplicate assignment ${assignment.area} -> ${assignment.family}`);
		seen.add(key);
		assignments.push({ area: assignment.area, family: assignment.family });
	}
	if (data.routing_status === "classified" && assignments.length === 0) throw new RouterError(`${metadataFile} classified status requires assignments`);
	if (data.routing_status === "unclassified" && (assignments.length !== 0 || typeof data.unclassified_reason !== "string" || !data.unclassified_reason.trim())) {
		throw new RouterError(`${metadataFile} unclassified status requires no assignments and a reason`);
	}
	return { repoId: data.repo_id, skillId, assignments, routingStatus: data.routing_status, unclassifiedReason: data.unclassified_reason };
}

function readLiveSkills(repoSkillsRoot, includeSkillIds, taxonomy, taxonomySha256, managedSkillIds) {
	if (!isDirectory(repoSkillsRoot)) throw new RouterError(`repo-skills collection does not exist: ${repoSkillsRoot}`);
	const all = [];
	for (const entry of fs.readdirSync(repoSkillsRoot, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
		if (!entry.isDirectory() || entry.isSymbolicLink()) continue;
		const skillDir = path.join(repoSkillsRoot, entry.name);
		const skillFile = path.join(skillDir, "SKILL.md");
		if (!isRegularFile(skillFile)) continue;
		const { id, description, frontmatter } = frontmatterDescription(skillFile);
		if (id !== entry.name) throw new RouterError(`${skillFile} name must match directory basename ${entry.name}`);
		if (id === ROUTER_ID || id === "repo-skills") continue;
		const metadataPath = path.join(skillDir, ROUTING_METADATA);
		if (!isRegularFile(metadataPath)) {
			if (includeSkillIds.includes(id) || !managedSkillIds || managedSkillIds.has(id)) {
				throw new RouterError(`managed repo skill is missing ${metadataPath}`);
			}
			continue;
		}
		const metadata = validateRoutingMetadata(metadataPath, id, taxonomy, taxonomySha256);
		all.push({ id, dir: skillDir, description, frontmatter, metadata });
	}
	const selected = includeSkillIds.length ? all.filter((skill) => includeSkillIds.includes(skill.id)) : all;
	const missing = includeSkillIds.filter((id) => !all.some((skill) => skill.id === id));
	if (missing.length) throw new RouterError(`--include-skill references missing skill ids: ${missing.join(", ")}`);
	if (!selected.length) throw new RouterError("no routable repo skills with v2 metadata were found");
	return selected;
}

function readExistingRecords(repoSkillsRoot, routerDir, templateDir) {
	const candidates = [
		path.join(repoSkillsRoot, REPOSITORY_INDEX_PATH),
		path.join(routerDir, REPOSITORIES_PATH),
		path.join(templateDir, REPOSITORIES_PATH),
	];
	const rows = [];
	for (const candidate of candidates) {
		for (const row of readJsonLines(candidate)) rows.push(row);
		if (rows.length) break;
	}
	return rows;
}

function readExistingAssignmentRecords(routerDir, templateDir) {
	for (const candidate of [path.join(routerDir, ASSIGNMENTS_PATH), path.join(templateDir, ASSIGNMENTS_PATH)]) {
		const rows = readJsonLines(candidate);
		if (rows.length) return rows;
	}
	return [];
}

function validateRoutingEntry(value, sourcePath, taxonomy, taxonomySha256) {
	if (!value || typeof value !== "object" || Array.isArray(value)) throw new RouterError(`${sourcePath} must contain a JSON object`);
	const allowed = new Set([
		"schema_version", "legacy_repo_id", "repo_id", "repo_name", "source_url", "source_commit",
		"source_checkout", "source_skill_root", "skill_id", "skill_root", "skill_content_sha256",
		"taxonomy_sha256", "status", "assignments", "unclassified_reason",
	]);
	for (const key of Object.keys(value)) if (!allowed.has(key)) throw new RouterError(`${sourcePath} contains unknown field ${key}`);
	if (value.schema_version !== 1) throw new RouterError(`${sourcePath}.schema_version must be 1`);
	if (typeof value.repo_id !== "string" || !REPO_ID.test(value.repo_id)) throw new RouterError(`${sourcePath}.repo_id must use owner/repository form`);
	if (typeof value.repo_name !== "string" || value.repo_name !== value.repo_id.split("/").at(-1)) throw new RouterError(`${sourcePath}.repo_name does not match repo_id`);
	if (typeof value.source_url !== "string" || !normalizeGithubUrl(value.source_url)) throw new RouterError(`${sourcePath}.source_url must be a GitHub repository URL`);
	if (typeof value.source_commit !== "string" || !/^[0-9a-f]{40}$/i.test(value.source_commit)) throw new RouterError(`${sourcePath}.source_commit must be a 40-hex commit`);
	if (value.legacy_repo_id !== undefined && (typeof value.legacy_repo_id !== "string" || !value.legacy_repo_id.trim())) throw new RouterError(`${sourcePath}.legacy_repo_id must be a non-empty string when provided`);
	if (typeof value.source_checkout !== "string" || !path.isAbsolute(value.source_checkout) || !isDirectory(value.source_checkout)) throw new RouterError(`${sourcePath}.source_checkout must be an existing absolute directory`);
	if (typeof value.skill_id !== "string" || !CANONICAL_SKILL_ID.test(value.skill_id)) throw new RouterError(`${sourcePath}.skill_id must use a canonical skill id`);
	if (!isRelativePath(value.skill_root)) throw new RouterError(`${sourcePath}.skill_root must be a relative path`);
	if (value.source_skill_root !== undefined && !isRelativePath(value.source_skill_root)) throw new RouterError(`${sourcePath}.source_skill_root must be a relative path`);
	if (typeof value.skill_content_sha256 !== "string" || !/^sha256:[0-9a-f]{64}$/i.test(value.skill_content_sha256)) {
		throw new RouterError(`${sourcePath}.skill_content_sha256 must be sha256:<64 hex characters>`);
	}
	if (value.taxonomy_sha256 !== taxonomySha256) throw new RouterError(`${sourcePath}.taxonomy_sha256 does not match the current taxonomy`);
	if (!new Set(["classified", "unclassified"]).has(value.status)) throw new RouterError(`${sourcePath}.status must be classified or unclassified`);
	if (!Array.isArray(value.assignments)) throw new RouterError(`${sourcePath}.assignments must be an array`);
	const exact = new Set(taxonomy.areas.flatMap((area) => area.families.map((family) => `${area.name}\0${family.name}`)));
	const seen = new Set();
	for (const [index, assignment] of value.assignments.entries()) {
		if (!assignment || typeof assignment !== "object" || Array.isArray(assignment)) throw new RouterError(`${sourcePath}.assignments[${index}] must be an object`);
		const allowedAssignmentFields = new Set(["area", "family", "confidence", "rationale", "evidence", "repo_skill_paths"]);
		if (Object.keys(assignment).some((key) => !allowedAssignmentFields.has(key))) throw new RouterError(`${sourcePath}.assignments[${index}] contains an unknown field`);
		if (typeof assignment.area !== "string" || typeof assignment.family !== "string" || !exact.has(`${assignment.area}\0${assignment.family}`)) {
			throw new RouterError(`${sourcePath}.assignments[${index}] contains an invalid taxonomy assignment`);
		}
		if (!new Set(["high", "medium", "low"]).has(assignment.confidence)) {
			throw new RouterError(`${sourcePath}.assignments[${index}].confidence must be high, medium, or low`);
		}
		const key = `${assignment.area}\0${assignment.family}`;
		if (seen.has(key)) throw new RouterError(`${sourcePath} contains a duplicate assignment: ${assignment.area} -> ${assignment.family}`);
		seen.add(key);
		if (value.status !== "classified") continue;
		if (typeof assignment.rationale !== "string" || !assignment.rationale.trim() || !Array.isArray(assignment.evidence) || assignment.evidence.length === 0) {
			throw new RouterError(`${sourcePath}.assignments[${index}] requires rationale and evidence`);
		}
		let nonGeneratedEvidence = false;
		for (const [evidenceIndex, evidence] of assignment.evidence.entries()) {
			if (!evidence || typeof evidence !== "object" || Array.isArray(evidence) || !isRelativePath(evidence.path) || typeof evidence.description !== "string" || !evidence.description.trim()) {
				throw new RouterError(`${sourcePath}.assignments[${index}].evidence[${evidenceIndex}] is invalid`);
			}
			if (evidence.line_start !== undefined && (!Number.isInteger(evidence.line_start) || evidence.line_start < 1)) throw new RouterError(`${sourcePath}.assignments[${index}] has an invalid line_start`);
			if (evidence.line_end !== undefined && (!Number.isInteger(evidence.line_end) || evidence.line_end < 1)) throw new RouterError(`${sourcePath}.assignments[${index}] has an invalid line_end`);
			if (evidence.line_start !== undefined && evidence.line_end !== undefined && evidence.line_end < evidence.line_start) throw new RouterError(`${sourcePath}.assignments[${index}] has a reversed line range`);
			if (evidence.kind !== "generated_skill") nonGeneratedEvidence = true;
			validateEvidenceFile(
				value.source_checkout,
				evidence.path,
				evidence.line_start,
				evidence.line_end,
				`${sourcePath}.assignments[${index}].evidence[${evidenceIndex}]`,
			);
		}
		if (!nonGeneratedEvidence) throw new RouterError(`${sourcePath} assignment ${assignment.area} -> ${assignment.family} has no non-generated repository evidence`);
		if (assignment.repo_skill_paths !== undefined && (!Array.isArray(assignment.repo_skill_paths) || assignment.repo_skill_paths.some((item) => !isRelativePath(item)))) {
			throw new RouterError(`${sourcePath}.assignments[${index}].repo_skill_paths is invalid`);
		}
	}
	if (value.status === "classified" && seen.size === 0) throw new RouterError(`${sourcePath}.classified status requires assignments`);
	if (value.status === "unclassified" && (seen.size !== 0 || typeof value.unclassified_reason !== "string" || !value.unclassified_reason.trim())) {
		throw new RouterError(`${sourcePath}.unclassified status requires a reason and no assignments`);
	}
	return value;
}

function readRoutingEntries(routingEntryPaths, taxonomy, taxonomySha256) {
	const entries = new Map();
	for (const sourcePath of routingEntryPaths) {
		const value = validateRoutingEntry(loadJson(sourcePath), sourcePath, taxonomy, taxonomySha256);
		if (entries.has(value.skill_id)) throw new RouterError(`duplicate routing handoff for skill ${value.skill_id}`);
		entries.set(value.skill_id, value);
	}
	return entries;
}

function makeRepositoryRecords(skills, existingRows, routingEntries) {
	const existing = new Map(existingRows.filter((row) => row && typeof row.skill_id === "string").map((row) => [row.skill_id, row]));
	return skills.map((skill) => {
		const prior = existing.get(skill.id) || {};
		const handoff = routingEntries.get(skill.id) || {};
		const provenance = readProvenance(skill.dir);
		const provenanceRepository = provenance?.repository && typeof provenance.repository === "object" ? provenance.repository : {};
		const provenanceSkill = provenance?.generated_skill && typeof provenance.generated_skill === "object" ? provenance.generated_skill : {};
		const sourceUrl = normalizeGithubUrl(handoff.source_url) || normalizeGithubUrl(prior.source_url) || normalizeGithubUrl(provenanceRepository.remote_url) || `https://github.com/${skill.metadata.repoId}`;
		const sourceCommit = /^[0-9a-f]{40}$/i.test(String(handoff.source_commit || ""))
			? String(handoff.source_commit).toLowerCase()
			: /^[0-9a-f]{40}$/i.test(String(prior.source_commit || ""))
				? String(prior.source_commit).toLowerCase()
				: /^[0-9a-f]{40}$/i.test(String(provenanceRepository.commit || ""))
					? String(provenanceRepository.commit).toLowerCase()
					: null;
		const sourceSkillRoot = handoff.source_skill_root || handoff.skill_root || prior.source_skill_root || provenanceSkill.root || null;
		const currentContentSha256 = treeDigest(skill.dir);
		const declaredContentSha256 = normalizeDigest(handoff.skill_content_sha256 || handoff.content_sha256);
		if (declaredContentSha256 && declaredContentSha256 !== currentContentSha256) {
			throw new RouterError(`routing handoff content digest does not match live skill ${skill.id}`);
		}
		// Always recompute the digest. Reusing a prior repository-index value would
		// leave stale content_sha256 after a refresh or a local skill replacement.
		const contentSha256 = currentContentSha256;
		return {
			schema_version: 1,
			repo_id: skill.metadata.repoId,
			legacy_repo_id: typeof handoff.legacy_repo_id === "string"
				? handoff.legacy_repo_id
				: typeof prior.legacy_repo_id === "string"
					? prior.legacy_repo_id
					: null,
			repo_name: skill.metadata.repoId.split("/").at(-1),
			skill_id: skill.id,
			source_url: sourceUrl,
			source_commit: sourceCommit,
			source_skill_root: sourceSkillRoot,
			target_skill_root: `repo-skills/${skill.id}`,
			aliases: Array.isArray(prior.aliases) ? [...prior.aliases].sort() : [],
			content_sha256: contentSha256,
			description: skill.description,
		};
	}).sort((left, right) => left.repo_id.localeCompare(right.repo_id) || left.skill_id.localeCompare(right.skill_id));
}

function makeAssignmentRecords(skills, repositoryRecords, existingRows, routingEntries, taxonomy) {
	const repositories = new Map(repositoryRecords.map((record) => [record.skill_id, record]));
	const existing = new Map(existingRows.filter((row) => row && typeof row.repo_id === "string" && typeof row.area === "string" && typeof row.family === "string")
		.map((row) => [`${row.repo_id}\0${row.area}\0${row.family}`, row]));
	const taxonomyOrder = new Map();
	let order = 0;
	for (const area of taxonomy.areas) for (const family of area.families) taxonomyOrder.set(`${area.name}\0${family.name}`, order++);
	return skills.flatMap((skill) => {
		const repository = repositories.get(skill.id);
		const handoff = routingEntries.get(skill.id);
		return skill.metadata.assignments.map((assignment) => {
			const key = `${skill.metadata.repoId}\0${assignment.area}\0${assignment.family}`;
			const prior = existing.get(key);
			const handoffAssignment = handoff?.assignments.find((candidate) => candidate.area === assignment.area && candidate.family === assignment.family);
			const confidence = handoffAssignment?.confidence ?? prior?.confidence;
			if (!new Set(["high", "medium", "low"]).has(confidence)) {
				throw new RouterError(`central assignment ${skill.metadata.repoId} -> ${assignment.area} -> ${assignment.family} is missing a valid confidence`);
			}
			return {
				repo_id: skill.metadata.repoId,
				legacy_repo_id: repository?.legacy_repo_id ?? null,
				skill_id: skill.id,
				area: assignment.area,
				family: assignment.family,
				confidence,
			};
		});
	}).sort((left, right) => taxonomyOrder.get(`${left.area}\0${left.family}`) - taxonomyOrder.get(`${right.area}\0${right.family}`) || left.repo_id.localeCompare(right.repo_id) || left.skill_id.localeCompare(right.skill_id));
}

function familyMap(taxonomy, skills) {
	const byKey = new Map();
	for (const area of taxonomy.areas) for (const family of area.families) byKey.set(`${area.name}\0${family.name}`, { area, family, skills: [] });
	for (const skill of skills) for (const assignment of skill.metadata.assignments) byKey.get(`${assignment.area}\0${assignment.family}`).skills.push(skill);
	for (const entry of byKey.values()) entry.skills.sort((left, right) => left.metadata.repoId.localeCompare(right.metadata.repoId) || left.id.localeCompare(right.id));
	return byKey;
}

function renderFrontmatter(templateDir, disabled) {
	const templateFile = path.join(templateDir, "SKILL.md");
	const source = isRegularFile(templateFile) ? readText(templateFile) : "";
	const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---/);
	let frontmatter = match ? parse(match[1]) : {};
	if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) frontmatter = {};
	frontmatter.name = ROUTER_ID;
	frontmatter.description = ROUTER_DESCRIPTION;
	frontmatter.metadata = { ...(frontmatter.metadata && typeof frontmatter.metadata === "object" ? frontmatter.metadata : {}), "disco-role": "operating" };
	delete frontmatter["disable-model-invocation"];
	if (disabled) frontmatter["disable-model-invocation"] = true;
	const lines = ["---", ...Object.entries(frontmatter).map(([key, value]) => {
		if (typeof value === "string") return `${key}: ${JSON.stringify(value)}`;
		if (value && typeof value === "object" && !Array.isArray(value)) return `${key}:\n${Object.entries(value).map(([childKey, childValue]) => `  ${childKey}: ${JSON.stringify(childValue)}`).join("\n")}`;
		return `${key}: ${String(value)}`;
	}), "---", ""];
	return lines.join("\n");
}

function renderRoot(taxonomy, map, skills, disabled, templateDir) {
	const populatedAreas = taxonomy.areas.filter((area) => area.families.some((family) => map.get(`${area.name}\0${family.name}`).skills.length > 0));
	const areaRows = populatedAreas.map((area) => {
		const populated = area.families.filter((family) => map.get(`${area.name}\0${family.name}`).skills.length > 0);
		const memberships = populated.reduce((sum, family) => sum + map.get(`${area.name}\0${family.name}`).skills.length, 0);
		return `| [${markdownEscape(area.name)}](references/areas/${slug(area.name)}.md) | ${populated.length} | ${memberships} |`;
	}).join("\n");
	return `${renderFrontmatter(templateDir, disabled)}# Repo Skills Router\n\nUse this router for substantive requests where a managed repository skill may provide implementation guidance. It is a progressive-disclosure index, not a replacement for the selected repository skill.\n\n## Routing procedure\n\n1. Identify the user's dominant capability, workflow, data/model format, and runtime intent.\n2. Read only the one or two most likely area pages below.\n3. Compare the relevant family pages, especially when training, inference, evaluation, deployment, or similarly named repositories overlap.\n4. Open the selected repository root at \`../repo-skills/<skill-id>/SKILL.md\`, then read only its relevant sub-skills, references, and scripts.\n5. If no exact family fits, do not force a repository match; continue with the general task context or report that the managed collection has no exact route.\n\nA repository may appear in several families. Choose the smallest set of repository roots that directly covers the request, and do not load every candidate listed on a family page.\n\n## Area quick map\n\n| Area | Populated families | Repository memberships | Area page |\n| --- | ---: | ---: | --- |\n${areaRows}\n\n## Maintenance\n\nThe machine-readable files under \`references/index/\` are the generated routing source of truth. Do not hand-edit area or family pages. For import, refresh, extension, or taxonomy changes, read [references/maintenance.md](references/maintenance.md) and use the verified importer/updater transaction.\n`;
}

function renderAreaPage(area, map) {
	const rows = area.families.filter((family) => map.get(`${area.name}\0${family.name}`).skills.length > 0).map((family) => {
		const entry = map.get(`${area.name}\0${family.name}`);
		return `| [${markdownEscape(family.name)}](../families/${slug(area.name)}/${slug(family.name)}.md) | ${markdownEscape(family.scope)} | ${entry.skills.length} |`;
	}).join("\n");
	return `# ${area.name}\n\n${area.scope || `Use this area for ${area.name.toLowerCase()} tasks.`}\n\nRead a family page only after confirming that the family scope matches the user's actual capability.\n\n| Family | Scope | Repositories |\n| --- | --- | ---: |\n${rows}\n`;
}

function renderFamilyPage(area, family, skills) {
	const rows = skills.map((skill) => `| [\`${skill.id}\`](../../../../repo-skills/${skill.id}/SKILL.md) | \`${markdownEscape(skill.metadata.repoId)}\` | ${markdownEscape(skill.description)} |`).join("\n");
	return `# ${area.name} -> ${family.name}\n\n${family.scope}\n\nChoose a repository below only when its description, package/repository identity, task surface, and runtime intent match the request. If several candidates overlap, prefer the one whose root skill directly covers the requested workflow; then inspect its internal navigation rather than loading all candidates.\n\n| Repo skill | Repository | Skill description |\n| --- | --- | --- |\n${rows}\n`;
}

function renderMaintenance(taxonomy, skills) {
	return `# Router maintenance\n\nThis router is generated from the fixed area -> family taxonomy and the v2 \`references/repo-routing-metadata.json\` fragment attached to each repository skill. The compact fragment contains only identity, taxonomy hash, status, and exact assignments. Full classification evidence belongs in the external production routing decision artifact, not in the runtime skill graph.\n\n## Import contract\n\n1. Finish and independently verify the generated repository skill.\n2. Classify it against the exact taxonomy using repository evidence plus the generated skill as navigation context.\n3. Write the external routing decision with assignment-specific rationale, evidence, and assignment-level confidence (\`high\`, \`medium\`, or \`low\`).\n4. Write the minimal v2 metadata fragment only after the decision is made; confidence remains in the central assignment index and is not copied into runtime metadata.\n5. Run the verified importer/updater under the shared lock so the skill, metadata, indexes, and router are updated together.\n\nThe central \`repositories.jsonl\` index preserves canonical repository identity, optional \`legacy_repo_id\`, source provenance, target skill root, aliases, content digest, and root description. The central \`assignments.jsonl\` index preserves canonical identity, optional \`legacy_repo_id\`, skill ID, exact area/family path, and confidence. These generated indexes are validated together with the per-skill metadata; unknown fields, duplicate identities, stale digests, and mismatched assignments are errors.\n\n\`unclassified\` is valid only when no exact family is supported. Ask the user whether to import it; if they want it included, propose a taxonomy extension and wait for approval/correction before changing the canonical taxonomy. \`blocked\` and \`failed\` are processing outcomes and must not be imported as routable skills.\n\n## Current generated scope\n\n- Areas in taxonomy: ${taxonomy.areas.length}\n- Routable repository skills: ${skills.length}\n- Taxonomy memberships: ${skills.reduce((sum, skill) => sum + skill.metadata.assignments.length, 0)}\n\nUse \`node update_repo_skills_router.mjs --library-root <library-root>\` for a full rebuild, or \`--include-skill <skill-id>\` with \`--output-router-dir <dir>\` for a filtered export.\n`;
}

function clearGeneratedRouter(routerDir) {
	if (!isDirectory(routerDir)) fs.mkdirSync(routerDir, { recursive: true });
	for (const relativePath of ["SKILL.md", "references/areas", "references/families", "references/index", "references/maintenance.md"]) {
		fs.rmSync(path.join(routerDir, relativePath), { recursive: true, force: true });
	}
}

function validateGeneratedRouter(routerDir, skills, taxonomy, membershipMap, repositoryRecords, assignmentRecords, checkSkillLinks) {
	if (!isRegularFile(path.join(routerDir, "SKILL.md"))) throw new RouterError(`generated router is missing ${path.join(routerDir, "SKILL.md")}`);
	const rootText = readText(path.join(routerDir, "SKILL.md"));
	const expectedSkillIds = new Set(skills.map((skill) => skill.id));
	const indexedSkillIds = new Set(repositoryRecords.map((record) => record.skill_id));
	if (indexedSkillIds.size !== expectedSkillIds.size || [...expectedSkillIds].some((id) => !indexedSkillIds.has(id))) throw new RouterError("generated repository index does not match selected routable skills");
	const repositoryBySkill = new Map(repositoryRecords.map((record) => [record.skill_id, record]));
	const repositoryIds = new Set();
	const foldedRepositoryIds = new Set();
	for (const record of repositoryRecords) {
		const unknownField = Object.keys(record).find((key) => !REPOSITORY_INDEX_FIELDS.has(key));
		if (unknownField) throw new RouterError(`generated repository index contains unknown field ${unknownField}`);
		if (typeof record.repo_id !== "string" || !REPO_ID.test(record.repo_id)) throw new RouterError(`generated repository index has an invalid repo_id for ${record.skill_id}`);
		if (record.repo_name !== record.repo_id.split("/").at(-1)) throw new RouterError(`generated repository index has a stale repo_name for ${record.repo_id}`);
		if (record.source_commit !== null && (typeof record.source_commit !== "string" || !/^[0-9a-f]{40}$/i.test(record.source_commit))) throw new RouterError(`generated repository index has an invalid source_commit for ${record.repo_id}`);
		if (record.source_skill_root !== null && (typeof record.source_skill_root !== "string" || !isRelativePath(record.source_skill_root))) throw new RouterError(`generated repository index has an invalid source_skill_root for ${record.repo_id}`);
		if (!Array.isArray(record.aliases) || record.aliases.some((alias) => typeof alias !== "string")) throw new RouterError(`generated repository index has invalid aliases for ${record.repo_id}`);
		if (typeof record.description !== "string" || !record.description.trim()) throw new RouterError(`generated repository index has an invalid description for ${record.repo_id}`);
		if (record.legacy_repo_id !== null && (typeof record.legacy_repo_id !== "string" || !record.legacy_repo_id.trim())) {
			throw new RouterError(`generated repository index has invalid legacy_repo_id for ${record.repo_id}`);
		}
		const foldedRepoId = record.repo_id.toLowerCase();
		if (repositoryIds.has(record.repo_id) || foldedRepositoryIds.has(foldedRepoId)) throw new RouterError(`generated repository index contains duplicate repo_id ${record.repo_id}`);
		repositoryIds.add(record.repo_id);
		foldedRepositoryIds.add(foldedRepoId);
	}
	const expectedAssignments = new Set(assignmentRecords.map((record) => `${record.repo_id}\0${record.area}\0${record.family}`));
	const actualAssignments = new Set();
	const taxonomyPaths = new Set(taxonomy.areas.flatMap((area) => area.families.map((family) => `${area.name}\0${family.name}`)));
	for (const record of assignmentRecords) {
		const unknownField = Object.keys(record).find((key) => !ASSIGNMENT_INDEX_FIELDS.has(key));
		if (unknownField) throw new RouterError(`generated assignment index contains unknown field ${unknownField}`);
		const repository = repositoryBySkill.get(record.skill_id);
		if (
			!repository ||
			record.repo_id !== repository.repo_id ||
			record.legacy_repo_id !== repository.legacy_repo_id ||
			typeof record.area !== "string" ||
			typeof record.family !== "string" ||
			!taxonomyPaths.has(`${record.area}\0${record.family}`)
		) throw new RouterError(`generated assignment index has stale repository identity or taxonomy path for ${record.repo_id}`);
		if (!new Set(["high", "medium", "low"]).has(record.confidence)) throw new RouterError(`generated assignment index has invalid confidence for ${record.repo_id}`);
		const key = `${record.repo_id}\0${record.area}\0${record.family}`;
		if (actualAssignments.has(key)) throw new RouterError(`generated assignment index contains a duplicate: ${record.repo_id} -> ${record.area} -> ${record.family}`);
		actualAssignments.add(key);
	}
	if (actualAssignments.size !== expectedAssignments.size) throw new RouterError("generated assignment index is not deterministic");
	for (const area of taxonomy.areas) {
		const areaFile = path.join(routerDir, "references", "areas", `${slug(area.name)}.md`);
		const hasFamily = area.families.some((family) => skills.some((skill) => skill.metadata.assignments.some((assignment) => assignment.area === area.name && assignment.family === family.name)));
		const areaLink = `references/areas/${slug(area.name)}.md`;
		if (hasFamily) {
			if (!isRegularFile(areaFile)) throw new RouterError(`generated router is missing area page: ${area.name}`);
			if (!rootText.includes(`(${areaLink})`)) throw new RouterError(`generated router root does not link area page: ${area.name}`);
		} else if (exists(areaFile) || rootText.includes(`(${areaLink})`)) {
			throw new RouterError(`generated subset router contains an empty area: ${area.name}`);
		}
		let areaText;
		if (hasFamily) areaText = readText(areaFile);
		for (const family of area.families) {
			const entry = membershipMap.get(`${area.name}\0${family.name}`);
			const familyFile = path.join(routerDir, "references", "families", slug(area.name), `${slug(family.name)}.md`);
			if (entry.skills.length && !isRegularFile(familyFile)) throw new RouterError(`generated router is missing family page: ${area.name} -> ${family.name}`);
			const familyLink = `../families/${slug(area.name)}/${slug(family.name)}.md`;
			if (entry.skills.length && !areaText.includes(`(${familyLink})`)) throw new RouterError(`generated area page does not link family: ${area.name} -> ${family.name}`);
			if (!entry.skills.length) {
				if (exists(familyFile)) throw new RouterError(`generated subset router contains an empty family: ${area.name} -> ${family.name}`);
				continue;
			}
			const text = readText(familyFile);
			for (const skill of entry.skills) {
				const relativeTarget = path.join(routerDir, "references", "families", slug(area.name), "../../../../repo-skills", skill.id, "SKILL.md");
				if (checkSkillLinks && !isRegularFile(relativeTarget)) throw new RouterError(`generated router link target is missing: ${skill.id}`);
				if (!text.includes(`repo-skills/${skill.id}/SKILL.md`)) throw new RouterError(`generated family page does not link ${skill.id}`);
			}
		}
	}
}

function buildRouter(libraryRoot, templateDir, options) {
	const repoSkillsRoot = path.join(libraryRoot, "repo-skills");
	const liveRouterDir = path.join(libraryRoot, ROUTER_ID);
	if (!isDirectory(repoSkillsRoot)) throw new RouterError(`repo-skills collection does not exist: ${repoSkillsRoot}`);
	if (!isDirectory(templateDir)) throw new RouterError(`router template does not exist: ${templateDir}`);
	const { taxonomy, taxonomySha256 } = resolveTaxonomy(liveRouterDir, templateDir);
	const existingRecords = readExistingRecords(repoSkillsRoot, liveRouterDir, templateDir);
	const existingAssignmentRecords = readExistingAssignmentRecords(liveRouterDir, templateDir);
	const managedSkillIds = existingRecords.length ? new Set(existingRecords.map((record) => record?.skill_id).filter((skillId) => typeof skillId === "string")) : undefined;
	const skills = readLiveSkills(repoSkillsRoot, options.includeSkillIds, taxonomy, taxonomySha256, managedSkillIds);
	const map = familyMap(taxonomy, skills);
	const routerDir = options.outputRouterDir || liveRouterDir;
	const routingEntries = readRoutingEntries(options.routingEntryPaths, taxonomy, taxonomySha256);
	for (const [skillId, entry] of routingEntries) {
		const skill = skills.find((candidate) => candidate.id === skillId);
		if (!skill) throw new RouterError(`routing handoff ${skillId} is not part of this router build`);
		if (skill.metadata.repoId !== entry.repo_id) throw new RouterError(`routing handoff repo_id does not match ${skillId}`);
		const metadataKeys = new Set(skill.metadata.assignments.map((assignment) => `${assignment.area}\0${assignment.family}`));
		const handoffKeys = new Set(entry.assignments.map((assignment) => `${assignment.area}\0${assignment.family}`));
		if (metadataKeys.size !== handoffKeys.size || [...metadataKeys].some((key) => !handoffKeys.has(key))) throw new RouterError(`routing handoff assignments do not match ${skillId} metadata`);
	}
	let disabled = options.routerVisibility === "disabled";
	if (options.routerVisibility === "preserve" && isRegularFile(path.join(liveRouterDir, "SKILL.md"))) {
		const existingFrontmatter = parseFrontmatter(path.join(liveRouterDir, "SKILL.md"));
		disabled = existingFrontmatter["disable-model-invocation"] === true;
	}
	clearGeneratedRouter(routerDir);
	fs.mkdirSync(path.join(routerDir, "references", "areas"), { recursive: true });
	fs.mkdirSync(path.join(routerDir, "references", "families"), { recursive: true });
	fs.mkdirSync(path.join(routerDir, "references", "index"), { recursive: true });
	writeText(path.join(routerDir, "SKILL.md"), renderRoot(taxonomy, map, skills, disabled, templateDir));
	for (const area of taxonomy.areas) {
		const populated = area.families.some((family) => map.get(`${area.name}\0${family.name}`).skills.length > 0);
		if (!populated) continue;
		writeText(path.join(routerDir, "references", "areas", `${slug(area.name)}.md`), renderAreaPage(area, map));
		for (const family of area.families) {
			const entry = map.get(`${area.name}\0${family.name}`);
			if (!entry.skills.length) continue;
			writeText(path.join(routerDir, "references", "families", slug(area.name), `${slug(family.name)}.md`), renderFamilyPage(area, family, entry.skills));
		}
	}
	const repositoryRecords = makeRepositoryRecords(skills, existingRecords, routingEntries);
	const assignmentRecords = makeAssignmentRecords(skills, repositoryRecords, existingAssignmentRecords, routingEntries, taxonomy);
	const repositoryIndexDigest = `sha256:${requireHash(repositoryRecords.map((record) => JSON.stringify(record)).join("\n") + "\n")}`;
	const assignmentIndexDigest = `sha256:${requireHash(assignmentRecords.map((record) => JSON.stringify(record)).join("\n") + "\n")}`;
	const buildMetadata = {
		schema_version: 1,
		repository_count: repositoryRecords.length,
		assignment_count: assignmentRecords.length,
		area_count: taxonomy.areas.length,
		family_count: taxonomy.areas.reduce((sum, area) => sum + area.families.length, 0),
		non_empty_family_count: [...map.values()].filter((entry) => entry.skills.length > 0).length,
		taxonomy_sha256: taxonomySha256,
		repository_index_sha256: repositoryIndexDigest,
		assignment_index_sha256: assignmentIndexDigest,
		source_router_run_id: process.env.DISCO_ROUTER_SOURCE_RUN_ID || null,
	};
	writeText(path.join(routerDir, TAXONOMY_PATH), stableJson(taxonomy));
	writeJsonLines(path.join(routerDir, REPOSITORIES_PATH), repositoryRecords);
	writeJsonLines(path.join(routerDir, ASSIGNMENTS_PATH), assignmentRecords);
	writeText(path.join(routerDir, BUILD_METADATA_PATH), stableJson(stableJsonValue(buildMetadata)));
	if (routerDir === liveRouterDir) writeJsonLines(path.join(repoSkillsRoot, REPOSITORY_INDEX_PATH), repositoryRecords);
	writeText(path.join(routerDir, "references", "maintenance.md"), renderMaintenance(taxonomy, skills));
	const taxonomyDigest = createHash("sha256").update(fs.readFileSync(path.join(routerDir, TAXONOMY_PATH))).digest("hex");
	if (taxonomyDigest !== taxonomySha256) throw new RouterError(`generated taxonomy does not match the resolved taxonomy hash ${taxonomySha256}`);
	validateGeneratedRouter(routerDir, skills, taxonomy, map, repositoryRecords, assignmentRecords, routerDir === liveRouterDir);
	return { routerDir, skills: skills.length, assignments: assignmentRecords.length, areas: taxonomy.areas.length, families: taxonomy.areas.reduce((sum, area) => sum + area.families.length, 0) };
}

function requireHash(value) {
	return createHash("sha256").update(value).digest("hex");
}

function parseArgs(argv) {
	const args = { agentDir: undefined, libraryRoot: undefined, templateDir: bundledRouterTemplateDir(), includeSkillIds: [], outputRouterDir: undefined, routingEntryPaths: [], routerVisibility: undefined, alreadyLocked: false, timeout: DEFAULT_TIMEOUT_SECONDS };
	for (let index = 0; index < argv.length; index += 1) {
		const item = argv[index];
		if (item === "--agent-dir") args.agentDir = argv[++index];
		else if (item === "--library-root") args.libraryRoot = argv[++index];
		else if (item === "--template-dir") args.templateDir = argv[++index];
		else if (item === "--include-skill") args.includeSkillIds.push(...String(argv[++index] || "").split(",").map((id) => id.trim()).filter(Boolean));
		else if (item === "--output-router-dir") args.outputRouterDir = argv[++index];
		else if (item === "--routing-entry") args.routingEntryPaths.push(path.resolve(expandHome(argv[++index] || "")));
		else if (item === "--router-visibility") args.routerVisibility = argv[++index];
		else if (item === "--already-locked") args.alreadyLocked = true;
		else if (item === "--timeout") args.timeout = Number(argv[++index]);
		else if (item === "-h" || item === "--help") { printHelp(); process.exit(0); }
		else throw new RouterError(`unknown argument: ${item}`);
	}
	if (args.agentDir && args.libraryRoot) throw new RouterError("use either --agent-dir or --library-root, not both");
	if (!args.agentDir && !args.libraryRoot) args.agentDir = defaultAgentDir();
	if (args.routerVisibility && !["preserve", "enabled", "disabled"].includes(args.routerVisibility)) throw new RouterError("--router-visibility must be preserve, enabled, or disabled");
	args.routerVisibility ??= args.outputRouterDir || args.libraryRoot ? "enabled" : "preserve";
	if (!Number.isFinite(args.timeout) || args.timeout <= 0) throw new RouterError("--timeout must be positive");
	return args;
}

function printHelp() {
	console.log(`Usage: node update_repo_skills_router.mjs [options]\n\nOptions:\n  --agent-dir DIR       DisCo agent directory\n  --library-root DIR    Library root containing repo-skills/ and repo-skills-router/\n  --template-dir DIR    Bundled empty router template\n  --include-skill ID    Include only selected skill ids; repeat or comma-separate\n  --output-router-dir DIR  Write a filtered router to DIR\n  --routing-entry FILE  Verified external classification handoff; repeat for selected skills\n  --router-visibility POLICY  preserve, enabled, or disabled\n  --already-locked      Assert the shared import lock is already held\n  --timeout SECONDS     Lock timeout`);
}

function runUnderLock(argv, agentDir, timeout) {
	const lockScript = withImportLockScript();
	if (!exists(lockScript)) throw new RouterError(`with_import_lock.mjs not found next to updater: ${lockScript}`);
	const forwarded = argv.filter((item) => item !== "--already-locked");
	const command = [process.execPath, lockScript, "--agent-dir", agentDir, "--timeout", String(timeout), "--", process.execPath, SCRIPT_PATH, ...forwarded, "--already-locked"];
	const completed = spawnSync(command[0], command.slice(1), { stdio: "inherit" });
	if (completed.error) throw completed.error;
	return completed.status ?? 1;
}

function main(argv) {
	let args;
	try { args = parseArgs(argv); } catch (error) { console.error(`update_repo_skills_router.mjs: ${error.message}`); return 2; }
	const agentDir = args.agentDir ? path.resolve(expandHome(args.agentDir)) : undefined;
	const libraryRoot = path.resolve(expandHome(args.libraryRoot || path.join(agentDir, "skills")));
	const templateDir = path.resolve(expandHome(args.templateDir));
	const outputRouterDir = args.outputRouterDir ? path.resolve(expandHome(args.outputRouterDir)) : undefined;
	const includeSkillIds = [...new Set(args.includeSkillIds)];
	if (agentDir && !args.alreadyLocked && !process.env.DISCO_IMPORT_LOCK_PATH) return runUnderLock(argv, agentDir, args.timeout);
	if (agentDir && args.alreadyLocked && !process.env.DISCO_IMPORT_LOCK_PATH && process.env.DISCO_ALLOW_UNLOCKED_ROUTER_UPDATE_FOR_TESTS !== "1") {
		console.error("update_repo_skills_router.mjs: --already-locked requires DISCO_IMPORT_LOCK_PATH");
		return 2;
	}
	try {
		const result = buildRouter(libraryRoot, templateDir, { includeSkillIds, outputRouterDir, routingEntryPaths: args.routingEntryPaths, routerVisibility: args.routerVisibility });
		console.log(`updated ${result.routerDir}: ${result.skills} skills, ${result.assignments} assignments, ${result.areas} areas, ${result.families} families`);
		return 0;
	} catch (error) {
		console.error(`update_repo_skills_router.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return error instanceof RouterError ? 2 : 1;
	}
}

process.exitCode = main(process.argv.slice(2));
