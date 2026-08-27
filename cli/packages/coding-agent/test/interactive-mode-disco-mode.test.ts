import { describe, expect, it, vi } from "vitest";
import type { DiscoAgentMode } from "../src/disco/modes/types.ts";
import { InteractiveMode } from "../src/modes/interactive/interactive-mode.ts";

type ModeSwitchContext = {
	sessionManager: {
		getDiscoMode: () => DiscoAgentMode;
		getEntries: () => unknown[];
		isPersisted: () => boolean;
		persistForResume: () => boolean;
	};
	session: { isStreaming: boolean; isCompacting: boolean; isBashRunning: boolean };
	runtimeHost: {
		newSession: (options: { discoMode: DiscoAgentMode }) => Promise<{ cancelled: boolean }>;
	};
	showStatus: (message: string) => void;
	showWarning: (message: string) => void;
	showExtensionConfirm: (title: string, message: string) => Promise<boolean>;
	clearStatusIndicator: () => void;
	handleFatalRuntimeError: (prefix: string, error: unknown) => Promise<void>;
};

type InteractiveModePrototype = {
	handleModeSwitchCommand(this: ModeSwitchContext, targetMode: DiscoAgentMode): Promise<void>;
};

const interactiveModePrototype = InteractiveMode.prototype as unknown as InteractiveModePrototype;

function createContext(options?: { currentMode?: DiscoAgentMode; confirmed?: boolean; newSessionCancelled?: boolean }) {
	const showStatus = vi.fn();
	const showWarning = vi.fn();
	const showExtensionConfirm = vi.fn(async () => options?.confirmed ?? true);
	const clearStatusIndicator = vi.fn();
	const newSession = vi.fn(async () => ({ cancelled: options?.newSessionCancelled ?? false }));
	const handleFatalRuntimeError = vi.fn(async () => {});
	const persistForResume = vi.fn(() => true);
	const context: ModeSwitchContext = {
		sessionManager: {
			getDiscoMode: () => options?.currentMode ?? "researcher",
			getEntries: () => [{}],
			isPersisted: () => true,
			persistForResume,
		},
		session: { isStreaming: false, isCompacting: false, isBashRunning: false },
		runtimeHost: { newSession },
		showStatus,
		showWarning,
		showExtensionConfirm,
		clearStatusIndicator,
		handleFatalRuntimeError,
	};
	return {
		context,
		showStatus,
		showWarning,
		showExtensionConfirm,
		clearStatusIndicator,
		newSession,
		persistForResume,
		handleFatalRuntimeError,
	};
}

describe("InteractiveMode DisCo mode switching", () => {
	it("keeps the current context when the requested mode is already active", async () => {
		const state = createContext({ currentMode: "creator" });

		await interactiveModePrototype.handleModeSwitchCommand.call(state.context, "creator");

		expect(state.showStatus).toHaveBeenCalledWith("Already in Creator mode; the current context was kept.");
		expect(state.showExtensionConfirm).not.toHaveBeenCalled();
		expect(state.newSession).not.toHaveBeenCalled();
		expect(state.persistForResume).not.toHaveBeenCalled();
		expect(state.clearStatusIndicator).not.toHaveBeenCalled();
	});

	it("explains the clean-context boundary and leaves the session unchanged when cancelled", async () => {
		const state = createContext({ confirmed: false });

		await interactiveModePrototype.handleModeSwitchCommand.call(state.context, "creator");

		expect(state.showExtensionConfirm).toHaveBeenCalledWith(
			"Switch to Creator mode",
			expect.stringContaining("the old session remains available through /resume and can be exported separately"),
		);
		expect(state.showExtensionConfirm).toHaveBeenCalledWith(
			"Switch to Creator mode",
			expect.stringContaining("Exports from the new session include only new-mode activity."),
		);
		expect(state.showStatus).toHaveBeenCalledWith("Mode switch cancelled");
		expect(state.newSession).not.toHaveBeenCalled();
		expect(state.persistForResume).not.toHaveBeenCalled();
		expect(state.clearStatusIndicator).not.toHaveBeenCalled();
	});

	it("blocks a cross-mode switch while a bash command is running", async () => {
		const state = createContext();
		state.context.session.isBashRunning = true;

		await interactiveModePrototype.handleModeSwitchCommand.call(state.context, "creator");

		expect(state.showWarning).toHaveBeenCalledWith(
			"Wait for the current bash command to finish or cancel it before switching modes.",
		);
		expect(state.showExtensionConfirm).not.toHaveBeenCalled();
		expect(state.persistForResume).not.toHaveBeenCalled();
		expect(state.newSession).not.toHaveBeenCalled();
	});

	it("creates a new session with the target mode after confirmation", async () => {
		const state = createContext();

		await interactiveModePrototype.handleModeSwitchCommand.call(state.context, "creator");

		expect(state.clearStatusIndicator).toHaveBeenCalledOnce();
		expect(state.persistForResume).toHaveBeenCalledOnce();
		expect(state.newSession).toHaveBeenCalledWith({ discoMode: "creator" });
		expect(state.showStatus).toHaveBeenCalledWith(
			"Switched to Creator mode in a new session. Previous context was cleared.",
		);
		expect(state.showWarning).not.toHaveBeenCalled();
		expect(state.handleFatalRuntimeError).not.toHaveBeenCalled();
	});
});
