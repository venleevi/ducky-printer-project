# Architecture

**Analysis Date:** 2026-03-13

## Pattern Overview

**Overall:** Event-driven framework with hook-based lifecycle management

**Key Characteristics:**
- Workflow orchestration through Claude Code commands
- Hook-based extension system (SessionStart, PostToolUse, statusline)
- Template-driven document generation
- Git-integrated state management
- Agent-based task decomposition

## Layers

**Command Layer:**
- Purpose: User-facing entry points for GSD operations
- Location: `.claude/commands/gsd/`
- Contains: Markdown command definitions (add-phase.md, execute-phase.md, etc.)
- Depends on: Workflow orchestrators, GSD tools
- Used by: Claude Code command palette

**Workflow Layer:**
- Purpose: Orchestration logic for multi-step operations
- Location: `.claude/get-shit-done/workflows/`
- Contains: Workflow definitions (execute-phase.md, plan-phase.md, etc.)
- Depends on: Agent prompts, GSD tools, templates
- Used by: Command layer

**Agent Layer:**
- Purpose: Specialized AI agents for specific tasks
- Location: `.claude/agents/`
- Contains: Agent prompt definitions (gsd-executor.md, gsd-planner.md, gsd-codebase-mapper.md, etc.)
- Depends on: Templates, codebase context
- Used by: Workflow layer for task delegation

**Tool Layer:**
- Purpose: Core runtime logic and state management
- Location: `.claude/get-shit-done/bin/`
- Contains: Node.js modules (gsd-tools.cjs, lib/*.cjs)
- Depends on: File system, git
- Used by: Commands, workflows, hooks

**Template Layer:**
- Purpose: Document structure definitions
- Location: `.claude/get-shit-done/templates/`
- Contains: Markdown templates (milestone.md, phase-prompt.md, codebase/*.md)
- Depends on: Nothing (pure templates)
- Used by: Tool layer for document generation

**Hook Layer:**
- Purpose: Event-driven background tasks
- Location: `.claude/hooks/`
- Contains: Node.js hook scripts (gsd-check-update.js, gsd-context-monitor.js, gsd-statusline.js)
- Depends on: File system, npm registry (for updates)
- Used by: Claude Code runtime

## Data Flow

**Command Execution Flow:**

1. User invokes command via Claude Code command palette (e.g., `/gsd:execute-phase`)
2. Command definition (`.claude/commands/gsd/execute-phase.md`) loads
3. Workflow orchestrator (`.claude/get-shit-done/workflows/execute-phase.md`) executes
4. Workflow spawns specialized agent (`.claude/agents/gsd-executor.md`)
5. Agent uses GSD tools (`gsd-tools.cjs`) to read state (`.planning/STATE.md`)
6. Agent performs work, updates files
7. GSD tools update state and git history
8. Control returns to user

**State Management:**
- Central state file: `.planning/STATE.md`
- State tracked: current milestone, phase progress, context, blockers
- State mutations: Through GSD tool library (`bin/lib/state.cjs`)
- Persistence: Git commits with structured messages

**Hook Execution Flow:**

1. **SessionStart**: `gsd-check-update.js` spawns background process to check npm for updates, writes cache to `~/.claude/cache/gsd-update-check.json`
2. **PostToolUse**: `gsd-context-monitor.js` reads context metrics from `/tmp/claude-ctx-{session_id}.json`, injects warnings when context is low
3. **Statusline**: `gsd-statusline.js` reads todos from `~/.claude/todos/`, context metrics from temp files, displays status bar

## Key Abstractions

**Milestone:**
- Purpose: Represents a major deliverable or project phase
- Examples: `.planning/milestones/01-milestone-name.md`
- Pattern: Numbered markdown files with frontmatter metadata
- Managed by: `bin/lib/milestone.cjs`

**Phase:**
- Purpose: Represents a discrete unit of work within a milestone
- Examples: Phase metadata in milestone files, execution plans in `.planning/phases/`
- Pattern: Decimal numbering (1.1, 1.2, 1.3) with status tracking
- Managed by: `bin/lib/phase.cjs`

**Agent:**
- Purpose: Specialized AI persona for specific task types
- Examples: `gsd-executor.md`, `gsd-planner.md`, `gsd-debugger.md`
- Pattern: Markdown prompt with role definition, process steps, rules
- Invocation: Via Agent tool in workflow orchestrators

**Template:**
- Purpose: Reusable document structure
- Examples: `templates/milestone.md`, `templates/phase-prompt.md`, `templates/codebase/architecture.md`
- Pattern: Markdown with placeholder syntax `[placeholder]`
- Rendering: Via `bin/lib/template.cjs`

## Entry Points

**Command Entry Points:**
- Location: `.claude/commands/gsd/*.md`
- Triggers: User invocation via Claude Code command palette
- Responsibilities: Load corresponding workflow, pass arguments

**Hook Entry Points:**
- Location: `.claude/hooks/*.js`
- Triggers: Claude Code lifecycle events (SessionStart, PostToolUse)
- Responsibilities: Background tasks (update checks, context monitoring, status display)

**Tool Entry Point:**
- Location: `.claude/get-shit-done/bin/gsd-tools.cjs`
- Triggers: Node.js execution from workflows or hooks
- Responsibilities: State management, file operations, git integration

## Error Handling

**Strategy:** Graceful degradation with silent failures for non-critical operations

**Patterns:**
- Hooks: Try-catch with `process.exit(0)` on error (never block Claude Code)
- Tools: Validation with error messages returned to caller
- Workflows: Error context propagated to user via agent response
- Timeouts: 3-second stdin timeout on hooks to prevent hanging

## Cross-Cutting Concerns

**Logging:** Not implemented (relies on Claude Code output capture)

**Validation:**
- Frontmatter parsing with schema validation (`bin/lib/frontmatter.cjs`)
- Git state validation before operations
- Phase existence and status checks

**Configuration:**
- Settings file: `.claude/settings.json` (hooks, statusline config)
- Planning config: `.planning/config.json` (project settings)
- Environment variables: `CLAUDE_CONFIG_DIR` for custom config directory

**Context Management:**
- Bridge file pattern: Statusline writes metrics to `/tmp/claude-ctx-{session_id}.json`
- Context monitor reads bridge file and injects warnings
- Thresholds: WARNING at 35% remaining, CRITICAL at 25% remaining

**Multi-Runtime Support:**
- Detects config directory across Claude, OpenCode, Gemini
- Hook event names adapt to runtime (PostToolUse vs AfterTool)

---

*Architecture analysis: 2026-03-13*
