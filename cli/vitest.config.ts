import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const codingAgentRoot = fileURLToPath(new URL("./packages/coding-agent", import.meta.url));

export default defineConfig({
  root: codingAgentRoot,
  test: {
    globals: true,
    environment: "node",
    fileParallelism: false,
    testTimeout: 30000,
    env: {
      DISCO_OFFLINE: "1",
      PI_OFFLINE: "1",
      GIT_COMMITTER_NAME: "DisCo test fixture",
      GIT_COMMITTER_EMAIL: "disco-tests@localhost",
    },
    unstubEnvs: true,
    reporters: process.env.GITHUB_ACTIONS ? ["dot", "github-actions"] : ["dot"],
    silent: "passed-only",
    server: {
      deps: {
        external: [/@silvia-odwyer\/photon-node/],
		inline: [/@earendil-works\/pi-ai/],
      },
    },
  },
});
