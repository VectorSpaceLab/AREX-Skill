import { spawnSync } from "node:child_process";
import { lstat, readFile, readdir, stat } from "node:fs/promises";
import { dirname, extname, isAbsolute, join, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { lexer, walkTokens } from "marked";

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const runtimeSourceRoot = join(packageRoot, "packages", "coding-agent", "src");
const failures = [];

function check(condition, message) {
	if (!condition) failures.push(message);
}

async function readJson(path) {
	return JSON.parse(await readFile(path, "utf8"));
}

async function pathExists(path) {
	try {
		await stat(path);
		return true;
	} catch (error) {
		if (error?.code === "ENOENT") return false;
		throw error;
	}
}

async function walkFiles(path) {
	const result = [];
	for (const entry of await readdir(path, { withFileTypes: true })) {
		const entryPath = join(path, entry.name);
		if (entry.isDirectory()) result.push(...(await walkFiles(entryPath)));
		else if (entry.isFile() || entry.isSymbolicLink()) result.push(entryPath);
	}
	return result;
}

function displayPath(path) {
	return relative(packageRoot, path).replaceAll("\\", "/");
}

const packageJsonPath = join(packageRoot, "package.json");
const packageJson = await readJson(packageJsonPath);
const changelog = await readFile(join(packageRoot, "CHANGELOG.md"), "utf8");

check(packageJson.private === undefined, "package.json must not contain a private field");
check(packageJson.name === "@auto-ml-skills/disco", "package name must be @auto-ml-skills/disco");
check(packageJson.version === "0.2.0", "package version must be 0.2.0");
const escapedPackageVersion = packageJson.version.replaceAll(".", "\\.");
check(
	new RegExp(`^## \\[?${escapedPackageVersion}\\]? - \\d{4}-\\d{2}-\\d{2}$`, "mu").test(changelog),
	`CHANGELOG.md must contain a dated release heading for ${packageJson.version}`,
);
check(packageJson.publishConfig?.access === "public", "publishConfig.access must be public");
check(packageJson.bin?.disco === "dist/cli.js", "the only supported CLI must be disco -> dist/cli.js");
check(Object.keys(packageJson.bin ?? {}).length === 1, "package must publish exactly one CLI executable");
check(packageJson.repository?.directory === "cli", "repository.directory must identify the cli package root");
check(packageJson.exports?.["."]?.import === "./dist/index.js", "root ESM export is missing");
check(packageJson.exports?.["."]?.types === "./dist/index.d.ts", "root type export is missing");
check(packageJson.exports?.["./rpc-entry"]?.import === "./dist/rpc-entry.js", "RPC ESM export is missing");
check(packageJson.dependencies?.["@earendil-works/pi-coding-agent"] === undefined, "DisCo must not depend on pi-coding-agent");

for (const name of ["@earendil-works/pi-agent-core", "@earendil-works/pi-ai", "@earendil-works/pi-tui"]) {
	check(packageJson.dependencies?.[name] === "0.83.0", `${name} must be pinned to 0.83.0`);
	const installedManifest = join(packageRoot, "node_modules", ...name.split("/"), "package.json");
	if (await pathExists(installedManifest)) {
		check((await readJson(installedManifest)).version === "0.83.0", `${name} installed version must be 0.83.0`);
	} else {
		failures.push(`${name} is not installed; run npm ci before verification`);
	}
}

for (const [name, value] of Object.entries({
	...(packageJson.dependencies ?? {}),
	...(packageJson.optionalDependencies ?? {}),
})) {
	check(!/^(?:file|link):/u.test(value), `${name} must not use a local ${value} dependency`);
}

check(await pathExists(join(packageRoot, "npm-shrinkwrap.json")), "npm-shrinkwrap.json must lock the published install tree");

const requiredBuildFiles = [
	"dist/cli.js",
	"dist/index.js",
	"dist/index.d.ts",
	"dist/rpc-entry.js",
	"dist/cli/repo-skills.js",
	"dist/core/repo-skills-library-manager.js",
	"dist/core/oauth/anthropic.js",
	"dist/core/oauth/openai-codex.js",
	"dist/core/oauth/openrouter.js",
	"dist/disco-resources/skills/README.md",
	"dist/disco-resources/skills/distill-ml-knowledge/SKILL.md",
	"dist/disco-resources/skills/distill-ml-knowledge/references/task-and-construction-contract.md",
	"dist/disco-resources/skills/distill-ml-knowledge/references/path-selection-and-adequacy.md",
	"dist/disco-resources/skills/distill-ml-knowledge/references/direct-construction-and-handoff.md",
	"dist/disco-resources/skills/distill-ml-knowledge/scripts/import_operating_skill_graph.mjs",
	"dist/disco-resources/skills/design-meta-skill/SKILL.md",
	"dist/disco-resources/skills/design-meta-skill/references/reusable-bundle-specification.md",
	"dist/disco-resources/skills/design-meta-skill/references/generation-verification-and-review.md",
	"dist/disco-resources/skills/verify-repo-skill/scripts/import_repo_skill.mjs",
	"dist/disco-resources/skills/verify-repo-skill/scripts/update_repo_skills_router.mjs",
	"dist/disco-resources/skills/verify-repo-skill/scripts/with_import_lock.mjs",
	"README.md",
	"CHANGELOG.md",
	"LICENSE",
	"THIRD_PARTY_NOTICES.md",
	"docs/index.md",
	"docs/sdk.md",
	"examples/README.md",
];
for (const path of requiredBuildFiles) {
	check(await pathExists(join(packageRoot, path)), `required build/package file is missing: ${path}`);
}

const sourceFiles = await walkFiles(runtimeSourceRoot);
const publishableSourceFiles = [
	...sourceFiles,
	...(await walkFiles(join(packageRoot, "docs"))),
	...(await walkFiles(join(packageRoot, "examples"))),
	packageJsonPath,
	join(packageRoot, "README.md"),
	join(packageRoot, "CHANGELOG.md"),
	join(packageRoot, "THIRD_PARTY_NOTICES.md"),
];

const textExtensions = new Set([".css", ".d.ts", ".html", ".js", ".json", ".map", ".md", ".mjs", ".ts", ".txt"]);
const localProxy = "127.0.0.1:7890";
const fictitiousService = /https?:\/\/(?:www\.)?disco\.dev\b/u;
const unownedDiscoRepository = /(?:github\.com|raw\.githubusercontent\.com)\/earendil-works\/disco\b/u;
const staleUpstreamRepository = /github\.com\/earendil-works\/pi-mono\b/u;
const stalePiBranding = ["Pi Coding Agent Theme", "Theme schema for Pi coding agent", "pi has joined Earendil"];

for (const path of publishableSourceFiles) {
	if (!textExtensions.has(extname(path)) && !path.endsWith(".d.ts")) continue;
	const content = await readFile(path, "utf8");
	check(!content.includes(localProxy), `${displayPath(path)} contains the local validation proxy`);
	check(!fictitiousService.test(content), `${displayPath(path)} contains an unowned disco.dev URL`);
	check(!unownedDiscoRepository.test(content), `${displayPath(path)} contains an unowned DisCo repository URL`);
	check(!staleUpstreamRepository.test(content), `${displayPath(path)} contains the stale upstream repository URL`);
	for (const branding of stalePiBranding) {
		check(!content.includes(branding), `${displayPath(path)} contains stale Pi branding: ${branding}`);
	}
}

for (const path of [
	"packages/coding-agent/src/modes/interactive/components/earendil-announcement.ts",
	"packages/coding-agent/src/modes/interactive/assets/clankolas.png",
]) {
	check(!(await pathExists(join(packageRoot, path))), `excluded upstream announcement resource is present: ${path}`);
}

for (const path of sourceFiles.filter((entry) => entry.endsWith(".ts"))) {
	const content = await readFile(path, "utf8");
	const shown = displayPath(path);
	check(!/["'`]~?\/?\.pi(?:\/|["'`])/u.test(content), `${shown} contains a Pi filesystem default`);
	check(!/Symbol\.for\(["']@(?:earendil-works|mariozechner)\/pi-coding-agent:/u.test(content), `${shown} shares a Pi global Symbol`);
	check(!/(?:from\s+|import\s*\()\s*["']@(?:earendil-works|mariozechner)\/pi-coding-agent/u.test(content), `${shown} imports external pi-coding-agent`);
	if (!path.endsWith("/cli/pi-environment-isolation.ts")) {
		check(!/\bPI_[A-Z0-9_]+\b/u.test(content), `${shown} reads or embeds a Pi-owned environment variable outside the isolation allowlist`);
	}
}

const packageManagerCli = await readFile(join(runtimeSourceRoot, "package-manager-cli.ts"), "utf8");
check(!packageManagerCli.includes("@earendil-works/pi-coding-agent"), "self-update code still targets pi-coding-agent");
check(packageManagerCli.includes("installSpec: `${PACKAGE_NAME}@latest`"), "self-update must derive its target from DisCo PACKAGE_NAME");

const packageManagerSource = await readFile(join(runtimeSourceRoot, "core", "package-manager.ts"), "utf8");
for (const name of ["@juicesharp/rpiv-ask-user-question", "@juicesharp/rpiv-todo", "pi-subagents"]) {
	check(packageManagerSource.includes(JSON.stringify(`npm:${name}`)), `default extension package is missing: ${name}`);
}

const builtDiscoResourceFiles = await walkFiles(join(packageRoot, "dist", "disco-resources"));
const markdownFiles = [...publishableSourceFiles, ...builtDiscoResourceFiles].filter((path) => path.endsWith(".md"));
for (const markdownPath of markdownFiles) {
	const markdown = await readFile(markdownPath, "utf8");
	const links = [];
	walkTokens(lexer(markdown), (token) => {
		if ((token.type === "link" || token.type === "image") && typeof token.href === "string") {
			links.push(token.href);
		}
	});

	for (const originalHref of links) {
		if (/^(?:[a-z][a-z0-9+.-]*:|#|\/\/)/iu.test(originalHref)) continue;
		const hrefWithoutFragment = originalHref.split("#", 1)[0]?.split("?", 1)[0] ?? "";
		if (!hrefWithoutFragment) continue;
		let decodedHref = hrefWithoutFragment;
		try {
			decodedHref = decodeURIComponent(hrefWithoutFragment);
		} catch {
			failures.push(`${displayPath(markdownPath)} has an invalid encoded link: ${originalHref}`);
			continue;
		}
		const target = isAbsolute(decodedHref)
			? resolve(packageRoot, `.${decodedHref}`)
			: resolve(dirname(markdownPath), decodedHref);
		const targetRelative = relative(packageRoot, target);
		if (targetRelative.startsWith("..") || isAbsolute(targetRelative)) {
			failures.push(`${displayPath(markdownPath)} links outside the package: ${originalHref}`);
			continue;
		}
		check(await pathExists(target), `${displayPath(markdownPath)} has a broken local link: ${originalHref}`);
	}
}

const packResult = spawnSync("npm", ["pack", "--dry-run", "--json", "--ignore-scripts"], {
	cwd: packageRoot,
	encoding: "utf8",
});
if (packResult.error) throw packResult.error;
if (packResult.status !== 0) {
	throw new Error(`npm pack --dry-run failed:\n${packResult.stderr || packResult.stdout}`);
}
const packReport = JSON.parse(packResult.stdout)[0];
check(packReport?.name === packageJson.name && packReport?.version === packageJson.version, "npm pack identity does not match package.json");
const packedEntries = packReport?.files ?? [];
const packedPaths = new Set(packedEntries.map((entry) => entry.path));

for (const path of requiredBuildFiles) check(packedPaths.has(path), `npm tarball is missing ${path}`);
check(packedPaths.has("package.json"), "npm tarball is missing package.json");
check(packedPaths.has("npm-shrinkwrap.json"), "npm tarball is missing npm-shrinkwrap.json");

for (const entry of packedEntries) {
	const packedPath = entry.path.replaceAll("\\", "/");
	check(!packedPath.startsWith("packages/"), `npm tarball leaks internal package source: ${packedPath}`);
	check(!packedPath.startsWith("node_modules/"), `npm tarball leaks node_modules: ${packedPath}`);
	check(!packedPath.startsWith("scripts/"), `npm tarball leaks release scripts: ${packedPath}`);
	check(!packedPath.startsWith("discard"), `npm tarball leaks discarded implementations: ${packedPath}`);
	check(!/(?:^|\/)dist\/.*\.test\.(?:d\.ts|js|map)$/u.test(packedPath), `npm tarball contains compiled tests: ${packedPath}`);
	const diskPath = join(packageRoot, packedPath);
	if (await pathExists(diskPath)) {
		check(!(await lstat(diskPath)).isSymbolicLink(), `npm tarball contains a source link: ${packedPath}`);
		if (textExtensions.has(extname(diskPath)) || diskPath.endsWith(".d.ts")) {
			const content = await readFile(diskPath, "utf8");
			check(!content.includes(localProxy), `npm tarball file contains the local validation proxy: ${packedPath}`);
			check(!fictitiousService.test(content), `npm tarball file contains an unowned disco.dev URL: ${packedPath}`);
			check(
				!unownedDiscoRepository.test(content),
				`npm tarball file contains an unowned DisCo repository URL: ${packedPath}`,
			);
			check(
				!staleUpstreamRepository.test(content),
				`npm tarball file contains the stale upstream repository URL: ${packedPath}`,
			);
			for (const branding of stalePiBranding) {
				check(!content.includes(branding), `npm tarball file contains stale Pi branding (${branding}): ${packedPath}`);
			}
		}
	}
}

const previousPackageDir = process.env.DISCO_PACKAGE_DIR;
delete process.env.DISCO_PACKAGE_DIR;
try {
	const rpcClientModule = await import(
		`${pathToFileURL(join(packageRoot, "dist", "modes", "rpc", "rpc-client.js")).href}?verify=${Date.now()}`
	);
	check(
		rpcClientModule.resolveRpcCliPath() === join(packageRoot, "dist", "cli.js"),
		"RpcClient default CLI path must resolve inside the installed DisCo package",
	);

	const systemPromptModule = await import(`${pathToFileURL(join(packageRoot, "dist", "core", "system-prompt.js")).href}?verify=${Date.now()}`);
	const prompt = systemPromptModule.buildSystemPrompt({ cwd: packageRoot });
	const pathMatches = [
		/^- Main documentation: (.+)$/mu.exec(prompt)?.[1],
		/^- Additional docs: (.+)$/mu.exec(prompt)?.[1],
		/^- Examples: (.+?) \(extensions,/mu.exec(prompt)?.[1],
	];
	for (const promptPath of pathMatches) {
		check(typeof promptPath === "string", "built system prompt is missing a documentation path");
		if (!promptPath) continue;
		const resolvedPath = resolve(promptPath);
		const promptRelative = relative(packageRoot, resolvedPath).replaceAll("\\", "/");
		check(!promptRelative.startsWith("..") && !isAbsolute(promptRelative), `system prompt path escapes the package: ${promptPath}`);
		check(await pathExists(resolvedPath), `system prompt path does not exist: ${promptPath}`);
		const info = await stat(resolvedPath).catch(() => undefined);
		check(
			info?.isDirectory()
				? [...packedPaths].some((path) => path.startsWith(`${promptRelative}/`))
				: packedPaths.has(promptRelative),
			`system prompt path is not in the npm tarball: ${promptPath}`,
		);
	}
} finally {
	if (previousPackageDir === undefined) delete process.env.DISCO_PACKAGE_DIR;
	else process.env.DISCO_PACKAGE_DIR = previousPackageDir;
}

if (failures.length > 0) {
	throw new Error(`Package verification failed:\n- ${failures.join("\n- ")}`);
}

console.log(`Verified ${packedEntries.length} packed files for ${packageJson.name}@${packageJson.version}.`);
