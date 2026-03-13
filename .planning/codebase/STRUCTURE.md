# Codebase Structure

**Analysis Date:** 2026-03-13

## Directory Layout

```
ducky-printer-project/
├── .claude/                    # Claude Code configuration and GSD framework
│   ├── agents/                 # Agent prompt definitions
│   ├── commands/gsd/           # Command definitions
│   ├── get-shit-done/          # Core GSD framework
│   ├── hooks/                  # Lifecycle hooks
│   ├── gsd-file-manifest.json  # File integrity checksums
│   ├── package.json            # Node.js module type declaration
│   └── settings.json           # Hook and statusline configuration
├── .planning/                  # Project planning documents
│   └── codebase/               # Codebase analysis documents
└── .gitignore                  # Python-focused gitignore
```

## Directory Purposes

**.claude/**
- Purpose: Claude Code configuration and GSD framework installation
- Contains: Agents, commands, workflows, tools, templates, hooks
- Key files: `settings.json`, `gsd-file-manifest.json`

**.claude/agents/**
- Purpose: Specialized AI agent prompt definitions
- Contains: Markdown agent definitions
- Key files:
  - `gsd-codebase-mapper.md`: Analyzes codebase structure
  - `gsd-executor.md`: Executes implementation plans
  - `gsd-planner.md`: Creates phase implementation plans
  - `gsd-debugger.md`: Diagnoses and fixes issues
  - `gsd-verifier.md`: Validates completed work
  - `gsd-roadmapper.md`: Creates project roadmaps
  - `gsd-integration-checker.md`: Validates integrations
  - `gsd-nyquist-auditor.md`: Audits plan completeness
  - `gsd-phase-researcher.md`: Researches phase requirements
  - `gsd-project-researcher.md`: Researches project context
  - `gsd-research-synthesizer.md`: Synthesizes research findings
  - `gsd-plan-checker.md`: Validates implementation plans

**.claude/commands/**
- Purpose: User-facing command definitions
- Contains: Markdown command files organized by namespace
- Key files in `gsd/`:
  - `execute-phase.md`: Execute current phase
  - `plan-phase.md`: Create phase implementation plan
  - `new-milestone.md`: Create new milestone
  - `complete-milestone.md`: Complete current milestone
  - `map-codebase.md`: Analyze codebase structure
  - `verify-work.md`: Validate completed work
  - `debug.md`: Debug issues
  - `research-phase.md`: Research phase requirements
  - `quick.md`: Quick task execution
  - `health.md`: Check project health
  - `progress.md`: Show project progress
  - `help.md`: Show help information

**.claude/get-shit-done/**
- Purpose: Core GSD framework (version 1.22.4)
- Contains: Tools, workflows, templates, references
- Key files: `VERSION`

**.claude/get-shit-done/bin/**
- Purpose: Runtime tools and libraries
- Contains: Node.js modules for state management and operations
- Key files:
  - `gsd-tools.cjs`: Main tool entry point
  - `lib/state.cjs`: State file operations
  - `lib/phase.cjs`: Phase management
  - `lib/milestone.cjs`: Milestone management
  - `lib/roadmap.cjs`: Roadmap operations
  - `lib/frontmatter.cjs`: Frontmatter parsing
  - `lib/template.cjs`: Template rendering
  - `lib/verify.cjs`: Verification logic
  - `lib/commands.cjs`: Command utilities
  - `lib/config.cjs`: Configuration management
  - `lib/core.cjs`: Core utilities
  - `lib/init.cjs`: Project initialization

**.claude/get-shit-done/workflows/**
- Purpose: Orchestration logic for multi-step operations
- Contains: Workflow markdown files
- Key files:
  - `execute-phase.md`: Phase execution workflow
  - `plan-phase.md`: Phase planning workflow
  - `verify-work.md`: Work verification workflow
  - `complete-milestone.md`: Milestone completion workflow
  - `new-project.md`: Project initialization workflow
  - `map-codebase.md`: Codebase mapping workflow
  - `debug.md`: Debugging workflow (alias: `diagnose-issues.md`)
  - `research-phase.md`: Phase research workflow

**.claude/get-shit-done/templates/**
- Purpose: Document structure templates
- Contains: Markdown templates with placeholders
- Key files:
  - `project.md`: Project definition
  - `milestone.md`: Milestone structure
  - `roadmap.md`: Roadmap structure
  - `state.md`: State tracking
  - `phase-prompt.md`: Phase execution prompt
  - `context.md`: Context tracking
  - `requirements.md`: Requirements documentation
  - `research.md`: Research documentation
  - `verification-report.md`: Verification results
  - `DEBUG.md`: Debug report
  - `UAT.md`: User acceptance testing
  - `VALIDATION.md`: Validation report

**.claude/get-shit-done/templates/codebase/**
- Purpose: Codebase analysis document templates
- Contains: Templates for mapping codebase
- Key files:
  - `architecture.md`: Architecture patterns
  - `structure.md`: Directory structure
  - `stack.md`: Technology stack
  - `integrations.md`: External integrations
  - `conventions.md`: Coding conventions
  - `testing.md`: Testing patterns
  - `concerns.md`: Technical debt and issues

**.claude/get-shit-done/templates/research-project/**
- Purpose: Templates for research-focused projects
- Contains: Research project documentation templates
- Key files:
  - `SUMMARY.md`: Research summary
  - `ARCHITECTURE.md`: Architecture analysis
  - `STACK.md`: Technology stack
  - `FEATURES.md`: Feature analysis
  - `PITFALLS.md`: Common pitfalls

**.claude/get-shit-done/references/**
- Purpose: Reference documentation for GSD concepts
- Contains: Markdown documentation
- Key files:
  - `checkpoints.md`: Checkpoint system documentation
  - `continuation-format.md`: Continuation format spec
  - `git-integration.md`: Git integration patterns
  - `model-profiles.md`: Model profile system
  - `planning-config.md`: Planning configuration
  - `verification-patterns.md`: Verification approaches
  - `tdd.md`: Test-driven development patterns
  - `questioning.md`: Questioning patterns

**.claude/hooks/**
- Purpose: Claude Code lifecycle hooks
- Contains: Node.js hook scripts
- Key files:
  - `gsd-check-update.js`: Check for GSD updates (SessionStart)
  - `gsd-context-monitor.js`: Monitor context usage (PostToolUse)
  - `gsd-statusline.js`: Display status bar

**.planning/**
- Purpose: Project planning and tracking documents
- Contains: Project state, milestones, phases, context
- Key locations: Will be created by GSD commands

**.planning/codebase/**
- Purpose: Codebase analysis documents
- Contains: Architecture, structure, stack, conventions, etc.
- Generated by: `/gsd:map-codebase` command

## Key File Locations

**Configuration:**
- `.claude/settings.json`: Hook and statusline configuration
- `.claude/package.json`: Node.js module type (CommonJS)
- `.claude/gsd-file-manifest.json`: File integrity checksums

**Entry Points:**
- `.claude/hooks/gsd-check-update.js`: Update check on session start
- `.claude/hooks/gsd-context-monitor.js`: Context monitoring
- `.claude/hooks/gsd-statusline.js`: Status bar display
- `.claude/get-shit-done/bin/gsd-tools.cjs`: Tool CLI entry point

**State Files:**
- `.planning/STATE.md`: Current project state (created by GSD)
- `.planning/ROADMAP.md`: Project roadmap (created by GSD)
- `.planning/PROJECT.md`: Project definition (created by GSD)

**Version Control:**
- `.gitignore`: Python-focused gitignore (indicates Python project intent)

## Naming Conventions

**Files:**
- Commands: `kebab-case.md` (e.g., `execute-phase.md`)
- Agents: `gsd-kebab-case.md` (e.g., `gsd-executor.md`)
- Templates: `kebab-case.md` or `UPPERCASE.md` for generated docs
- Scripts: `gsd-kebab-case.js` (e.g., `gsd-statusline.js`)
- Tools: `kebab-case.cjs` (CommonJS modules)

**Directories:**
- Framework: `kebab-case` (e.g., `get-shit-done`)
- Planning: `lowercase` (e.g., `codebase`, `milestones`)

## Where to Add New Code

**New Command:**
- Command definition: `.claude/commands/gsd/command-name.md`
- Workflow: `.claude/get-shit-done/workflows/command-name.md`
- Tests: Not applicable (declarative system)

**New Agent:**
- Agent definition: `.claude/agents/gsd-agent-name.md`
- Include: Role definition, process steps, rules, templates

**New Template:**
- Planning template: `.claude/get-shit-done/templates/template-name.md`
- Codebase template: `.claude/get-shit-done/templates/codebase/TEMPLATE-NAME.md`

**New Tool Function:**
- Core logic: `.claude/get-shit-done/bin/lib/module-name.cjs`
- Export from: `.claude/get-shit-done/bin/gsd-tools.cjs`

**New Hook:**
- Hook script: `.claude/hooks/gsd-hook-name.js`
- Register in: `.claude/settings.json` (hooks section)

**Project Documentation:**
- Codebase analysis: `.planning/codebase/DOCUMENT-NAME.md`
- Milestone: `.planning/milestones/NN-milestone-name.md`
- Phase plans: `.planning/phases/M.N-phase-name/`
- Context: `.planning/CONTEXT.md`

## Special Directories

**.git/**
- Purpose: Git version control
- Generated: Yes
- Committed: No (internal git metadata)

**.planning/**
- Purpose: GSD project planning documents
- Generated: Yes (by GSD commands)
- Committed: Yes (core to GSD workflow)

**.claude/cache/**
- Purpose: Cache for update checks and temporary data
- Generated: Yes (by hooks)
- Committed: No (transient data)

**~/.claude/todos/**
- Purpose: Session-specific todo tracking
- Generated: Yes (by GSD commands)
- Committed: No (user-specific, outside project)
- Location: User home directory

**/tmp/claude-ctx-{session_id}.json**
- Purpose: Context metrics bridge between statusline and context monitor
- Generated: Yes (by statusline hook)
- Committed: No (temporary session data)
- Location: OS temp directory

## Import Patterns

**Not applicable:** This is a declarative framework. Node.js modules use CommonJS `require()`:
- `const fs = require('fs');`
- `const path = require('path');`
- `const { spawn } = require('child_process');`

JavaScript files are tools/hooks, not application code with complex import graphs.

## File Organization Principles

1. **Separation of Concerns:** Commands, workflows, agents, tools are separate layers
2. **Template-Driven:** Documents generated from templates with consistent structure
3. **Hook-Based Extension:** Runtime behavior extended via hooks, not code modification
4. **Git-Integrated:** State tracked in `.planning/`, committed with structured messages
5. **Multi-Runtime Support:** Config detection supports Claude, OpenCode, Gemini

---

*Structure analysis: 2026-03-13*
