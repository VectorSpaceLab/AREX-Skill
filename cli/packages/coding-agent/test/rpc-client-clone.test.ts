import { dirname, isAbsolute } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { resolveRpcCliPath, RpcClient } from "../src/modes/rpc/rpc-client.ts";

type RpcClientPrivate = {
	send: (command: { type: string }) => Promise<unknown>;
	getData: <T>(response: unknown) => T;
};

describe("RpcClient clone", () => {
	it("resolves the default CLI relative to its own module", () => {
		const defaultPath = resolveRpcCliPath();

		expect(isAbsolute(defaultPath)).toBe(true);
		expect(dirname(defaultPath)).toMatch(/[\\/]src$/u);
		expect(defaultPath).toMatch(/[\\/]cli\.js$/u);
		expect(resolveRpcCliPath("/explicit/disco-cli.js")).toBe("/explicit/disco-cli.js");
	});

	it("sends the clone RPC command", async () => {
		const client = new RpcClient();
		const privateClient = client as unknown as RpcClientPrivate;
		const send = vi.fn(async () => ({
			type: "response",
			command: "clone",
			success: true,
			data: { cancelled: false },
		}));
		privateClient.send = send;
		privateClient.getData = <T>(response: unknown): T => {
			return (response as { data: T }).data;
		};

		const result = await client.clone();

		expect(send).toHaveBeenCalledWith({ type: "clone" });
		expect(result).toEqual({ cancelled: false });
	});
});
