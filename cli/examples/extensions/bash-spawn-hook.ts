/**
 * Bash Spawn Hook Example
 *
 * Adjusts command, cwd, and env before execution.
 *
 * Usage:
 *   disco -e ./bash-spawn-hook.ts
 */

import type { ExtensionAPI } from "@auto-ml-skills/disco";
import { createBashTool } from "@auto-ml-skills/disco";

export default function (disco: ExtensionAPI) {
	const cwd = process.cwd();

	const bashTool = createBashTool(cwd, {
		spawnHook: ({ command, cwd, env }) => ({
			command: `source ~/.profile\n${command}`,
			cwd,
			env: { ...env, DISCO_SPAWN_HOOK: "1" },
		}),
	});

	disco.registerTool({
		...bashTool,
		execute: async (id, params, signal, onUpdate, _ctx) => {
			return bashTool.execute(id, params, signal, onUpdate);
		},
	});
}
