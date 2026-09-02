import { chmodSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { readManagedInstallMarker } from "../src/utils/managed-install.ts";

const originalManagedInstall = process.env.DISCO_MANAGED_INSTALL;
const originalManagedInstallDir = process.env.DISCO_MANAGED_INSTALL_DIR;
const originalManagedInstallMarker = process.env.DISCO_MANAGED_INSTALL_MARKER;
const temporaryDirectories: string[] = [];

function createMarker(overrides: Record<string, unknown> = {}): string {
	const root = mkdtempSync(join("/tmp", "disco-managed-marker-"));
	temporaryDirectories.push(root);
	const installDir = join(root, "install");
	const version = "0.2.1";
	const entrypoint = join(installDir, "releases", version, "node_modules", "@arex-skill", "disco", "dist", "cli.js");
	const installerPath = join(installDir, "install-disco.sh");
	const nodePath = join(root, "node");
	mkdirSync(dirname(entrypoint), { recursive: true });
	mkdirSync(installDir, { recursive: true });
	writeFileSync(entrypoint, "#!/usr/bin/env sh\n");
	writeFileSync(installerPath, "#!/usr/bin/env sh\n");
	writeFileSync(nodePath, "#!/usr/bin/env sh\n");
	chmodSync(entrypoint, 0o755);
	chmodSync(installerPath, 0o755);
	chmodSync(nodePath, 0o755);
	writeFileSync(join(installDir, "current-version"), `${version}\n`);
	writeFileSync(
		join(installDir, "managed-install.json"),
		JSON.stringify({
			schemaVersion: 1,
			packageName: "@arex-skill/disco",
			activeVersion: version,
			installDir,
			entrypoint,
			nodeSource: "system",
			nodeVersion: "24.16.0",
			nodePath,
			installerPath,
			platform: "linux-x64",
			...overrides,
		}),
	);
	process.env.DISCO_MANAGED_INSTALL = "1";
	process.env.DISCO_MANAGED_INSTALL_DIR = installDir;
	delete process.env.DISCO_MANAGED_INSTALL_MARKER;
	return installDir;
}

afterEach(() => {
	if (originalManagedInstall === undefined) delete process.env.DISCO_MANAGED_INSTALL;
	else process.env.DISCO_MANAGED_INSTALL = originalManagedInstall;
	if (originalManagedInstallDir === undefined) delete process.env.DISCO_MANAGED_INSTALL_DIR;
	else process.env.DISCO_MANAGED_INSTALL_DIR = originalManagedInstallDir;
	if (originalManagedInstallMarker === undefined) delete process.env.DISCO_MANAGED_INSTALL_MARKER;
	else process.env.DISCO_MANAGED_INSTALL_MARKER = originalManagedInstallMarker;
	for (const directory of temporaryDirectories.splice(0)) rmSync(directory, { recursive: true, force: true });
});

describe("managed install marker", () => {
	it("accepts a complete marker whose pointer and entrypoint agree", () => {
		const installDir = createMarker();

		expect(readManagedInstallMarker()).toMatchObject({
			packageName: "@arex-skill/disco",
			activeVersion: "0.2.1",
			installDir,
		});
	});

	it("accepts a marker written with a UTF-8 BOM", () => {
		const installDir = createMarker();
		const markerPath = join(installDir, "managed-install.json");
		const marker = readFileSync(markerPath, "utf8");
		writeFileSync(markerPath, `\uFEFF${marker}`, "utf8");

		expect(readManagedInstallMarker()).toMatchObject({
			packageName: "@arex-skill/disco",
			activeVersion: "0.2.1",
		});
	});

	it("rejects an entrypoint outside the managed release tree", () => {
		const installDir = createMarker({ entrypoint: join(installDirPlaceholder(), "outside", "cli.js") });

		expect(readManagedInstallMarker()).toBeUndefined();
		void installDir;
	});

	it("rejects a marker whose current pointer does not match activeVersion", () => {
		const installDir = createMarker();
		writeFileSync(join(installDir, "current-version"), "0.2.0\n");

		expect(readManagedInstallMarker()).toBeUndefined();
	});
});

function installDirPlaceholder(): string {
	return "/tmp/disco-marker-outside";
}
