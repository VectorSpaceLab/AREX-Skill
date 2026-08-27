import type { ExtensionAPI, ExtensionContext } from "../../core/extensions/types.ts";
import type { DiscoAgentMode } from "../modes/types.ts";
import {
	createEffortState,
	createWorkflowStorage,
	createWorkflowTool,
	installResultDelivery,
	installTaskPanel,
	installWorkflowEditor,
	loadWorkflowSettings,
	registerAllSavedWorkflows,
	registerBuiltinWorkflows,
	registerEffortCommand,
	registerWorkflowCommands,
	registerWorkflowModelsCommand,
	saveWorkflowSettingsForCwd,
	WorkflowManager,
} from "./index.ts";
import type { WorkflowSettings } from "./workflow-settings.ts";

export function createDisCoDynamicWorkflowExtension(
	cwd: string = process.cwd(),
	discoMode: DiscoAgentMode = "researcher",
) {
	return function discoDynamicWorkflowExtension(api: ExtensionAPI): void {
		const storage = createWorkflowStorage(cwd);
		const settings = loadWorkflowSettings({ cwd });
		const manager = new WorkflowManager({
			cwd,
			loadSavedWorkflow: (name: string) => storage.load(name)?.script,
			defaultAgentTimeoutMs: settings.defaultAgentTimeoutMs ?? null,
			concurrency: settings.defaultConcurrency,
			defaultAgentRetries: settings.defaultAgentRetries,
			discoMode,
		});

		const workflowTool = createWorkflowTool({ cwd, manager, storage });
		api.registerTool(workflowTool);
		registerWorkflowCommands(api, manager, { storage, cwd });
		registerWorkflowModelsCommand(api);
		registerBuiltinWorkflows(api, { cwd });
		registerAllSavedWorkflows(api, cwd, storage, manager);

		const effort = createEffortState();
		registerEffortCommand(api, effort);
		let editorInstalled = false;

		api.on("session_start", (_event: unknown, ctx: ExtensionContext) => {
			const active = api.getActiveTools();
			if (!active.includes(workflowTool.name)) {
				api.setActiveTools([...active, workflowTool.name]);
			}

			manager.setMainModel(ctx.model ? `${ctx.model.provider}/${ctx.model.id}` : undefined);
			manager.setModelRegistry(ctx.modelRegistry);
			try {
				manager.setSessionId(ctx.sessionManager?.getSessionId());
			} catch {
				// sessionManager may be unavailable in some contexts.
			}

			installResultDelivery(api, manager);
			installTaskPanel(api, manager, ctx.ui, { storage, cwd, loadSettings: () => loadWorkflowSettings({ cwd }) });
			if (!editorInstalled) {
				installWorkflowEditor(api, ctx.ui, effort, {
					settingsStore: {
						load: () => loadWorkflowSettings({ cwd }),
						save: (nextSettings: WorkflowSettings) => saveWorkflowSettingsForCwd(nextSettings, cwd),
					},
				});
				editorInstalled = true;
			}
		});
	};
}
