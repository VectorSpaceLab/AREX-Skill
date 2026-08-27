import { chmodSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import { delimiter, join } from "path";
import { afterEach, describe, expect, test } from "vitest";
import {
	detectInstallMethod,
	getShareViewerUrl,
	getSelfUpdateCommand,
	getSelfUpdateUnavailableInstruction,
	getUpdateInstruction,
} from "../src/config.ts";

const execPathDescriptor = Object.getOwnPropertyDescriptor(process, "execPath");
const originalPath = process.env.PATH;
const originalDiscoPackageDir = process.env.DISCO_PACKAGE_DIR;
const originalShareViewerUrl = process.env.DISCO_SHARE_VIEWER_URL;
const originalArgv1 = process.argv[1];
let tempDir: string | undefined;

function setExecPath(value: string): void {
	Object.defineProperty(process, "execPath", {
		value,
		configurable: true,
	});
}

afterEach(() => {
	if (execPathDescriptor) {
		Object.defineProperty(process, "execPath", execPathDescriptor);
	}
	if (originalPath === undefined) {
		delete process.env.PATH;
	} else {
		process.env.PATH = originalPath;
	}
	if (originalDiscoPackageDir === undefined) {
		delete process.env.DISCO_PACKAGE_DIR;
	} else {
		process.env.DISCO_PACKAGE_DIR = originalDiscoPackageDir;
	}
	if (originalShareViewerUrl === undefined) {
		delete process.env.DISCO_SHARE_VIEWER_URL;
	} else {
		process.env.DISCO_SHARE_VIEWER_URL = originalShareViewerUrl;
	}
	if (originalArgv1 === undefined) {
		process.argv.splice(1, 1);
	} else {
		process.argv[1] = originalArgv1;
	}
	if (tempDir) {
		chmodSync(tempDir, 0o700);
		rmSync(tempDir, { recursive: true, force: true });
		tempDir = undefined;
	}
});

describe("getShareViewerUrl", () => {
	test("uses the public gist URL by default", () => {
		delete process.env.DISCO_SHARE_VIEWER_URL;
		expect(getShareViewerUrl("abc123")).toBe("https://gist.github.com/abc123");
	});

	test("keeps hash routing for a configured share viewer", () => {
		process.env.DISCO_SHARE_VIEWER_URL = "https://viewer.example/disco#";
		expect(getShareViewerUrl("abc123")).toBe("https://viewer.example/disco#abc123");
	});
});

function createNpmPrefixInstall(template = "disco-prefix-"): { prefix: string; packageDir: string } {
	const prefix = mkdtempSync(join(tmpdir(), template));
	const root = join(prefix, "lib", "node_modules");
	const scopeDir = join(root, "@auto-ml-skills");
	const packageDir = join(scopeDir, "disco");
	mkdirSync(packageDir, { recursive: true });
	tempDir = prefix;
	process.env.DISCO_PACKAGE_DIR = packageDir;
	setExecPath(join(packageDir, "dist", "cli.js"));
	return { prefix, packageDir };
}

function createPnpmGlobalInstall(): { root: string; packageDir: string } {
	const temp = mkdtempSync(join(tmpdir(), "disco-pnpm-"));
	const binDir = join(temp, "bin");
	const root = join(temp, "pnpm", "global", "5", "node_modules");
	const packageDir = join(root, "@auto-ml-skills", "disco");
	mkdirSync(packageDir, { recursive: true });
	mkdirSync(binDir, { recursive: true });
	writeFileSync(join(binDir, process.platform === "win32" ? "pnpm.cmd" : "pnpm"), createFakePnpmScript(root));
	chmodSync(join(binDir, process.platform === "win32" ? "pnpm.cmd" : "pnpm"), 0o755);
	tempDir = temp;
	process.env.PATH = `${binDir}${delimiter}${originalPath ?? ""}`;
	process.env.DISCO_PACKAGE_DIR = packageDir;
	setExecPath(
		join(
			root,
			".pnpm",
			"@auto-ml-skills+disco@0.0.0",
			"node_modules",
			"@auto-ml-skills",
			"disco",
			"dist",
			"cli.js",
		),
	);
	return { root, packageDir };
}

function createYarnGlobalInstall(): { globalDir: string; packageDir: string } {
	const temp = mkdtempSync(join(tmpdir(), "disco-yarn-"));
	const binDir = join(temp, "bin");
	const globalDir = join(temp, "yarn", "global");
	const packageDir = join(globalDir, "node_modules", "@auto-ml-skills", "disco");
	mkdirSync(packageDir, { recursive: true });
	mkdirSync(binDir, { recursive: true });
	writeFileSync(join(binDir, process.platform === "win32" ? "yarn.cmd" : "yarn"), createFakeYarnScript(globalDir));
	chmodSync(join(binDir, process.platform === "win32" ? "yarn.cmd" : "yarn"), 0o755);
	tempDir = temp;
	process.env.PATH = `${binDir}${delimiter}${originalPath ?? ""}`;
	process.env.DISCO_PACKAGE_DIR = packageDir;
	setExecPath(join(globalDir, ".yarn", "@auto-ml-skills", "disco", "dist", "cli.js"));
	return { globalDir, packageDir };
}

function createBunGlobalInstall(): { packageDir: string } {
	const temp = mkdtempSync(join(tmpdir(), "disco-bun-"));
	const prefix = join(temp, ".bun");
	const bunBin = join(prefix, "bin");
	const root = join(prefix, "install", "global", "node_modules");
	const scopeDir = join(root, "@auto-ml-skills");
	const packageDir = join(scopeDir, "disco");
	mkdirSync(packageDir, { recursive: true });
	mkdirSync(bunBin, { recursive: true });
	writeFileSync(join(bunBin, process.platform === "win32" ? "bun.cmd" : "bun"), createFakeBunScript(bunBin));
	chmodSync(join(bunBin, process.platform === "win32" ? "bun.cmd" : "bun"), 0o755);
	tempDir = temp;
	process.env.PATH = `${bunBin}${delimiter}${originalPath ?? ""}`;
	process.env.DISCO_PACKAGE_DIR = packageDir;
	setExecPath(join(packageDir, "dist", "cli.js"));
	return { packageDir };
}

function createFakePnpmScript(root: string): string {
	if (process.platform === "win32") {
		return `@echo off\r\nif "%1"=="root" if "%2"=="-g" echo ${root}\r\n`;
	}
	const escapedRoot = root.replaceAll("'", "'\\''");
	return `#!/bin/sh\nif [ "$1" = "root" ] && [ "$2" = "-g" ]; then\n\tprintf '%s\\n' '${escapedRoot}'\n\texit 0\nfi\nexit 1\n`;
}

function createFakeYarnScript(globalDir: string): string {
	if (process.platform === "win32") {
		return `@echo off\r\nif "%1"=="global" if "%2"=="dir" echo ${globalDir}\r\n`;
	}
	const escapedGlobalDir = globalDir.replaceAll("'", "'\\''");
	return `#!/bin/sh\nif [ "$1" = "global" ] && [ "$2" = "dir" ]; then\n\tprintf '%s\\n' '${escapedGlobalDir}'\n\texit 0\nfi\nexit 1\n`;
}

function createFakeBunScript(bunBin: string): string {
	if (process.platform === "win32") {
		return `@echo off\r\nif "%1"=="pm" if "%2"=="bin" if "%3"=="-g" echo ${bunBin}\r\n`;
	}
	const escapedBunBin = bunBin.replaceAll("'", "'\\''");
	return `#!/bin/sh\nif [ "$1" = "pm" ] && [ "$2" = "bin" ] && [ "$3" = "-g" ]; then\n\tprintf '%s\\n' '${escapedBunBin}'\n\texit 0\nfi\nexit 1\n`;
}

describe("detectInstallMethod", () => {
	test("detects pnpm from Windows .pnpm install paths", () => {
		setExecPath(
			"C:\\Users\\Admin\\Documents\\pnpm-repository\\global\\5\\.pnpm\\@auto-ml-skills+disco@0.67.68\\node_modules\\@auto-ml-skills\\disco\\dist\\cli.js",
		);

		expect(detectInstallMethod()).toBe("pnpm");
		expect(getUpdateInstruction("@auto-ml-skills/disco")).toBe(
			"Run: pnpm install -g --ignore-scripts --config.minimumReleaseAge=0 @auto-ml-skills/disco",
		);
	});

	test("does not self-update unknown wrapper installs", () => {
		setExecPath("/usr/local/bin/node");

		expect(detectInstallMethod()).toBe("unknown");
		expect(getSelfUpdateCommand("@auto-ml-skills/disco")).toBeUndefined();
		expect(getUpdateInstruction("@auto-ml-skills/disco")).toBe(
			"Update @auto-ml-skills/disco using the package manager, wrapper, or source checkout that provides this installation.",
		);
	});

	test("self-updates npm installs from custom prefixes", () => {
		const { prefix } = createNpmPrefixInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco");

		expect(detectInstallMethod()).toBe("npm");
		expect(command).toEqual({
			command: "npm",
			args: [
				"--prefix",
				prefix,
				"install",
				"-g",
				"--ignore-scripts",
				"--min-release-age=0",
				"@auto-ml-skills/disco",
			],
			display: `npm --prefix ${prefix} install -g --ignore-scripts --min-release-age=0 @auto-ml-skills/disco`,
		});
	});

	test("self-updates exact npm versions without uninstalling the current package", () => {
		const { prefix } = createNpmPrefixInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco", undefined, {
			packageName: "@auto-ml-skills/disco",
			installSpec: "@auto-ml-skills/disco@1.2.3",
		});

		expect(command).toEqual({
			command: "npm",
			args: [
				"--prefix",
				prefix,
				"install",
				"-g",
				"--ignore-scripts",
				"--min-release-age=0",
				"@auto-ml-skills/disco@1.2.3",
			],
			display: `npm --prefix ${prefix} install -g --ignore-scripts --min-release-age=0 @auto-ml-skills/disco@1.2.3`,
		});
	});

	test("self-updates renamed packages from the current install prefix", () => {
		const { prefix } = createNpmPrefixInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco", undefined, "@example/disco-next");

		expect(command).toEqual({
			command: "npm",
			args: ["--prefix", prefix, "install", "-g", "--ignore-scripts", "--min-release-age=0", "@example/disco-next"],
			display: `npm --prefix ${prefix} uninstall -g @auto-ml-skills/disco && npm --prefix ${prefix} install -g --ignore-scripts --min-release-age=0 @example/disco-next`,
			steps: [
				{
					command: "npm",
					args: ["--prefix", prefix, "uninstall", "-g", "@auto-ml-skills/disco"],
					display: `npm --prefix ${prefix} uninstall -g @auto-ml-skills/disco`,
				},
				{
					command: "npm",
					args: ["--prefix", prefix, "install", "-g", "--ignore-scripts", "--min-release-age=0", "@example/disco-next"],
					display: `npm --prefix ${prefix} install -g --ignore-scripts --min-release-age=0 @example/disco-next`,
				},
			],
		});
	});

	test("self-update respects configured npmCommand", () => {
		const { prefix } = createNpmPrefixInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco", ["npm", "--prefix", prefix]);

		expect(command).toEqual({
			command: "npm",
			args: [
				"--prefix",
				prefix,
				"install",
				"-g",
				"--ignore-scripts",
				"--min-release-age=0",
				"@auto-ml-skills/disco",
			],
			display: `npm --prefix ${prefix} install -g --ignore-scripts --min-release-age=0 @auto-ml-skills/disco`,
		});
	});

	test("self-update treats empty npmCommand as unset", () => {
		const { prefix } = createNpmPrefixInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco", []);

		expect(command?.args).toEqual([
			"--prefix",
			prefix,
			"install",
			"-g",
			"--ignore-scripts",
			"--min-release-age=0",
			"@auto-ml-skills/disco",
		]);
	});

	test("quotes npm self-update display paths", () => {
		const { prefix } = createNpmPrefixInstall("disco prefix ");

		const command = getSelfUpdateCommand("@auto-ml-skills/disco");

		expect(command?.display).toBe(
			`npm --prefix "${prefix}" install -g --ignore-scripts --min-release-age=0 @auto-ml-skills/disco`,
		);
	});

	test("does not infer Windows npm custom prefixes from package paths", () => {
		const packageDir = "C:\\Users\\Admin\\npm prefix\\node_modules\\@auto-ml-skills\\disco";
		process.env.DISCO_PACKAGE_DIR = packageDir;
		setExecPath(`${packageDir}\\dist\\cli.js`);

		expect(detectInstallMethod()).toBe("npm");
		expect(getUpdateInstruction("@auto-ml-skills/disco")).toBe(
			"Run: npm install -g --ignore-scripts --min-release-age=0 @auto-ml-skills/disco",
		);
	});

	test("self-updates bun global installs from bun pm bin", () => {
		createBunGlobalInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco");

		expect(detectInstallMethod()).toBe("bun");
		expect(command).toEqual({
			command: "bun",
			args: ["install", "-g", "--ignore-scripts", "--minimum-release-age=0", "@auto-ml-skills/disco"],
			display: "bun install -g --ignore-scripts --minimum-release-age=0 @auto-ml-skills/disco",
		});
	});

	test("self-updates renamed pnpm global installs by removing the old package first", () => {
		createPnpmGlobalInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco", undefined, "@example/disco-next");

		expect(detectInstallMethod()).toBe("pnpm");
		expect(command).toEqual({
			command: "pnpm",
			args: ["install", "-g", "--ignore-scripts", "--config.minimumReleaseAge=0", "@example/disco-next"],
			display:
				"pnpm remove -g @auto-ml-skills/disco && pnpm install -g --ignore-scripts --config.minimumReleaseAge=0 @example/disco-next",
			steps: [
				{
					command: "pnpm",
					args: ["remove", "-g", "@auto-ml-skills/disco"],
					display: "pnpm remove -g @auto-ml-skills/disco",
				},
				{
					command: "pnpm",
					args: ["install", "-g", "--ignore-scripts", "--config.minimumReleaseAge=0", "@example/disco-next"],
					display: "pnpm install -g --ignore-scripts --config.minimumReleaseAge=0 @example/disco-next",
				},
			],
		});
	});

	test("self-updates pnpm v11 global installs resolved through the store", () => {
		const temp = mkdtempSync(join(tmpdir(), "disco-pnpm11-"));
		const binDir = join(temp, "bin");
		const root = join(temp, "Library", "pnpm", "global", "v11");
		const packageName = "@auto-ml-skills/disco";
		const globalPackageDir = join(root, "11e9a", "node_modules", "@auto-ml-skills", "disco");
		const storePackageDir = join(
			temp,
			"Library",
			"pnpm",
			"store",
			"v11",
			"links",
			"@auto-ml-skills",
			"disco",
			"0.75.0",
			"hash",
			"node_modules",
			"@auto-ml-skills",
			"disco",
		);
		mkdirSync(globalPackageDir, { recursive: true });
		mkdirSync(storePackageDir, { recursive: true });
		mkdirSync(binDir, { recursive: true });
		writeFileSync(join(globalPackageDir, "package.json"), "{}");
		writeFileSync(join(binDir, process.platform === "win32" ? "pnpm.cmd" : "pnpm"), createFakePnpmScript(root));
		chmodSync(join(binDir, process.platform === "win32" ? "pnpm.cmd" : "pnpm"), 0o755);
		tempDir = temp;
		process.env.PATH = `${binDir}${delimiter}${originalPath ?? ""}`;
		process.env.DISCO_PACKAGE_DIR = storePackageDir;
		process.argv[1] = join(globalPackageDir, "dist", "cli.js");
		setExecPath(join(storePackageDir, "dist", "cli.js"));

		const command = getSelfUpdateCommand(packageName);

		expect(detectInstallMethod()).toBe("pnpm");
		expect(command).toEqual({
			command: "pnpm",
			args: ["install", "-g", "--ignore-scripts", "--config.minimumReleaseAge=0", packageName],
			display: `pnpm install -g --ignore-scripts --config.minimumReleaseAge=0 ${packageName}`,
		});
	});

	test("self-updates renamed yarn global installs by removing the old package first", () => {
		createYarnGlobalInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco", undefined, "@example/disco-next");

		expect(detectInstallMethod()).toBe("yarn");
		expect(command).toEqual({
			command: "yarn",
			args: ["global", "add", "--ignore-scripts", "@example/disco-next"],
			display: "yarn global remove @auto-ml-skills/disco && yarn global add --ignore-scripts @example/disco-next",
			steps: [
				{
					command: "yarn",
					args: ["global", "remove", "@auto-ml-skills/disco"],
					display: "yarn global remove @auto-ml-skills/disco",
				},
				{
					command: "yarn",
					args: ["global", "add", "--ignore-scripts", "@example/disco-next"],
					display: "yarn global add --ignore-scripts @example/disco-next",
				},
			],
		});
	});

	test("self-updates renamed bun global installs by removing the old package first", () => {
		createBunGlobalInstall();

		const command = getSelfUpdateCommand("@auto-ml-skills/disco", undefined, "@example/disco-next");

		expect(detectInstallMethod()).toBe("bun");
		expect(command).toEqual({
			command: "bun",
			args: ["install", "-g", "--ignore-scripts", "--minimum-release-age=0", "@example/disco-next"],
			display:
				"bun uninstall -g @auto-ml-skills/disco && bun install -g --ignore-scripts --minimum-release-age=0 @example/disco-next",
			steps: [
				{
					command: "bun",
					args: ["uninstall", "-g", "@auto-ml-skills/disco"],
					display: "bun uninstall -g @auto-ml-skills/disco",
				},
				{
					command: "bun",
					args: ["install", "-g", "--ignore-scripts", "--minimum-release-age=0", "@example/disco-next"],
					display: "bun install -g --ignore-scripts --minimum-release-age=0 @example/disco-next",
				},
			],
		});
	});

	test.skipIf(process.getuid?.() === 0)("does not self-update when npm install path is not writable", () => {
		const { packageDir } = createNpmPrefixInstall();
		chmodSync(packageDir, 0o500);

		expect(getSelfUpdateCommand("@auto-ml-skills/disco")).toBeUndefined();
		expect(getSelfUpdateUnavailableInstruction("@auto-ml-skills/disco")).toContain(
			"the install path is not writable",
		);
	});
});
