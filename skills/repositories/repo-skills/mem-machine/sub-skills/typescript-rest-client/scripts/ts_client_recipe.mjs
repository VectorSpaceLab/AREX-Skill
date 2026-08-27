#!/usr/bin/env node
/** Print or run a minimal @memmachine/client recipe.
 * Default mode prints a recipe. --live-health imports the package and calls
 * healthCheck against an explicitly configured base URL. It does not add or
 * delete memories.
 */

import process from 'node:process'

function arg(name, fallback) {
  const i = process.argv.indexOf(name)
  if (i >= 0 && i + 1 < process.argv.length) return process.argv[i + 1]
  return fallback
}

const liveHealth = process.argv.includes('--live-health')
const baseUrl = arg('--base-url', process.env.MEMMACHINE_BASE_URL || process.env.MEMORY_BACKEND_URL || 'https://api.memmachine.ai/v2')
const apiKey = arg('--api-key', process.env.MEMMACHINE_API_KEY)

const recipe = `import MemMachineClient from '@memmachine/client'

const client = new MemMachineClient({
  base_url: '${baseUrl}',
  api_key: process.env.MEMMACHINE_API_KEY
})

const project = client.project({ org_id: 'my-org', project_id: 'my-project' })
const memory = project.memory({ user_id: 'alice', agent_id: 'assistant' })
await memory.add('Alice prefers aisle seats.', { metadata: { category: 'travel' } })
const result = await memory.search('What seating does Alice prefer?', { top_k: 5 })
console.dir(result, { depth: null })
`

if (!liveHealth) {
  console.log(recipe)
  process.exit(0)
}

try {
  const mod = await import('@memmachine/client')
  const MemMachineClient = mod.default || mod.MemMachineClient
  const client = new MemMachineClient({ base_url: baseUrl, api_key: apiKey })
  const health = await client.healthCheck()
  console.dir(health, { depth: null })
} catch (err) {
  console.error(err && err.stack ? err.stack : err)
  process.exit(1)
}
