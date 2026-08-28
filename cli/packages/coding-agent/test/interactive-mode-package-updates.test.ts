import { Container } from "@earendil-works/pi-tui";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { DefaultPackageManager } from "../src/core/package-manager.ts";
import { InteractiveMode } from "../src/modes/interactive/interactive-mode.ts";
import { initTheme } from "../src/modes/interactive/theme/theme.ts";

function render(container: Container): string {
	return container
		.render(120)
		.join("\n")
		.replace(/\u001b\[[0-9;]*m/g, "");
}

describe("InteractiveMode package update notifications", () => {
	beforeAll(() => {
		initTheme("dark");
	});

	beforeEach(() => {
		vi.stubEnv("DISCO_OFFLINE", "");
	});

	afterEach(() => {
		vi.restoreAllMocks();
		vi.unstubAllEnvs();
	});

	it("maps package-manager updates to display names", async () => {
		vi.spyOn(DefaultPackageManager.prototype, "checkForAvailableUpdates").mockResolvedValue([
			{
				source: "npm:@juicesharp/rpiv-todo@^2.7.1",
				displayName: "@juicesharp/rpiv-todo",
				type: "npm",
				scope: "user",
			},
		]);
		const fakeThis = {
			sessionManager: { getCwd: () => process.cwd() },
			settingsManager: {},
		};

		const packages = await (InteractiveMode as any).prototype.checkForPackageUpdates.call(fakeThis);

		expect(packages).toEqual(["@juicesharp/rpiv-todo"]);
	});

	it("renders the update command and affected default package", () => {
		const fakeThis = {
			chatContainer: new Container(),
			ui: { requestRender: vi.fn() },
		};

		InteractiveMode.prototype.showPackageUpdateNotification.call(fakeThis as any, ["@juicesharp/rpiv-todo"]);

		const output = render(fakeThis.chatContainer);
		expect(output).toContain("Package Updates Available");
		expect(output).toContain("disco update --extensions");
		expect(output).toContain("- @juicesharp/rpiv-todo");
		expect(fakeThis.ui.requestRender).toHaveBeenCalledTimes(1);
	});
});
