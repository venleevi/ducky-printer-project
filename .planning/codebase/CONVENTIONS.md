# Coding Conventions

**Analysis Date:** 2026-03-13

## Naming Patterns

**Files:**
- kebab-case for all files (gsd-check-update.js, gsd-context-monitor.js)
- Markdown files: kebab-case for commands and workflows (execute-phase.md, map-codebase.md)
- Agent files: gsd-{role}.md pattern (gsd-executor.md, gsd-planner.md, gsd-codebase-mapper.md)
- Template files: kebab-case or single-word (conventions.md, testing.md, phase-prompt.md)

**Functions:**
- camelCase for all functions (detectConfigDir, process, spawn)
- No special prefix for async functions
- Descriptive names that indicate action (detectConfigDir, writeFileSync, clearTimeout)

**Variables:**
- camelCase for variables (homeDir, cwd, globalConfigDir, projectConfigDir)
- UPPER_SNAKE_CASE for constants (WARNING_THRESHOLD, CRITICAL_THRESHOLD, STALE_SECONDS, DEBOUNCE_CALLS)
- Descriptive const names for file paths (cacheDir, cacheFile, metricsPath, bridgePath)

**Types:**
- Not applicable - codebase uses JavaScript, not TypeScript
- JSON structures follow camelCase for keys (update_available, session_id, remaining_percentage)

## Code Style

**Formatting:**
- No Prettier or ESLint config detected in project root
- 2 space indentation (consistent across all .js files)
- Single quotes for strings
- Semicolons used consistently
- 80-100 character line length (soft limit, some lines exceed)

**Linting:**
- No linting configuration detected
- No package.json at project root (only in .claude/ directory)
- Clean, readable code without linting enforcement

## Import Organization

**Order:**
1. Node.js built-in modules (fs, path, os, child_process)
2. External packages (none detected in hook files)
3. No internal module imports in hooks (standalone scripts)

**Grouping:**
- Built-in requires grouped at top of file
- No blank lines between require statements
- Destructured imports used when needed: `const { spawn } = require('child_process');`

**Path Aliases:**
- None used - hooks use relative paths
- Workflow files use @ references to templates and references

## Error Handling

**Patterns:**
- Silent failures in hooks to avoid blocking execution
- try/catch blocks wrap stdin parsing: `try { const data = JSON.parse(input); } catch (e) { process.exit(0); }`
- Early exit on errors: `if (!sessionId) { process.exit(0); }`
- Graceful degradation: if metrics file missing or stale, exit silently

**Error Types:**
- No custom error classes
- Silent exit (process.exit(0)) used for graceful failures
- No error logging in hooks (to avoid stderr noise)

## Logging

**Framework:**
- No logging framework used
- Hooks write to stdout only for structured output
- No console.log calls in production hooks

**Patterns:**
- Hooks communicate via stdout: `process.stdout.write(JSON.stringify(output));`
- Comments explain behavior instead of runtime logging
- Silent operation: errors result in exit(0) rather than logging

## Comments

**When to Comment:**
- Block comments at file start explain purpose and architecture:
  ```javascript
  // Context Monitor - PostToolUse/AfterTool hook (Gemini uses AfterTool)
  // Reads context metrics from the statusline bridge file and injects
  // warnings when context usage is high.
  ```
- Inline comments explain thresholds, timeouts, and non-obvious behavior
- Comments document "why" not "what": `// Timeout guard: if stdin doesn't close within 3s... exit silently`
- Reference external issues: `// See #775.`

**JSDoc/TSDoc:**
- Not used in this codebase
- Function documentation through descriptive names and comments

**TODO Comments:**
- Not detected in current codebase
- If added, would likely follow format: `// TODO: description`

## Function Design

**Size:**
- Functions kept compact (detectConfigDir is 12 lines)
- Scripts structured as linear flow with helper functions extracted
- Main execution in stdin event handlers

**Parameters:**
- Functions take minimal parameters (detectConfigDir takes baseDir)
- Configuration via constants at file top
- No complex parameter objects (simple JavaScript)

**Return Values:**
- Explicit return values from functions: `return envDir || path.join(baseDir, '.claude');`
- Process exit for script termination: `process.exit(0);`
- Early returns for guard clauses

## Module Design

**Exports:**
- Hook scripts are standalone executables (no exports)
- Shebang line for direct execution: `#!/usr/bin/env node`
- Package.json in .claude/ uses `{"type":"commonjs"}`

**Module Pattern:**
- Scripts are single-purpose, self-contained
- No module exports/imports between hooks
- Each hook is independent executable

## Markdown Conventions

**Agent Files (.claude/agents/):**
- Frontmatter with name, description, tools, color, skills
- Structured with XML-like tags: `<role>`, `<process>`, `<step name="">`, `<critical_rules>`
- Steps include priority attributes: `<step name="init_context" priority="first">`

**Command Files (.claude/commands/gsd/):**
- Frontmatter with name, description, argument-hint, allowed-tools
- Reference external workflows via @-syntax: `@./.claude/get-shit-done/workflows/execute-phase.md`
- Structured sections: `<objective>`, `<execution_context>`, `<context>`, `<process>`

**Workflow Files (.claude/get-shit-done/workflows/):**
- Detailed process documentation with `<step>` tags
- Bash code examples in triple backticks
- Success criteria at end: `<success_criteria>` with checklist

**Template Files (.claude/get-shit-done/templates/):**
- Show example structure and good examples
- Include `<guidelines>` and usage instructions
- Placeholder patterns: `[YYYY-MM-DD]`, `[Placeholder text]`

---

*Convention analysis: 2026-03-13*
