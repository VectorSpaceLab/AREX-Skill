#!/usr/bin/env node

/**
 * Build a complete area -> family repository-skills collection in one staged
 * pass. This is the initial/full-build companion to import_repo_skill.mjs;
 * it deliberately does not invoke the single-repository importer.
 */

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseDocument, Scalar } from "yaml";

const DEFAULT_EXPECTED_REPOSITORIES = 1000;
const DEFAULT_EXPECTED_ASSIGNMENTS = 2186;
const TAXONOMY_SHA256 = "f8c306386015711634ddbb43a5eb95d1f58909c3513ce2063ba42efdd583a431";
const REPO_ID = /^[^/\s]+\/[^/\s]+$/;
const SKILL_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SCRIPT_DIR = path.dirname(SCRIPT_PATH);
const BUNDLED_TEMPLATE = path.resolve(SCRIPT_DIR, "../../repo-skills-router");
const ROUTER_UPDATER = path.join(SCRIPT_DIR, "update_repo_skills_router.mjs");

class BuilderError extends Error {
	constructor(message) {
		super(message);
		this.name = "BuilderError";
	}
}

function expandHome(value) {
	return String(value).replace(/^~(?=$|[\\/])/, os.homedir());
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

function regularFile(filePath) {
	if (!exists(filePath)) return false;
	const stat = fs.lstatSync(filePath);
	return stat.isFile() && !stat.isSymbolicLink();
}

function realDirectory(directory) {
	if (!exists(directory)) return false;
	const stat = fs.lstatSync(directory);
	return stat.isDirectory() && !stat.isSymbolicLink();
}

function isWithin(parent, candidate) {
	const relative = path.relative(parent, candidate);
	return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function readJson(filePath) {
	try {
		return JSON.parse(fs.readFileSync(filePath, "utf8"));
	} catch (error) {
		throw new BuilderError(`${filePath} is invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
	}
}

function readRecords(filePath, label) {
	if (!regularFile(filePath)) throw new BuilderError(`${label} does not exist as a regular file: ${filePath}`);
	const text = fs.readFileSync(filePath, "utf8").trim();
	if (!text) return [];
	if (filePath.toLowerCase().endsWith(".jsonl")) {
		return text.split(/\r?\n/).map((line, index) => {
			try {
				return JSON.parse(line);
			} catch (error) {
				throw new BuilderError(`${label}:${index + 1} is invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
			}
		});
	}
	const value = readJson(filePath);
	if (Array.isArray(value)) return value;
	for (const key of ["records", "repositories", "assignments", "items"]) {
		if (Array.isArray(value?.[key])) return value[key];
	}
	throw new BuilderError(`${label} must be a JSON array, JSONL file, or object containing records[]`);
}

function writeJsonLines(filePath, records) {
	fs.mkdirSync(path.dirname(filePath), { recursive: true });
	fs.writeFileSync(filePath, records.map((record) => JSON.stringify(record)).join("\n") + (records.length ? "\n" : ""), "utf8");
}

function stableJson(value) {
	return `${JSON.stringify(value, null, 2)}\n`;
}

function parseFrontmatter(filePath) {
	const content = fs.readFileSync(filePath, "utf8");
	const match = content.match(/^---(\r?\n)([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match?.[2]) throw new BuilderError(`${filePath} is missing YAML frontmatter`);
	const document = parseDocument(match[2]);
	if (document.errors.length > 0) throw new BuilderError(`${filePath} has invalid YAML frontmatter: ${document.errors[0]?.message}`);
	const value = document.toJS();
	if (!value || typeof value !== "object" || Array.isArray(value)) throw new BuilderError(`${filePath} frontmatter must be a mapping`);
	return { content, document, frontmatter: value, frontmatterEnd: match[0].length };
}

function quoteScalar(value) {
	const scalar = new Scalar(value);
	scalar.type = "QUOTE_DOUBLE";
	return scalar;
}

function normalizeSkillFrontmatter(filePath, expectedName, isRoot) {
	const parsed = parseFrontmatter(filePath);
	const currentName = parsed.frontmatter.name;
	if (typeof currentName !== "string" || !SKILL_ID.test(currentName)) {
		throw new BuilderError(`${filePath} must declare a canonical lowercase-hyphen name`);
	}
	if (!isRoot && currentName !== expectedName) {
		throw new BuilderError(`${filePath} name ${currentName} does not match its directory basename ${expectedName}`);
	}
	const description = parsed.frontmatter.description;
	if (typeof description !== "string" || !description.trim()) throw new BuilderError(`${filePath} must declare a non-empty description`);
	parsed.document.set("name", isRoot ? expectedName : currentName);
	parsed.document.set("description", quoteScalar(description.trim()));
	parsed.document.setIn(["metadata", "disco-role"], "operating");
	parsed.document.set("disable-model-invocation", true);
	const body = parsed.content.slice(parsed.frontmatterEnd);
	fs.writeFileSync(filePath, `---\n${parsed.document.toString()}---\n${body}`, "utf8");
}

function collectFiles(root, files = []) {
	if (!realDirectory(root)) throw new BuilderError(`skill source is not a real directory: ${root}`);
	for (const entry of fs.readdirSync(root, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
		const entryPath = path.join(root, entry.name);
		if (entry.isSymbolicLink()) throw new BuilderError(`skill source contains a symbolic link: ${entryPath}`);
		if (entry.isDirectory()) {
			if (entry.name === "__pycache__") throw new BuilderError(`skill source contains generated Python cache directory: ${entryPath}`);
			collectFiles(entryPath, files);
		} else if (entry.isFile()) {
			if (/\.(?:pyc|pyo)$/i.test(entry.name)) throw new BuilderError(`skill source contains generated Python bytecode: ${entryPath}`);
			files.push(entryPath);
		}
		else throw new BuilderError(`skill source contains a non-portable entry: ${entryPath}`);
	}
	return files;
}

function copyTree(source, destination) {
	const files = collectFiles(source);
	for (const sourceFile of files) {
		const relativePath = path.relative(source, sourceFile);
		const target = path.join(destination, relativePath);
		fs.mkdirSync(path.dirname(target), { recursive: true });
		fs.copyFileSync(sourceFile, target);
	}
}

function treeDigest(root) {
	const hash = createHash("sha256");
	const files = collectFiles(root).sort((left, right) => left.localeCompare(right));
	for (const filePath of files) {
		const relativePath = path.relative(root, filePath).split(path.sep).join("/");
		const content = fs.readFileSync(filePath);
		hash.update(`file\0${relativePath}\0${content.byteLength}\0`);
		hash.update(content);
		hash.update("\0");
	}
	return `sha256:${hash.digest("hex")}`;
}

function validateMarkdownLinks(skillRoot) {
	for (const filePath of collectFiles(skillRoot).filter((file) => path.extname(file).toLowerCase() === ".md")) {
		const content = fs.readFileSync(filePath, "utf8");
		let fenced = false;
		const prose = content.split(/\r?\n/).filter((line) => {
			if (/^\s*```/.test(line)) {
				fenced = !fenced;
				return false;
			}
			return !fenced;
		}).join("\n").replace(/(`+)[\s\S]*?\1/g, "");
		for (const match of prose.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
			let target = match[1]?.trim();
			if (!target || target.startsWith("#") || /^[a-z][a-z0-9+.-]*:/i.test(target)) continue;
			if (target.startsWith("<") && target.endsWith(">")) target = target.slice(1, -1);
			target = target.split("#", 1)[0]?.split("?", 1)[0] ?? "";
			if (!target) continue;
			let decoded;
			try {
				decoded = decodeURIComponent(target);
			} catch {
				throw new BuilderError(`${filePath} contains an invalid encoded Markdown link: ${target}`);
			}
			const resolved = path.resolve(path.dirname(filePath), decoded);
			if (!isWithin(skillRoot, resolved) || !exists(resolved)) throw new BuilderError(`${filePath} contains a broken or external relative link: ${target}`);
		}
	}
}

function normalizeSkillGraph(sourceRoot, targetRoot, skillId) {
	copyTree(sourceRoot, targetRoot);
	const files = collectFiles(targetRoot);
	const rootSkill = path.join(targetRoot, "SKILL.md");
	if (!regularFile(rootSkill)) throw new BuilderError(`selected skill root is missing SKILL.md: ${sourceRoot}`);
	const seenNames = new Set();
	for (const filePath of files.filter((file) => path.basename(file) === "SKILL.md")) {
		const relativeDirectory = path.relative(targetRoot, path.dirname(filePath));
		const isRoot = relativeDirectory === "";
		const expectedName = isRoot ? skillId : path.basename(path.dirname(filePath));
		normalizeSkillFrontmatter(filePath, expectedName, isRoot);
		const finalName = isRoot ? skillId : expectedName;
		if (seenNames.has(finalName)) throw new BuilderError(`skill graph contains duplicate skill name ${finalName}: ${sourceRoot}`);
		seenNames.add(finalName);
	}
	validateMarkdownLinks(targetRoot);
}

function validateRuntimePrivacy(skillRoot, record) {
	const forbidden = [];
	if (typeof record.source_checkout === "string" && record.source_checkout.trim()) {
		forbidden.push({ value: path.resolve(expandHome(record.source_checkout)), label: "source_checkout" });
	}
	forbidden.push({ value: path.join(os.homedir(), ".disco", "agent", "envs") + path.sep, label: "private DisCo environment" });
	for (const filePath of collectFiles(skillRoot)) {
		const content = fs.readFileSync(filePath);
		for (const item of forbidden) {
			if (content.includes(Buffer.from(item.value))) {
				throw new BuilderError(`${filePath} leaks the production ${item.label} path ${item.value}`);
			}
		}
	}
}

function normalizeTaxonomy(value, sourcePath) {
	if (!value || typeof value !== "object" || Array.isArray(value) || !Array.isArray(value.areas)) throw new BuilderError(`${sourcePath} must contain an areas array`);
	const areas = value.areas.map((area, areaIndex) => {
		if (!area || typeof area.name !== "string" || typeof area.scope !== "string" || !Array.isArray(area.families)) throw new BuilderError(`${sourcePath}: invalid area at index ${areaIndex}`);
		const families = area.families.map((family, familyIndex) => {
			if (!family || typeof family.name !== "string" || typeof family.scope !== "string") throw new BuilderError(`${sourcePath}: invalid family at ${area.name}/${familyIndex}`);
			if (family.id !== undefined && (typeof family.id !== "string" || !family.id.trim())) throw new BuilderError(`${sourcePath}: invalid family id at ${area.name}/${familyIndex}`);
			return family;
		});
		if (area.id !== undefined && (typeof area.id !== "string" || !area.id.trim())) throw new BuilderError(`${sourcePath}: invalid area id at index ${areaIndex}`);
		area.families = families;
		return area;
	});
	const paths = new Set();
	const order = new Map();
	let orderIndex = 0;
	for (const area of areas) for (const family of area.families) {
		const key = `${area.name}\0${family.name}`;
		if (paths.has(key)) throw new BuilderError(`${sourcePath} contains a duplicate taxonomy path: ${area.name} -> ${family.name}`);
		paths.add(key);
		order.set(key, orderIndex++);
	}
	value.areas = areas;
	Object.defineProperty(value, "paths", { value: paths, enumerable: false, writable: false, configurable: false });
	Object.defineProperty(value, "order", { value: order, enumerable: false, writable: false, configurable: false });
	return value;
}

function validateRepoId(value, field, sourcePath) {
	if (typeof value !== "string" || !REPO_ID.test(value)) throw new BuilderError(`${sourcePath}.${field} must use owner/repository form`);
}

function validateGithubUrl(value, sourcePath) {
	if (typeof value !== "string" || !/^https:\/\/github\.com\/[^/\s]+\/[^/\s]+(?:\.git)?\/?$/i.test(value.trim())) {
		throw new BuilderError(`${sourcePath}.source_url must be a canonical GitHub repository URL`);
	}
}

function normalizedRepoFromGithubUrl(value) {
	return value.trim().replace(/^https:\/\/github\.com\//i, "").replace(/\.git\/?$/i, "").replace(/\/$/, "").toLowerCase();
}

function sourcePathFor(record, sourceManifestPath, sourceRoot) {
	if (typeof record.source_skill_root !== "string" || !record.source_skill_root.trim()) throw new BuilderError(`source manifest record ${record.repo_id} is missing source_skill_root`);
	const value = expandHome(record.source_skill_root);
	if (path.isAbsolute(value)) return path.resolve(value);
	if (typeof record.source_checkout === "string" && record.source_checkout.trim()) return path.resolve(expandHome(record.source_checkout), value);
	if (sourceRoot) return path.resolve(sourceRoot, value);
	return path.resolve(path.dirname(sourceManifestPath), value);
}

function validateSourceMetadata(skillRoot, record, assignments, taxonomy) {
	const metadataFile = path.join(skillRoot, "references", "repo-routing-metadata.json");
	if (!regularFile(metadataFile)) throw new BuilderError(`${metadataFile} is missing; full collection builds require v2 routing metadata for every managed repository skill`);
	const value = readJson(metadataFile);
	if (!value || typeof value !== "object" || Array.isArray(value)) throw new BuilderError(`${metadataFile} must contain an object`);
	const allowed = new Set(["schema_version", "repo_id", "skill_id", "taxonomy_sha256", "routing_status", "assignments", "unclassified_reason"]);
	for (const key of Object.keys(value)) if (!allowed.has(key)) throw new BuilderError(`${metadataFile} contains unknown field ${key}`);
	if (value.schema_version !== "2.0") throw new BuilderError(`${metadataFile} uses a non-v2 routing schema; refusing to silently import legacy scenario metadata`);
	if (value.repo_id !== record.repo_id || value.skill_id !== record.skill_id || value.taxonomy_sha256 !== TAXONOMY_SHA256) {
		throw new BuilderError(`${metadataFile} repo identity or taxonomy does not match the source import manifest`);
	}
	if (value.routing_status !== "classified" || value.unclassified_reason !== undefined) throw new BuilderError(`${metadataFile} must be classified without unclassified_reason for a full collection build`);
	if (!Array.isArray(value.assignments)) throw new BuilderError(`${metadataFile}.assignments must be an array`);
	const expected = new Set(assignments.map((assignment) => `${assignment.area}\0${assignment.family}`));
	const actual = new Set(value.assignments.map((assignment) => {
		if (!assignment || typeof assignment !== "object" || Array.isArray(assignment) || Object.keys(assignment).some((key) => !["area", "family"].includes(key)) || typeof assignment.area !== "string" || typeof assignment.family !== "string") {
			throw new BuilderError(`${metadataFile} contains an invalid assignment`);
		}
		return `${assignment.area}\0${assignment.family}`;
	}));
	if (expected.size !== actual.size || [...expected].some((key) => !actual.has(key))) throw new BuilderError(`${metadataFile} assignments do not match the authoritative assignment ledger`);
	for (const key of actual) if (!taxonomy.paths.has(key)) throw new BuilderError(`${metadataFile} contains an invalid taxonomy path`);
}

function writeRoutingMetadata(skillRoot, record, assignments) {
	const metadataPath = path.join(skillRoot, "references", "repo-routing-metadata.json");
	fs.mkdirSync(path.dirname(metadataPath), { recursive: true });
	const value = {
		schema_version: "2.0",
		repo_id: record.repo_id,
		skill_id: record.skill_id,
		taxonomy_sha256: TAXONOMY_SHA256,
		routing_status: "classified",
		assignments: assignments.map(({ area, family }) => ({ area, family })),
	};
	fs.writeFileSync(metadataPath, stableJson(value), "utf8");
}

function validateRepositoryManifest(records, expectedCount, sourcePath) {
	if (records.length !== expectedCount) throw new BuilderError(`repository manifest has ${records.length} records; expected ${expectedCount}`);
	const byRepo = new Map();
	const caseFolded = new Map();
	for (const [index, record] of records.entries()) {
		const source = `${sourcePath}:${index + 1}`;
		validateRepoId(record?.repo_id, "repo_id", source);
		if (byRepo.has(record.repo_id)) throw new BuilderError(`${source} duplicates repo_id ${record.repo_id}`);
		const folded = record.repo_id.toLowerCase();
		if (caseFolded.has(folded)) throw new BuilderError(`${source} case-insensitively duplicates repo_id ${caseFolded.get(folded)}`);
		if (record.status !== "classified") throw new BuilderError(`${source} has status ${JSON.stringify(record.status)}; full collection builds accept classified repositories only`);
		byRepo.set(record.repo_id, record);
		caseFolded.set(folded, record.repo_id);
	}
	return byRepo;
}

function validateAssignments(records, repositoryById, taxonomy, expectedCount, sourcePath) {
	if (records.length !== expectedCount) throw new BuilderError(`assignment ledger has ${records.length} records; expected ${expectedCount}`);
	const seen = new Set();
	const byRepo = new Map();
	for (const [index, record] of records.entries()) {
		const source = `${sourcePath}:${index + 1}`;
		validateRepoId(record?.repo_id, "repo_id", source);
		if (!repositoryById.has(record.repo_id)) throw new BuilderError(`${source} references a repo absent from the repository manifest: ${record.repo_id}`);
		if (typeof record.area !== "string" || typeof record.family !== "string" || !taxonomy.paths.has(`${record.area}\0${record.family}`)) throw new BuilderError(`${source} contains an invalid taxonomy path`);
		if (!new Set(["high", "medium", "low"]).has(record.confidence)) throw new BuilderError(`${source}.confidence must be high, medium, or low`);
		const key = `${record.repo_id}\0${record.area}\0${record.family}`;
		if (seen.has(key)) throw new BuilderError(`${source} duplicates assignment ${record.repo_id} -> ${record.area} -> ${record.family}`);
		seen.add(key);
		if (!byRepo.has(record.repo_id)) byRepo.set(record.repo_id, []);
		byRepo.get(record.repo_id).push({ area: record.area, family: record.family, confidence: record.confidence });
	}
	for (const repoId of repositoryById.keys()) if (!byRepo.has(repoId)) throw new BuilderError(`classified repository has no taxonomy assignment: ${repoId}`);
	for (const assignments of byRepo.values()) assignments.sort((left, right) => taxonomy.order.get(`${left.area}\0${left.family}`) - taxonomy.order.get(`${right.area}\0${right.family}`));
	return byRepo;
}

function validateSourceManifest(records, repositoryById, assignmentByRepo, sourceManifestPath, sourceRoot, taxonomy) {
	if (records.length !== repositoryById.size) throw new BuilderError(`source import manifest has ${records.length} records; expected ${repositoryById.size}`);
	const byRepo = new Map();
	const bySkill = new Map();
	const bySourceUrl = new Map();
	const bySourcePath = new Map();
	for (const [index, record] of records.entries()) {
		const source = `${sourceManifestPath}:${index + 1}`;
		validateRepoId(record?.repo_id, "repo_id", source);
		if (!repositoryById.has(record.repo_id)) throw new BuilderError(`${source} repo_id is not in the repository manifest: ${record.repo_id}`);
		if (byRepo.has(record.repo_id)) throw new BuilderError(`${source} duplicates repo_id ${record.repo_id}`);
		if (typeof record.skill_id !== "string" || !SKILL_ID.test(record.skill_id)) throw new BuilderError(`${source}.skill_id must be a canonical lowercase-hyphen id`);
		if (bySkill.has(record.skill_id)) throw new BuilderError(`${source} duplicates skill_id ${record.skill_id}`);
		validateGithubUrl(record.source_url, source);
		if (normalizedRepoFromGithubUrl(record.source_url) !== record.repo_id.toLowerCase()) throw new BuilderError(`${source}.source_url does not identify ${record.repo_id}`);
		const normalizedSourceUrl = record.source_url.trim().replace(/\.git\/?$/i, "").replace(/\/$/, "").toLowerCase();
		if (bySourceUrl.has(normalizedSourceUrl)) throw new BuilderError(`${source} duplicates source_url used by ${bySourceUrl.get(normalizedSourceUrl)}`);
		const sourcePath = sourcePathFor(record, sourceManifestPath, sourceRoot);
		if (!realDirectory(sourcePath)) throw new BuilderError(`${source} source_skill_root does not resolve to a real directory: ${sourcePath}`);
		if (bySourcePath.has(sourcePath)) throw new BuilderError(`${source} reuses source skill root from ${bySourcePath.get(sourcePath)}`);
		if (!regularFile(path.join(sourcePath, "SKILL.md"))) throw new BuilderError(`${source} source_skill_root is missing SKILL.md: ${sourcePath}`);
		if (record.source_commit !== null && record.source_commit !== undefined && (typeof record.source_commit !== "string" || !/^[0-9a-f]{40}$/i.test(record.source_commit))) throw new BuilderError(`${source}.source_commit must be null or a 40-hex commit`);
		if (record.legacy_repo_id !== undefined && (typeof record.legacy_repo_id !== "string" || !record.legacy_repo_id.trim())) throw new BuilderError(`${source}.legacy_repo_id must be a non-empty string when provided`);
		if (typeof record.source_skill_root === "string" && path.isAbsolute(expandHome(record.source_skill_root))) throw new BuilderError(`${source}.source_skill_root must be repository-relative; put its checkout in source_checkout`);
		if (record.aliases !== undefined && (!Array.isArray(record.aliases) || record.aliases.some((alias) => typeof alias !== "string"))) throw new BuilderError(`${source}.aliases must be an array of strings when provided`);
		byRepo.set(record.repo_id, { ...record, sourcePath });
		bySkill.set(record.skill_id, record.repo_id);
		bySourceUrl.set(normalizedSourceUrl, record.repo_id);
		bySourcePath.set(sourcePath, record.repo_id);
		validateSourceMetadata(sourcePath, record, assignmentByRepo.get(record.repo_id), taxonomy);
	}
	for (const repoId of repositoryById.keys()) if (!byRepo.has(repoId)) throw new BuilderError(`source import manifest is missing repository: ${repoId}`);
	return byRepo;
}

function copyTemplate(templateDir, outputDir) {
	if (!realDirectory(templateDir)) throw new BuilderError(`router template is not a real directory: ${templateDir}`);
	if (!regularFile(path.join(templateDir, "SKILL.md"))) throw new BuilderError(`router template is missing SKILL.md: ${templateDir}`);
	copyTree(templateDir, outputDir);
}

function runRouterUpdater(libraryRoot, templateDir, environment) {
	if (!regularFile(ROUTER_UPDATER)) throw new BuilderError(`router updater is missing: ${ROUTER_UPDATER}`);
	const result = spawnSync(process.execPath, [ROUTER_UPDATER, "--library-root", libraryRoot, "--template-dir", templateDir, "--router-visibility", "enabled"], {
		encoding: "utf8",
		env: { ...process.env, ...environment },
	});
	if (result.stdout) process.stdout.write(result.stdout);
	if (result.stderr) process.stderr.write(result.stderr);
	if (result.error) throw result.error;
	if (result.status !== 0) throw new BuilderError(`router updater failed with exit code ${result.status ?? 1}`);
}

function validateOutput(outputDir, repositoryById, assignmentByRepo, expectedAssignments) {
	const repoSkillsRoot = path.join(outputDir, "repo-skills");
	const routerDir = path.join(outputDir, "repo-skills-router");
	const roots = fs.readdirSync(repoSkillsRoot, { withFileTypes: true }).filter((entry) => entry.isDirectory() && regularFile(path.join(repoSkillsRoot, entry.name, "SKILL.md")));
	if (roots.length !== repositoryById.size) throw new BuilderError(`staged collection has ${roots.length} direct skill roots; expected ${repositoryById.size}`);
	const repositoryIndex = readRecords(path.join(repoSkillsRoot, "repository-index.jsonl"), "generated repository index");
	const assignmentIndex = readRecords(path.join(routerDir, "references", "index", "assignments.jsonl"), "generated assignment index");
	const taxonomyFile = path.join(routerDir, "references", "index", "taxonomy.json");
	if (!regularFile(taxonomyFile) || createHash("sha256").update(fs.readFileSync(taxonomyFile)).digest("hex") !== TAXONOMY_SHA256) throw new BuilderError("generated taxonomy does not match the canonical taxonomy hash");
	if (repositoryIndex.length !== repositoryById.size) throw new BuilderError(`generated repository index has ${repositoryIndex.length} rows; expected ${repositoryById.size}`);
	if (assignmentIndex.length !== expectedAssignments) throw new BuilderError(`generated assignment index has ${assignmentIndex.length} rows; expected ${expectedAssignments}`);
	const metadata = readJson(path.join(routerDir, "references", "index", "build-metadata.json"));
	if (metadata.repository_count !== repositoryById.size || metadata.assignment_count !== expectedAssignments || metadata.taxonomy_sha256 !== TAXONOMY_SHA256) throw new BuilderError("generated router build metadata does not match the validated collection scope");
	const repositoryIndexByRepo = new Map(repositoryIndex.map((record) => [record.repo_id, record]));
	const repositoryIds = new Set();
	const foldedRepositoryIds = new Set();
	for (const record of repositoryIndex) {
		const unknownField = Object.keys(record).find((key) => !new Set([
			"schema_version", "repo_id", "legacy_repo_id", "repo_name", "skill_id", "source_url",
			"source_commit", "source_skill_root", "target_skill_root", "aliases", "content_sha256", "description",
		]).has(key));
		if (unknownField) throw new BuilderError(`generated repository index contains unknown field ${unknownField}`);
		if (!repositoryById.has(record.repo_id) || !regularFile(path.join(repoSkillsRoot, record.skill_id, "SKILL.md"))) throw new BuilderError(`generated repository index contains an invalid or missing skill: ${record.repo_id} -> ${record.skill_id}`);
		if (record.schema_version !== 1 || typeof record.repo_id !== "string" || !REPO_ID.test(record.repo_id) || record.repo_name !== record.repo_id.split("/").at(-1)) throw new BuilderError(`generated repository index contains invalid identity: ${record.repo_id}`);
		if (record.legacy_repo_id !== null && (typeof record.legacy_repo_id !== "string" || !record.legacy_repo_id.trim())) throw new BuilderError(`generated repository index contains an invalid legacy_repo_id: ${record.repo_id}`);
		if (record.source_commit !== null && (typeof record.source_commit !== "string" || !/^[0-9a-f]{40}$/i.test(record.source_commit))) throw new BuilderError(`generated repository index contains an invalid source_commit: ${record.repo_id}`);
		if (record.source_skill_root !== null && (typeof record.source_skill_root !== "string" || path.isAbsolute(record.source_skill_root))) throw new BuilderError(`generated repository index contains an invalid source_skill_root: ${record.repo_id}`);
		if (!Array.isArray(record.aliases) || record.aliases.some((alias) => typeof alias !== "string")) throw new BuilderError(`generated repository index contains invalid aliases: ${record.repo_id}`);
		if (typeof record.content_sha256 !== "string" || !/^sha256:[0-9a-f]{64}$/i.test(record.content_sha256) || typeof record.description !== "string" || !record.description.trim()) throw new BuilderError(`generated repository index contains invalid content metadata: ${record.repo_id}`);
		const foldedRepoId = record.repo_id.toLowerCase();
		if (repositoryIds.has(record.repo_id) || foldedRepositoryIds.has(foldedRepoId)) throw new BuilderError(`generated repository index contains duplicate repo_id: ${record.repo_id}`);
		repositoryIds.add(record.repo_id);
		foldedRepositoryIds.add(foldedRepoId);
	}
	for (const record of assignmentIndex) {
		const unknownField = Object.keys(record).find((key) => !new Set(["repo_id", "legacy_repo_id", "skill_id", "area", "family", "confidence"]).has(key));
		if (unknownField) throw new BuilderError(`generated assignment index contains unknown field ${unknownField}`);
		const repository = repositoryIndexByRepo.get(record.repo_id);
		if (!repository || record.skill_id !== repository.skill_id || record.legacy_repo_id !== repository.legacy_repo_id) throw new BuilderError(`generated assignment index contains stale repository identity: ${record.repo_id}`);
		if (!new Set(["high", "medium", "low"]).has(record.confidence)) throw new BuilderError(`generated assignment index contains invalid confidence: ${record.repo_id}`);
	}
	const actualAssignments = new Set(assignmentIndex.map((record) => `${record.repo_id}\0${record.area}\0${record.family}`));
	const expected = new Set([...assignmentByRepo.entries()].flatMap(([repoId, assignments]) => assignments.map((assignment) => `${repoId}\0${assignment.area}\0${assignment.family}`)));
	if (actualAssignments.size !== expected.size || [...expected].some((key) => !actualAssignments.has(key))) throw new BuilderError("generated assignment index does not match the validated assignment ledger");
}

function parseArgs(argv) {
	const args = {
		sourceManifest: undefined,
		repositoryManifest: undefined,
		assignments: undefined,
		taxonomy: undefined,
		outputDir: undefined,
		templateDir: BUNDLED_TEMPLATE,
		sourceRoot: undefined,
		expectedRepositories: DEFAULT_EXPECTED_REPOSITORIES,
		expectedAssignments: DEFAULT_EXPECTED_ASSIGNMENTS,
		routerRunId: undefined,
	};
	const required = new Set(["--source-manifest", "--repository-manifest", "--assignments", "--taxonomy", "--output-dir"]);
	for (let index = 0; index < argv.length; index += 1) {
		const item = argv[index];
		if (item === "--source-manifest") args.sourceManifest = argv[++index];
		else if (item === "--repository-manifest") args.repositoryManifest = argv[++index];
		else if (item === "--assignments") args.assignments = argv[++index];
		else if (item === "--taxonomy") args.taxonomy = argv[++index];
		else if (item === "--output-dir") args.outputDir = argv[++index];
		else if (item === "--template-dir") args.templateDir = argv[++index];
		else if (item === "--source-root") args.sourceRoot = argv[++index];
		else if (item === "--expected-repositories") args.expectedRepositories = Number(argv[++index]);
		else if (item === "--expected-assignments") args.expectedAssignments = Number(argv[++index]);
		else if (item === "--source-router-run-id") args.routerRunId = argv[++index];
		else if (item === "-h" || item === "--help") {
			printHelp();
			process.exit(0);
		} else throw new BuilderError(`unknown argument: ${item}`);
	}
	for (const option of required) {
		const value = option === "--source-manifest" ? args.sourceManifest : option === "--repository-manifest" ? args.repositoryManifest : option === "--assignments" ? args.assignments : option === "--taxonomy" ? args.taxonomy : args.outputDir;
		if (!value) throw new BuilderError(`${option} is required`);
	}
	if (!Number.isInteger(args.expectedRepositories) || args.expectedRepositories < 1) throw new BuilderError("--expected-repositories must be a positive integer");
	if (!Number.isInteger(args.expectedAssignments) || args.expectedAssignments < 1) throw new BuilderError("--expected-assignments must be a positive integer");
	return args;
}

function printHelp() {
	console.log(`Usage: node build_repo_skills_collection.mjs [options]

Required:
  --source-manifest FILE       JSONL/JSON mapping repo_id to source skill roots and skill_id
  --repository-manifest FILE   Terminal classified repository manifest
  --assignments FILE            Final area-family assignment ledger (JSONL/JSON)
  --taxonomy FILE               Canonical taxonomy JSON
  --output-dir DIR              New staged library root containing repo-skills/

Optional:
  --template-dir DIR            Empty bundled repo-skills-router template
  --source-root DIR             Base for relative source_skill_root values
  --expected-repositories N     Expected repository count (default: 1000)
  --expected-assignments N      Expected membership count (default: 2186)
  --source-router-run-id ID     Recorded in generated build metadata

Each source manifest record must contain repo_id, skill_id, source_url,
source_skill_root, and optionally source_checkout/source_commit/aliases. The
builder creates a fresh staging tree and never overwrites an existing output.`);
}

function build(args) {
	const sourceManifestPath = path.resolve(expandHome(args.sourceManifest));
	const repositoryManifestPath = path.resolve(expandHome(args.repositoryManifest));
	const assignmentsPath = path.resolve(expandHome(args.assignments));
	const taxonomyPath = path.resolve(expandHome(args.taxonomy));
	const templateDir = path.resolve(expandHome(args.templateDir));
	const outputDir = path.resolve(expandHome(args.outputDir));
	const sourceRoot = args.sourceRoot ? path.resolve(expandHome(args.sourceRoot)) : undefined;
	if (exists(outputDir)) throw new BuilderError(`output directory already exists; refusing to overwrite: ${outputDir}`);
	if (!regularFile(taxonomyPath)) throw new BuilderError(`taxonomy does not exist as a regular file: ${taxonomyPath}`);
	if (fs.readFileSync(taxonomyPath).length === 0) throw new BuilderError(`taxonomy is empty: ${taxonomyPath}`);
	const taxonomyHash = createHash("sha256").update(fs.readFileSync(taxonomyPath)).digest("hex");
	if (taxonomyHash !== TAXONOMY_SHA256) throw new BuilderError(`taxonomy hash ${taxonomyHash} does not match the canonical ${TAXONOMY_SHA256}`);
	const taxonomy = normalizeTaxonomy(readJson(taxonomyPath), taxonomyPath);
	const repositoryRecords = readRecords(repositoryManifestPath, "repository manifest");
	const repositoryById = validateRepositoryManifest(repositoryRecords, args.expectedRepositories, repositoryManifestPath);
	const assignmentRecords = readRecords(assignmentsPath, "assignment ledger");
	const assignmentByRepo = validateAssignments(assignmentRecords, repositoryById, taxonomy, args.expectedAssignments, assignmentsPath);
	const sourceRecords = readRecords(sourceManifestPath, "source import manifest");
	const sourceByRepo = validateSourceManifest(sourceRecords, repositoryById, assignmentByRepo, sourceManifestPath, sourceRoot, taxonomy);
	const temporaryParent = path.dirname(outputDir);
	fs.mkdirSync(temporaryParent, { recursive: true });
	const temporaryDir = fs.mkdtempSync(path.join(temporaryParent, `.repo-skills-build-${process.pid}-`));
	try {
		const repoSkillsRoot = path.join(temporaryDir, "repo-skills");
		const routerDir = path.join(temporaryDir, "repo-skills-router");
		fs.mkdirSync(repoSkillsRoot, { recursive: true });
		copyTemplate(templateDir, routerDir);
		const repositoryIndex = [];
		for (const [repoId, source] of [...sourceByRepo.entries()].sort(([left], [right]) => left.localeCompare(right))) {
			const targetRoot = path.join(repoSkillsRoot, source.skill_id);
			normalizeSkillGraph(source.sourcePath, targetRoot, source.skill_id);
			validateRuntimePrivacy(targetRoot, source);
			validateSourceMetadata(targetRoot, source, assignmentByRepo.get(repoId), taxonomy);
			writeRoutingMetadata(targetRoot, source, assignmentByRepo.get(repoId));
			const contentSha256 = treeDigest(targetRoot);
			repositoryIndex.push({
				schema_version: 1,
				repo_id: source.repo_id,
				legacy_repo_id: typeof source.legacy_repo_id === "string" ? source.legacy_repo_id : null,
			repo_name: source.repo_name || source.repo_id.split("/").at(-1),
			skill_id: source.skill_id,
				source_url: source.source_url.replace(/\.git\/?$/i, "").replace(/\/$/, ""),
				source_commit: source.source_commit ? source.source_commit.toLowerCase() : null,
				source_skill_root: source.source_skill_root,
				target_skill_root: `repo-skills/${source.skill_id}`,
			aliases: Array.isArray(source.aliases) ? [...new Set(source.aliases)].sort() : [],
			content_sha256: contentSha256,
			description: parseFrontmatter(path.join(targetRoot, "SKILL.md")).frontmatter.description,
		});
		}
		writeJsonLines(path.join(repoSkillsRoot, "repository-index.jsonl"), repositoryIndex.sort((left, right) => left.repo_id.localeCompare(right.repo_id) || left.skill_id.localeCompare(right.skill_id)));
		fs.mkdirSync(path.join(routerDir, "references", "index"), { recursive: true });
		fs.writeFileSync(path.join(routerDir, "references", "index", "taxonomy.json"), stableJson(taxonomy), "utf8");
		const repositoryByRepoId = new Map(repositoryIndex.map((record) => [record.repo_id, record]));
		const centralAssignments = [...assignmentByRepo.entries()].flatMap(([repoId, assignments]) => assignments.map((assignment) => ({
			repo_id: repoId,
			legacy_repo_id: repositoryByRepoId.get(repoId)?.legacy_repo_id ?? null,
			skill_id: repositoryByRepoId.get(repoId)?.skill_id,
			area: assignment.area,
			family: assignment.family,
			confidence: assignment.confidence,
		})));
		writeJsonLines(path.join(routerDir, "references", "index", "assignments.jsonl"), centralAssignments);
		const environment = {};
		if (args.routerRunId) environment.DISCO_ROUTER_SOURCE_RUN_ID = args.routerRunId;
		runRouterUpdater(temporaryDir, templateDir, environment);
		validateOutput(temporaryDir, repositoryById, assignmentByRepo, args.expectedAssignments);
		fs.renameSync(temporaryDir, outputDir);
		console.log(`built staged repository skill collection at ${outputDir}: ${repositoryById.size} repositories, ${args.expectedAssignments} assignments`);
	} catch (error) {
		fs.rmSync(temporaryDir, { recursive: true, force: true });
		throw error;
	}
}

function main(argv) {
	try {
		build(parseArgs(argv));
		return 0;
	} catch (error) {
		console.error(`build_repo_skills_collection.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return error instanceof BuilderError ? 2 : 1;
	}
}

process.exitCode = main(process.argv.slice(2));
