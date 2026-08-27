#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const HELP = `Read-only static checker for @mem0/vercel-ai-provider usage.

Usage:
  node scripts/check_vercel_mem0_usage.mjs <file-or-directory> [...]

Checks TypeScript/JavaScript source for:
  - @mem0/vercel-ai-provider imports
  - createMem0 calls and wrapped model usage
  - addMemories/retrieveMemories/getMemories/searchMemories calls
  - nearby user_id/app_id/agent_id/run_id scoping
  - literal Mem0 API keys
  - AI SDK v5/v4 hints that may not match provider v3.0.0

The checker is read-only and does not execute application code.
`;

const SOURCE_EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs']);
const scopePattern = /\b(user_id|app_id|agent_id|run_id)\b|\b(userId|appId|agentId|runId)\b/;
const utilityPattern = /\b(addMemories|retrieveMemories|getMemories|searchMemories)\s*\(/g;

function walk(target) {
  const stat = fs.statSync(target, { throwIfNoEntry: false });
  if (!stat) return [];
  if (stat.isFile()) return SOURCE_EXTENSIONS.has(path.extname(target)) ? [target] : [];
  if (!stat.isDirectory()) return [];
  const out = [];
  for (const entry of fs.readdirSync(target, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name === 'dist' || entry.name === '.next' || entry.name === '.git') continue;
    out.push(...walk(path.join(target, entry.name)));
  }
  return out;
}

function lineOf(text, index) {
  return text.slice(0, index).split('\n').length;
}

function snippetAround(text, index, radius = 320) {
  return text.slice(Math.max(0, index - radius), Math.min(text.length, index + radius));
}

function checkFile(file) {
  const text = fs.readFileSync(file, 'utf8');
  const findings = [];
  const importsProvider = text.includes('@mem0/vercel-ai-provider');
  const importsAi = /from\s+['"]ai['"]|require\(['"]ai['"]\)/.test(text);
  const createMem0Imported = /\bcreateMem0\b/.test(text) && importsProvider;
  const createMem0Calls = [...text.matchAll(/\bcreateMem0\s*\(/g)];
  const mem0KeyLiteral = /\bm0-[A-Za-z0-9_-]{12,}/.exec(text);

  if (mem0KeyLiteral) {
    findings.push({ level: 'error', line: lineOf(text, mem0KeyLiteral.index), message: 'literal Mem0 API key-looking value found; use MEM0_API_KEY env var' });
  }

  const utilityCalls = [...text.matchAll(utilityPattern)];

  if (importsProvider && !createMem0Calls.length && !utilityCalls.length) {
    findings.push({ level: 'warn', line: 1, message: 'imports @mem0/vercel-ai-provider but no createMem0 or utility call was found' });
  }

  if (createMem0Imported && !createMem0Calls.length) {
    findings.push({ level: 'warn', line: 1, message: 'createMem0 appears imported/referenced but is not called' });
  }

  for (const match of createMem0Calls) {
    const nearby = snippetAround(text, match.index, 700);
    if (!/mem0ApiKey|MEM0_API_KEY/.test(nearby)) {
      findings.push({ level: 'info', line: lineOf(text, match.index), message: 'createMem0 call has no nearby mem0ApiKey/MEM0_API_KEY; verify config supplies it' });
    }
    if (!/provider\s*:|apiKey\s*:|OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_GENERATIVE_AI_API_KEY|GROQ_API_KEY|COHERE_API_KEY/.test(nearby)) {
      findings.push({ level: 'info', line: lineOf(text, match.index), message: 'createMem0 call has no nearby upstream provider/apiKey; verify selected model provider is configured' });
    }
  }

  const wrappedModelCalls = [...text.matchAll(/model\s*:\s*\w+\s*\([^)]*\)/g)];
  for (const match of wrappedModelCalls) {
    const nearby = snippetAround(text, match.index, 500);
    if (/createMem0|\bmem0\s*=/.test(text) && !scopePattern.test(nearby)) {
      findings.push({ level: 'warn', line: lineOf(text, match.index), message: 'wrapped model call has no nearby user/app/agent/run scope' });
    }
  }

  for (const match of utilityCalls) {
    const nearby = snippetAround(text, match.index, 500);
    if (!scopePattern.test(nearby)) {
      findings.push({ level: 'warn', line: lineOf(text, match.index), message: `${match[1]} call has no nearby user/app/agent/run scope` });
    }
    if (!/mem0ApiKey|MEM0_API_KEY/.test(nearby) && !/process\.env\.MEM0_API_KEY/.test(text)) {
      findings.push({ level: 'info', line: lineOf(text, match.index), message: `${match[1]} may rely on MEM0_API_KEY; verify it is available server-side` });
    }
  }

  if (importsAi && /LanguageModelV2|ProviderV2|ai@\^?5|"ai"\s*:\s*"\^?5/.test(text)) {
    findings.push({ level: 'warn', line: 1, message: 'AI SDK v5/V2 hint found; @mem0/vercel-ai-provider v3.0.0 targets AI SDK v6 ProviderV3' });
  }

  if (/NEXT_PUBLIC_MEM0_API_KEY|VITE_MEM0_API_KEY|PUBLIC_MEM0_API_KEY/.test(text)) {
    findings.push({ level: 'error', line: 1, message: 'public/client-exposed Mem0 API key variable detected; keep MEM0_API_KEY server-side' });
  }

  return { file, importsProvider, createMem0Calls: createMem0Calls.length, findings };
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    process.stdout.write(HELP);
    return 0;
  }

  const files = [...new Set(args.flatMap(walk))].sort();
  if (files.length === 0) {
    console.log('No TypeScript/JavaScript source files found.');
    return 0;
  }

  let errors = 0;
  let warnings = 0;
  let providerFiles = 0;
  for (const file of files) {
    const result = checkFile(file);
    if (result.importsProvider) providerFiles += 1;
    if (!result.findings.length) continue;
    console.log(file);
    for (const finding of result.findings) {
      if (finding.level === 'error') errors += 1;
      if (finding.level === 'warn') warnings += 1;
      console.log(`  ${finding.level.toUpperCase()} line ${finding.line}: ${finding.message}`);
    }
  }

  console.log(`Checked ${files.length} file(s); provider imports in ${providerFiles}; warnings=${warnings}; errors=${errors}.`);
  return errors > 0 ? 1 : 0;
}

process.exitCode = main();
